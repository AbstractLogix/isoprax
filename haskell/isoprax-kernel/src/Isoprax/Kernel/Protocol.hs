{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Protocol (runJsonLines, handleLine) where

import Control.Monad (unless)
import Data.Aeson
  ( Object
  , Value (..)
  , object
  , toJSON
  , (.=)
  )
import qualified Data.Aeson.Key
import Data.Aeson.Parser (jsonNoDup)
import Data.Aeson.RFC8785 (encodeCanonical)
import Data.Attoparsec.ByteString (endOfInput, parseOnly)
import Data.Attoparsec.ByteString.Char8 (skipSpace)
import qualified Data.ByteString as ByteString
import qualified Data.ByteString.Char8 as ByteString8
import qualified Data.ByteString.Lazy as LazyByteString
import Data.Scientific (floatingOrInteger)
import Data.Text (Text)
import qualified Data.Text as Text
import Isoprax.Kernel.Admission
import Isoprax.Kernel.Calibration
import Isoprax.Kernel.Commensurability
import Isoprax.Kernel.Conformance
import Isoprax.Kernel.Decode
import Isoprax.Kernel.Identity
import Isoprax.Kernel.Types
import System.IO (hFlush, hIsEOF, stdin, stdout)

runJsonLines :: IO ()
runJsonLines = loop
  where
    loop = do
      eof <- hIsEOF stdin
      unless eof $ do
        line <- ByteString8.hGetLine stdin
        unless (ByteString.null line) $ do
          ByteString.hPut stdout (handleLine line)
          ByteString.hPut stdout (ByteString8.pack "\n")
          hFlush stdout
        loop

handleLine :: ByteString.ByteString -> ByteString.ByteString
handleLine line =
  let parsed = parseOnly (jsonNoDup <* skipSpace <* endOfInput) line
      result = case parsed of
        Left message -> Left (KernelError (parseErrorCategory message) "request is not valid unique-key JSON")
        Right request -> handleRequest request
  in LazyByteString.toStrict (encodeCanonical (either errorResponse id result))

parseErrorCategory :: String -> ErrorCategory
parseErrorCategory message
  | Text.isInfixOf "duplicate" (Text.toLower (Text.pack message)) = DuplicateKey
  | otherwise = InvalidJson

handleRequest :: Value -> Either KernelError Value
handleRequest raw = do
  request <- objectValue InvalidJson "request" raw
  version <- requiredField InvalidJson "version" request >>= scientificValue InvalidJson "version"
  if version /= 1
    then Left (KernelError UnsupportedVersion "supported protocol version is 1")
    else do
      operation <- requiredText InvalidJson "operation" request
      case operation of
        "identity" -> identityOperation request
        "commensurability" -> commensurabilityOperation request
        "calibration" -> calibrationOperation request
        "admission" -> admissionOperation request
        "conformance" -> conformanceOperation request
        _ -> Left (KernelError UnknownOperation "unknown operation")

identityOperation :: Object -> Either KernelError Value
identityOperation request = do
  rejectUnknownFields InvalidIdentityValue ["version", "operation", "value"] request
  value <- requiredField InvalidIdentityValue "value" request
  identity <- canonicalIdentity value
  pure $ response
    [ "canonical" .= identityCanonical identity
    , "sha256" .= identitySha256 identity
    ]

commensurabilityOperation :: Object -> Either KernelError Value
commensurabilityOperation request = do
  rejectUnknownFields InvalidOutcomeDefinition
    ["version", "operation", "left", "right", "attestation", "bridge"]
    request
  leftValue <- requiredField InvalidOutcomeDefinition "left" request
  rightValue <- requiredField InvalidOutcomeDefinition "right" request
  left <- parseOutcomeDefinition leftValue
  right <- parseOutcomeDefinition rightValue
  decision <- checkCommensurability
    left right
    (optionalField "attestation" request)
    (optionalField "bridge" request)
  pure $ response
    [ "level" .= levelText (decisionLevel decision)
    , "commensurable" .= decisionCommensurable decision
    , "pooling_allowed" .= decisionPoolingAllowed decision
    , "differing_fields" .= decisionDifferingFields decision
    , "reason_code" .= decisionReasonCode decision
    ]

calibrationOperation :: Object -> Either KernelError Value
calibrationOperation request = do
  rejectUnknownFields InvalidCalibrationInput
    ["version", "operation", "definition_id", "scores", "outcomes", "min_events", "n_bins", "max_ece"]
    request
  definitionId <- requiredText InvalidCalibrationInput "definition_id" request
    >>= nonEmptyText InvalidCalibrationInput "definition_id"
  scores <- requiredField InvalidCalibrationInput "scores" request >>= parseScores
  outcomes <- requiredField InvalidCalibrationInput "outcomes" request >>= parseOutcomes
  config <- parseCalibrationConfig request
  result <- evaluateCalibration definitionId config scores outcomes
  pure $ response ["calibration" .= calibrationJson result]

admissionOperation :: Object -> Either KernelError Value
admissionOperation request = do
  rejectUnknownFields InvalidAdmissionInput
    ["version", "operation", "rows", "fitted_row_ids", "gated_row_ids", "provenance", "predeclaration"]
    request
  rows <- optionalArray "rows" request >>= traverse parseAdmissionRow
  fitted <- optionalTextArray "fitted_row_ids" request
  gated <- optionalTextArray "gated_row_ids" request
  provenance <- traverse parseProvenance (optionalField "provenance" request)
  predeclaration <- traverse parsePredeclaration (optionalField "predeclaration" request)
  let decision = evaluateAdmission rows fitted gated provenance predeclaration
  pure $ response
    [ "calibration_evidence" .= gateJson (calibrationAdmission decision)
    , "provenance_predeclaration" .= gateJson (provenanceAdmission decision)
    ]

conformanceOperation :: Object -> Either KernelError Value
conformanceOperation request = do
  rejectUnknownFields InvalidOutcomeDefinition
    [ "version", "operation", "left", "right", "attestation", "bridge"
    , "left_scores", "left_outcomes", "right_scores", "right_outcomes"
    , "min_events", "n_bins", "max_ece"
    ] request
  left <- requiredField InvalidOutcomeDefinition "left" request >>= parseOutcomeDefinition
  right <- requiredField InvalidOutcomeDefinition "right" request >>= parseOutcomeDefinition
  leftScores <- requiredField InvalidCalibrationInput "left_scores" request >>= parseScores
  leftOutcomes <- requiredField InvalidCalibrationInput "left_outcomes" request >>= parseOutcomes
  rightScores <- requiredField InvalidCalibrationInput "right_scores" request >>= parseScores
  rightOutcomes <- requiredField InvalidCalibrationInput "right_outcomes" request >>= parseOutcomes
  config <- parseCalibrationConfig request
  commensurability <- checkCommensurability
    left right (optionalField "attestation" request) (optionalField "bridge" request)
  leftCalibration <- evaluateCalibration (outcomeId left) config leftScores leftOutcomes
  rightCalibration <- evaluateCalibration (outcomeId right) config rightScores rightOutcomes
  let projection = projectStage0
        (calibrationBins config) commensurability
        leftCalibration rightCalibration
        leftScores leftOutcomes rightScores rightOutcomes
  pure $ response
    [ "commensurability" .= commensurabilityJson commensurability
    , "left_calibration" .= calibrationJson leftCalibration
    , "right_calibration" .= calibrationJson rightCalibration
    , "pooled_ece" .= maybe Null toJSON (conformancePooledEce projection)
    , "declarable_class" .= conformanceDeclarableClass projection
    ]

parseCalibrationConfig :: Object -> Either KernelError CalibrationConfig
parseCalibrationConfig request = do
  minEvents <- optionalInt "min_events" request (calibrationMinEvents defaultCalibrationConfig)
  bins <- optionalInt "n_bins" request (calibrationBins defaultCalibrationConfig)
  maxEce <- case field "max_ece" request of
    Nothing -> Right (calibrationMaxEce defaultCalibrationConfig)
    Just value -> doubleValue InvalidCalibrationInput "max_ece" value
  pure (CalibrationConfig minEvents bins maxEce)

parseScores :: Value -> Either KernelError [Double]
parseScores value =
  arrayValue InvalidCalibrationInput "scores" value
    >>= traverse (doubleValue InvalidCalibrationInput "score")

parseOutcomes :: Value -> Either KernelError [Int]
parseOutcomes value = do
  values <- arrayValue InvalidCalibrationInput "outcomes" value
  traverse parseOutcome values
  where
    parseOutcome (Number number) =
      case floatingOrInteger number :: Either Double Integer of
        Right 0 -> Right 0
        Right 1 -> Right 1
        _ -> Left (KernelError InvalidCalibrationInput "outcomes must be binary 0 or 1")
    parseOutcome _ = Left (KernelError InvalidCalibrationInput "outcomes must be binary 0 or 1")

optionalInt :: Text -> Object -> Int -> Either KernelError Int
optionalInt name request fallback =
  case field name request of
    Nothing -> Right fallback
    Just (Number number) ->
      case floatingOrInteger number :: Either Double Integer of
        Right value | value >= 0 && value <= fromIntegral (maxBound :: Int) -> Right (fromIntegral value)
        _ -> Left (KernelError InvalidCalibrationInput (name <> " must be a non-negative integer"))
    Just _ -> Left (KernelError InvalidCalibrationInput (name <> " must be a non-negative integer"))

optionalTextArray :: Text -> Object -> Either KernelError [Text]
optionalTextArray name request =
  case field name request of
    Nothing -> Right []
    Just value -> arrayValue InvalidAdmissionInput name value
      >>= traverse (textValue InvalidAdmissionInput name)

optionalArray :: Text -> Object -> Either KernelError [Value]
optionalArray name request =
  case field name request of
    Nothing -> Right []
    Just value -> arrayValue InvalidAdmissionInput name value

parseAdmissionRow :: Value -> Either KernelError AdmissionRow
parseAdmissionRow value = do
  rowObject <- objectValue InvalidAdmissionInput "row" value
  rejectUnknownFields InvalidAdmissionInput ["row_id", "split"] rowObject
  rowId <- requiredText InvalidAdmissionInput "row_id" rowObject
  split <- requiredText InvalidAdmissionInput "split" rowObject
  pure (AdmissionRow rowId split)

parseProvenance :: Value -> Either KernelError ProvenanceInput
parseProvenance value = do
  provenanceObject <- objectValue InvalidAdmissionInput "provenance" value
  rejectUnknownFields InvalidAdmissionInput
    ["source_system", "uses_private_production_data", "uses_privileged_telemetry"]
    provenanceObject
  source <- requiredText InvalidAdmissionInput "source_system" provenanceObject
  privateData <- requiredField InvalidAdmissionInput "uses_private_production_data" provenanceObject
    >>= boolValue InvalidAdmissionInput "uses_private_production_data"
  privileged <- requiredField InvalidAdmissionInput "uses_privileged_telemetry" provenanceObject
    >>= boolValue InvalidAdmissionInput "uses_privileged_telemetry"
  pure (ProvenanceInput source privateData privileged)

parsePredeclaration :: Value -> Either KernelError PredeclarationInput
parsePredeclaration value = do
  declarationObject <- objectValue InvalidAdmissionInput "predeclaration" value
  rejectUnknownFields InvalidAdmissionInput
    ["artifact_hash", "external_anchor_reference", "predeclared_at", "corpus_collection_started_at"]
    declarationObject
  hash <- requiredText InvalidAdmissionInput "artifact_hash" declarationObject
  anchor <- requiredText InvalidAdmissionInput "external_anchor_reference" declarationObject
  declared <- requiredText InvalidAdmissionInput "predeclared_at" declarationObject
  started <- requiredText InvalidAdmissionInput "corpus_collection_started_at" declarationObject
  pure (PredeclarationInput hash anchor declared started)

optionalField :: Text -> Object -> Maybe Value
optionalField name request = case field name request of
  Nothing -> Nothing
  Just Null -> Nothing
  Just value -> Just value

calibrationJson :: CalibrationDecision -> Value
calibrationJson result = object
  [ "calibrated" .= calibrationPassed result
  , "ece" .= calibrationEce result
  , "sample_count" .= calibrationCount result
  , "reason_code" .= calibrationReasonCode result
  ]

commensurabilityJson :: CommensurabilityDecision -> Value
commensurabilityJson result = object
  [ "level" .= levelText (decisionLevel result)
  , "commensurable" .= decisionCommensurable result
  , "pooling_allowed" .= decisionPoolingAllowed result
  , "differing_fields" .= decisionDifferingFields result
  , "reason_code" .= decisionReasonCode result
  ]

gateJson :: AdmissionGate -> Value
gateJson result = object
  [ "passed" .= admissionGatePassed result
  , "reason_code" .= admissionGateReason result
  ]

response :: [(Data.Aeson.Key.Key, Value)] -> Value
response fields = object (("version" .= (1 :: Int)) : fields)

errorResponse :: KernelError -> Value
errorResponse failure = object
  [ "version" .= (1 :: Int)
  , "error" .= object
      [ "category" .= errorCategoryText (errorCategory failure)
      , "detail" .= errorDetail failure
      ]
  ]

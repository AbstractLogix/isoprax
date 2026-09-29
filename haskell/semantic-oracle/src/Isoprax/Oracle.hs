{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Oracle
  ( Definition
  , CalibrationPolicy
  , CommensurabilityEvidence
  , CalibrationEvidence
  , PoolingAuthorization
  , parseDefinition
  , parseCalibrationPolicy
  , establishCommensurability
  , establishCalibration
  , authorizePooledComparison
  , authorizedPooledEce
  , runFixture
  ) where

import Control.Monad (unless, when)
import Crypto.Hash.SHA256 qualified as SHA256
import Data.Aeson (FromJSON, Result (..), ToJSON, Value (..), fromJSON, object, toJSON, (.=))
import Data.Aeson.Key qualified as Key
import Data.Aeson.KeyMap qualified as KeyMap
import Data.Aeson.RFC8785 (encodeCanonical)
import Data.ByteString qualified as ByteString
import Data.ByteString.Lazy qualified as LazyByteString
import Data.List (sortOn)
import Data.Scientific (Scientific, base10Exponent, coefficient, fromFloatDigits, toRealFloat)
import Data.Text (Text)
import Data.Text qualified as Text
import Data.Vector qualified as Vector
import Data.Word (Word8)

data Definition = Definition
  { definitionId :: Text
  , definitionKey :: Value
  , definitionContentDigest :: Text
  }
  deriving (Eq, Show)

data CalibrationPolicy = CalibrationPolicy
  { policyMinEvents :: Int
  , policyBins :: Int
  , policyMaxEce :: Double
  }
  deriving (Eq, Show)

data CommensurabilityEvidence = CommensurabilityEvidence
  { commensurabilityLeftId :: Text
  , commensurabilityRightId :: Text
  , commensurabilityLeftDigest :: Text
  , commensurabilityRightDigest :: Text
  }
  deriving (Eq, Show)

data CalibrationEvidence = CalibrationEvidence
  { calibrationDefinitionId :: Text
  , calibrationDefinitionDigest :: Text
  , calibrationSampleHash :: Text
  , calibrationPolicy :: CalibrationPolicy
  }
  deriving (Eq, Show)

data PoolingAuthorization = PoolingAuthorization
  { authorizationLeftSampleHash :: Text
  , authorizationRightSampleHash :: Text
  , authorizationPolicy :: CalibrationPolicy
  }
  deriving (Eq, Show)

parseDefinition :: Value -> Either Text Definition
parseDefinition value = do
  members <- asObject "outcome definition" value
  rejectUnknown "outcome definition" ["id", "event", "observation_process", "window", "thresholds", "description"] members
  identifier <- requiredText "id" members
  event <- requiredText "event" members
  unless (not (Text.null (Text.strip identifier))) (Left "definition id must not be empty")
  unless (not (Text.null (Text.strip event))) (Left "definition event must not be empty")
  processValue <- requiredField "observation_process" members
  (processKind, processParameters, processRaw) <- parseProcess processValue
  windowValue <- requiredField "window" members
  windowKey <- parseWindow windowValue
  thresholdValues <- case KeyMap.lookup "thresholds" members of
    Nothing -> Right []
    Just (String raw) -> if Text.null (Text.strip raw) then Right [] else (: []) <$> parseThreshold (String raw)
    Just (Array values) -> traverse parseThreshold (Vector.toList values)
    Just _ -> Left "thresholds must be a string or array"
  let sortedThresholds = sortOn show thresholdValues
      processKey = arrayValue [String processKind, toJSONValue processParameters, String processRaw]
      key = arrayValue [
          String (normalized event)
        , processKey
        , windowKey
        , toJSONValue sortedThresholds
        ]
      digestInput = object
        [ "kind" .= ("isoprax.outcome-definition-content" :: Text)
        , "version" .= (1 :: Int)
        , "comparison_key" .= key
        ]
  digest <- canonicalHash digestInput
  pure (Definition identifier key digest)

parseCalibrationPolicy :: Value -> Either Text CalibrationPolicy
parseCalibrationPolicy value = do
  members <- asObject "calibration policy" value
  rejectUnknown "calibration policy" ["min_events", "n_bins", "max_ece"] members
  minEvents <- requiredInt "min_events" members
  bins <- requiredInt "n_bins" members
  maxEce <- requiredDouble "max_ece" members
  when (minEvents < 0) (Left "min_events must not be negative")
  when (bins < 1) (Left "n_bins must be positive")
  when (not (finite maxEce) || maxEce < 0 || maxEce > 1) (Left "max_ece must be finite and in [0, 1]")
  pure (CalibrationPolicy minEvents bins maxEce)

establishCommensurability :: Definition -> Definition -> Either Text CommensurabilityEvidence
establishCommensurability left right
  | definitionKey left == definitionKey right =
      Right (CommensurabilityEvidence (definitionId left) (definitionId right) (definitionContentDigest left) (definitionContentDigest right))
  | otherwise = Left "outcome definitions are not directly commensurable"

establishCalibration
  :: Definition
  -> CalibrationPolicy
  -> [Double]
  -> [Int]
  -> Either Text CalibrationEvidence
establishCalibration definition policy scores outcomes = do
  validateSample scores outcomes
  sampleHash <- sampleDigest scores outcomes
  let passes = calibrationPasses policy scores outcomes
  unless passes (Left "calibration does not satisfy its policy")
  pure (CalibrationEvidence (definitionId definition) (definitionContentDigest definition) sampleHash policy)

authorizePooledComparison
  :: CommensurabilityEvidence
  -> CalibrationEvidence
  -> CalibrationEvidence
  -> Either Text PoolingAuthorization
authorizePooledComparison commensurability left right = do
  unless
    ( calibrationDefinitionId left == commensurabilityLeftId commensurability
      && calibrationDefinitionDigest left == commensurabilityLeftDigest commensurability
    )
    (Left "left calibration targets a different definition")
  unless
    ( calibrationDefinitionId right == commensurabilityRightId commensurability
      && calibrationDefinitionDigest right == commensurabilityRightDigest commensurability
    )
    (Left "right calibration targets a different definition")
  unless (calibrationPolicy left == calibrationPolicy right) (Left "calibration policies differ")
  pure (PoolingAuthorization (calibrationSampleHash left) (calibrationSampleHash right) (calibrationPolicy left))

authorizedPooledEce
  :: PoolingAuthorization
  -> [Double]
  -> [Int]
  -> [Double]
  -> [Int]
  -> Either Text Double
authorizedPooledEce authorization leftScores leftOutcomes rightScores rightOutcomes = do
  validateSample leftScores leftOutcomes
  validateSample rightScores rightOutcomes
  leftDigest <- sampleDigest leftScores leftOutcomes
  rightDigest <- sampleDigest rightScores rightOutcomes
  unless (leftDigest == authorizationLeftSampleHash authorization) (Left "left sample differs from calibration evidence")
  unless (rightDigest == authorizationRightSampleHash authorization) (Left "right sample differs from calibration evidence")
  pure (expectedCalibrationError (policyBins (authorizationPolicy authorization)) (leftScores ++ rightScores) (leftOutcomes ++ rightOutcomes))

runFixture :: Value -> Either Text Value
runFixture (Array fixtures) =
  arrayValue <$> traverse runFixture (Vector.toList fixtures)
runFixture fixture = do
  members <- asObject "fixture" fixture
  left <- requiredField "left" members >>= parseDefinition
  right <- requiredField "right" members >>= parseDefinition
  leftCalibration <- requiredField "left_calibration" members >>= parseCalibrationInput
  rightCalibration <- requiredField "right_calibration" members >>= parseCalibrationInput
  pooled <- requiredField "pooled" members >>= asObject "pooled samples"
  leftPoolScores <- requiredArray "left_scores" pooled >>= traverse valueDouble
  leftPoolOutcomes <- requiredArray "left_outcomes" pooled >>= traverse valueInt
  rightPoolScores <- requiredArray "right_scores" pooled >>= traverse valueDouble
  rightPoolOutcomes <- requiredArray "right_outcomes" pooled >>= traverse valueInt
  commensurability <- pure (establishCommensurability left right)
  let leftPasses = calibrationPasses (inputPolicy leftCalibration) (inputScores leftCalibration) (inputOutcomes leftCalibration)
      rightPasses = calibrationPasses (inputPolicy rightCalibration) (inputScores rightCalibration) (inputOutcomes rightCalibration)
      authorization = do
        commEvidence <- commensurability
        leftEvidence <- establishCalibration (inputDefinition leftCalibration) (inputPolicy leftCalibration) (inputScores leftCalibration) (inputOutcomes leftCalibration)
        rightEvidence <- establishCalibration (inputDefinition rightCalibration) (inputPolicy rightCalibration) (inputScores rightCalibration) (inputOutcomes rightCalibration)
        authorizePooledComparison commEvidence leftEvidence rightEvidence
      pooledResult = do
        authorized <- authorization
        authorizedPooledEce authorized leftPoolScores leftPoolOutcomes rightPoolScores rightPoolOutcomes
  leftSampleHash <- sampleDigest (inputScores leftCalibration) (inputOutcomes leftCalibration)
  rightSampleHash <- sampleDigest (inputScores rightCalibration) (inputOutcomes rightCalibration)
  leftPolicyHash <- policyDigest (inputPolicy leftCalibration)
  rightPolicyHash <- policyDigest (inputPolicy rightCalibration)
  pure $ object
    [ "commensurable" .= either (const False) (const True) commensurability
    , "definition_digests" .= object
        [ "left" .= definitionContentDigest left
        , "right" .= definitionContentDigest right
        , "left_calibration" .= definitionContentDigest (inputDefinition leftCalibration)
        , "right_calibration" .= definitionContentDigest (inputDefinition rightCalibration)
        ]
    , "calibration_passes" .= object ["left" .= leftPasses, "right" .= rightPasses]
    , "sample_digests" .= object ["left" .= leftSampleHash, "right" .= rightSampleHash]
    , "policy_digests" .= object ["left" .= leftPolicyHash, "right" .= rightPolicyHash]
    , "authorized" .= either (const False) (const True) authorization
    , "pooled_ece" .= either (const Nothing) Just pooledResult
    ]

data CalibrationInput = CalibrationInput
  { inputDefinition :: Definition
  , inputPolicy :: CalibrationPolicy
  , inputScores :: [Double]
  , inputOutcomes :: [Int]
  }

parseCalibrationInput :: Value -> Either Text CalibrationInput
parseCalibrationInput value = do
  members <- asObject "calibration input" value
  definition <- requiredField "definition" members >>= parseDefinition
  policy <- requiredField "policy" members >>= parseCalibrationPolicy
  scores <- requiredArray "scores" members >>= traverse valueDouble
  outcomes <- requiredArray "outcomes" members >>= traverse valueInt
  validateSample scores outcomes
  pure (CalibrationInput definition policy scores outcomes)

parseProcess :: Value -> Either Text (Text, [(Text, Text)], Text)
parseProcess (String raw) =
  let text = Text.strip raw
  in if Text.null text then Left "observation process must not be empty" else Right (Text.toLower text, [], text)
parseProcess value = do
  members <- asObject "observation_process" value
  rejectUnknown "observation_process" ["kind", "parameters", "raw"] members
  kind <- requiredText "kind" members
  raw <- optionalText "raw" members
  parameters <- case KeyMap.lookup "parameters" members of
    Nothing -> Right []
    Just (Object objectValues) -> traverse parseParameter (KeyMap.toList objectValues)
    Just (Array values) -> traverse parsePair (Vector.toList values)
    Just _ -> Left "observation process parameters must be an object or pair array"
  let sorted = sortOn fst parameters
  when (Text.null (Text.strip kind)) (Left "observation process kind must not be empty")
  when (hasDuplicateKeys sorted) (Left "observation process parameter keys must be unique")
  pure (normalized kind, sorted, normalized raw)
  where
    parseParameter (key, String parameterValue) = Right (Key.toText key, parameterValue)
    parseParameter _ = Left "observation process parameter values must be strings"
    parsePair (Array pair) = case Vector.toList pair of
      [String key, String parameterValue] -> Right (key, parameterValue)
      _ -> Left "observation process parameter pairs must contain two strings"
    parsePair _ = Left "observation process parameters must be pairs"

parseWindow :: Value -> Either Text Value
parseWindow (String raw) =
  let text = Text.strip raw
  in if Text.null text
       then Left "window description must not be empty"
       else Right (arrayValue [Null, String "", String (normalized text)])
parseWindow value = do
  members <- asObject "window" value
  rejectUnknown "window" ["duration", "unit", "anchor", "raw"] members
  duration <- optionalNumber "duration" members
  unit <- optionalText "unit" members
  anchor <- optionalText "anchor" members
  when (maybe False (< 0) duration) (Left "window duration must not be negative")
  when (Text.null (Text.strip anchor)) (Left "window anchor must not be empty")
  when (maybe False (const (Text.null (Text.strip unit))) duration) (Left "window unit is required with a duration")
  pure (arrayValue [maybe Null (Number . fromFloat) duration, String (normalized unit), String (normalized anchor)])

parseThreshold :: Value -> Either Text Value
parseThreshold (String raw) =
  let text = Text.strip raw
  in if Text.null text then Left "threshold must not be empty" else Right (arrayValue [String (normalized text), String "", Null, Null, String ""])
parseThreshold value = do
  members <- asObject "threshold" value
  rejectUnknown "threshold" ["metric", "operator", "value", "sustain", "sustain_unit", "raw"] members
  metric <- requiredText "metric" members
  operator <- optionalText "operator" members
  thresholdValue <- case KeyMap.lookup "value" members of
    Nothing -> Right Null
    Just Null -> Right Null
    Just (String text) -> Right (String text)
    Just (Number number) -> do
      _ <- scientificDouble number
      Right (Number number)
    Just _ -> Left "threshold value must be a string, number, or null"
  sustain <- optionalNumber "sustain" members
  sustainUnit <- optionalText "sustain_unit" members
  when (Text.null (Text.strip metric)) (Left "threshold metric must not be empty")
  when (maybe False (< 0) sustain) (Left "threshold sustain must not be negative")
  pure (arrayValue
    [ String (normalized metric)
    , String (Text.strip operator)
    , thresholdValue
    , maybe Null (Number . fromFloat) sustain
    , String (normalized sustainUnit)
    ])

calibrationPasses :: CalibrationPolicy -> [Double] -> [Int] -> Bool
calibrationPasses policy scores outcomes =
  length scores >= policyMinEvents policy
    && not (null (filter (== 0) outcomes) || null (filter (== 1) outcomes))
    && expectedCalibrationError (policyBins policy) scores outcomes <= policyMaxEce policy
    && scoreVariance scores > 0

validateSample :: [Double] -> [Int] -> Either Text ()
validateSample scores outcomes = do
  unless (length scores == length outcomes) (Left "scores and outcomes must have equal length")
  unless (all (\score -> finite score && score >= 0 && score <= 1) scores) (Left "scores must be finite and in [0, 1]")
  unless (all (\outcome -> outcome == 0 || outcome == 1) outcomes) (Left "outcomes must be binary")

expectedCalibrationError :: Int -> [Double] -> [Int] -> Double
expectedCalibrationError _ [] _ = 0
expectedCalibrationError bins scores outcomes =
  let pairs = zip scores outcomes
      edge index
        | index == bins = 1
        | otherwise = fromIntegral index * (1 / fromIntegral bins)
      binError index =
        let lower = edge index
            upper = edge (index + 1)
            inBin (score, _) = score >= lower && (if index == bins - 1 then score <= upper else score < upper)
            assigned = filter inBin pairs
            count = length assigned
        in if count == 0
             then 0
             else fromIntegral count * abs
               ( sum (map fst assigned) / fromIntegral count
                 - fromIntegral (sum (map snd assigned)) / fromIntegral count
               )
  in sum (map binError [0 .. bins - 1]) / fromIntegral (length scores)

scoreVariance :: [Double] -> Double
scoreVariance [] = 0
scoreVariance scores =
  let mean = sum scores / fromIntegral (length scores)
  in sum (map (\score -> (score - mean) ^ (2 :: Int)) scores) / fromIntegral (length scores)

sampleDigest :: [Double] -> [Int] -> Either Text Text
sampleDigest scores outcomes = do
  validateSample scores outcomes
  canonicalHash (object ["scores" .= scores, "outcomes" .= outcomes])

policyDigest :: CalibrationPolicy -> Either Text Text
policyDigest policy = canonicalHash (object
  [ "kind" .= ("isoprax.calibration-policy" :: Text)
  , "version" .= (1 :: Int)
  , "min_events" .= policyMinEvents policy
  , "n_bins" .= policyBins policy
  , "max_ece" .= policyMaxEce policy
  ])

canonicalHash :: Value -> Either Text Text
canonicalHash value = do
  validateCanonicalValue value
  let bytes = LazyByteString.toStrict (encodeCanonical value)
      digest = SHA256.hash bytes
  pure (Text.pack (concatMap byteHex (ByteString.unpack digest)))

validateCanonicalValue :: Value -> Either Text ()
validateCanonicalValue value = case value of
  Object members -> traverse_ validateCanonicalValue (map snd (KeyMap.toList members))
  Array values -> traverse_ validateCanonicalValue (Vector.toList values)
  Number number -> do
    let asDouble = toRealFloat number :: Double
    when (not (finite asDouble)) (Left "number is outside the finite IEEE-754 domain")
    when (base10Exponent number == 0 && abs (coefficient number) > 9007199254740991) (Left "integer is outside the safe-integer range")
  _ -> Right ()

asObject :: Text -> Value -> Either Text (KeyMap.KeyMap Value)
asObject _ (Object members) = Right members
asObject label _ = Left (label <> " must be an object")

requiredField :: Text -> KeyMap.KeyMap Value -> Either Text Value
requiredField name members = maybe (Left ("missing field: " <> name)) Right (KeyMap.lookup (Key.fromText name) members)

requiredText :: Text -> KeyMap.KeyMap Value -> Either Text Text
requiredText name members = requiredField name members >>= valueText name

optionalText :: Text -> KeyMap.KeyMap Value -> Either Text Text
optionalText name members = case KeyMap.lookup (Key.fromText name) members of
  Nothing -> Right ""
  Just Null -> Right ""
  Just value -> valueText name value

valueText :: Text -> Value -> Either Text Text
valueText _ (String text) = Right text
valueText label _ = Left (label <> " must be a string")

requiredInt :: Text -> KeyMap.KeyMap Value -> Either Text Int
requiredInt name members = requiredField name members >>= valueInt

valueInt :: Value -> Either Text Int
valueInt (Number value)
  | base10Exponent value /= 0 = Left "expected an integer"
  | otherwise = case fromJSONValue (Number value) :: Maybe Int of
      Just result -> Right result
      Nothing -> Left "expected an integer"
valueInt _ = Left "expected an integer"

requiredDouble :: Text -> KeyMap.KeyMap Value -> Either Text Double
requiredDouble name members = requiredField name members >>= valueDouble

valueDouble :: Value -> Either Text Double
valueDouble (Number value) = scientificDouble value
valueDouble _ = Left "expected a number"

optionalNumber :: Text -> KeyMap.KeyMap Value -> Either Text (Maybe Double)
optionalNumber name members = case KeyMap.lookup (Key.fromText name) members of
  Nothing -> Right Nothing
  Just Null -> Right Nothing
  Just value -> Just <$> valueDouble value

requiredArray :: Text -> KeyMap.KeyMap Value -> Either Text [Value]
requiredArray name members = do
  value <- requiredField name members
  case value of
    Array values -> Right (Vector.toList values)
    _ -> Left (name <> " must be an array")

rejectUnknown :: Text -> [Text] -> KeyMap.KeyMap Value -> Either Text ()
rejectUnknown label allowed members =
  case filter (`notElem` allowed) (map Key.toText (KeyMap.keys members)) of
    [] -> Right ()
    name : _ -> Left ("unknown " <> label <> " field: " <> name)

hasDuplicateKeys :: [(Text, Text)] -> Bool
hasDuplicateKeys pairs = any ((> 1) . length) (groupKeys (map fst pairs))
  where
    groupKeys [] = []
    groupKeys (key : rest) =
      let (same, remaining) = span (== key) rest
      in (key : same) : groupKeys remaining

normalized :: Text -> Text
normalized = Text.toLower . Text.strip

arrayValue :: [Value] -> Value
arrayValue = Array . Vector.fromList

toJSONValue :: ToJSON a => a -> Value
toJSONValue = toJSON

fromJSONValue :: FromJSON a => Value -> Maybe a
fromJSONValue value = case fromJSON value of
  Success result -> Just result
  Error _ -> Nothing

scientificDouble :: Scientific -> Either Text Double
scientificDouble value =
  let number = toRealFloat value :: Double
  in if finite number then Right number else Left "number must be finite"

fromFloat :: Double -> Scientific
fromFloat = fromFloatDigits

finite :: Double -> Bool
finite number = not (isNaN number || isInfinite number)

traverse_ :: (a -> Either e b) -> [a] -> Either e ()
traverse_ _ [] = Right ()
traverse_ action (value : rest) = action value >> traverse_ action rest

byteHex :: Word8 -> String
byteHex byte =
  let digits = "0123456789abcdef"
      value = fromIntegral byte :: Int
  in [digits !! (quot value 16), digits !! (rem value 16)]

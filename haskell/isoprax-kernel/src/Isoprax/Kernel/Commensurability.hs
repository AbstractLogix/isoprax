{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Commensurability
  ( parseOutcomeDefinition
  , parseAttestationEvidence
  , parseBridgeEvidence
  , checkCommensurability
  , checkCommensurabilityWithEvidence
  , levelText
  ) where

import Data.Aeson (Value (..))
import qualified Data.Aeson.Key as Key
import qualified Data.Aeson.KeyMap as KeyMap
import Data.List (sort)
import Data.Scientific (normalize)
import Data.Text (Text)
import qualified Data.Text as Text
import Isoprax.Kernel.Decode
import Isoprax.Kernel.Types

parseOutcomeDefinition :: Value -> Either KernelError OutcomeDefinition
parseOutcomeDefinition value = do
  object <- objectValue InvalidOutcomeDefinition "outcome definition" value
  rejectUnknownFields InvalidOutcomeDefinition
    ["id", "event", "observation_process", "window", "thresholds", "description"]
    object
  definitionId <- requiredText InvalidOutcomeDefinition "id" object >>= nonEmptyText InvalidOutcomeDefinition "id"
  event <- requiredText InvalidOutcomeDefinition "event" object
    >>= nonEmptyText InvalidOutcomeDefinition "event"
  _ <- optionalText InvalidOutcomeDefinition "description" object
  processValue <- requiredField InvalidOutcomeDefinition "observation_process" object
  process <- parseProcess processValue
  windowValue <- requiredField InvalidOutcomeDefinition "window" object
  window <- parseWindow windowValue
  thresholds <- case field "thresholds" object of
    Nothing -> Right []
    Just raw -> arrayValue InvalidOutcomeDefinition "thresholds" raw
      >>= traverse parseThreshold
  pure OutcomeDefinition
    { outcomeId = definitionId
    , outcomeEvent = Text.toLower (Text.strip event)
    , outcomeProcess = process
    , outcomeWindow = window
    , outcomeThresholds = sort thresholds
    }

parseProcess :: Value -> Either KernelError (Text, [(Text, Text)], Text)
parseProcess value = do
  object <- objectValue InvalidOutcomeDefinition "observation_process" value
  rejectUnknownFields InvalidOutcomeDefinition ["kind", "parameters", "raw"] object
  kind <- requiredText InvalidOutcomeDefinition "kind" object
    >>= nonEmptyText InvalidOutcomeDefinition "kind"
  raw <- optionalText InvalidOutcomeDefinition "raw" object
  parameters <- case field "parameters" object of
    Nothing -> Right []
    Just (Object parameterObject) ->
      traverse parseParameter (KeyMap.toList parameterObject) >>= pure . sort
    Just _ -> Left (KernelError InvalidOutcomeDefinition "observation_process.parameters must be an object")
  pure (Text.toLower (Text.strip kind), parameters, Text.toLower (Text.strip raw))
  where
    parseParameter (key, String parameterValue) = Right (Key.toText key, parameterValue)
    parseParameter _ = Left (KernelError InvalidOutcomeDefinition "observation process parameter values must be strings")

parseWindow :: Value -> Either KernelError (Maybe Double, Text, Text)
parseWindow value = do
  object <- objectValue InvalidOutcomeDefinition "window" value
  rejectUnknownFields InvalidOutcomeDefinition ["duration", "unit", "anchor", "raw"] object
  duration <- optionalNumber InvalidOutcomeDefinition "duration" object
  case duration of
    Just number | number < 0 ->
      Left (KernelError InvalidOutcomeDefinition "window.duration must be non-negative")
    _ -> pure ()
  unit <- requiredText InvalidOutcomeDefinition "unit" object
    >>= nonEmptyText InvalidOutcomeDefinition "unit"
  anchor <- requiredText InvalidOutcomeDefinition "anchor" object
    >>= nonEmptyText InvalidOutcomeDefinition "anchor"
  _ <- optionalText InvalidOutcomeDefinition "raw" object
  pure
    ( duration
    , Text.toLower (Text.strip unit)
    , Text.toLower (Text.strip anchor)
    )

parseThreshold :: Value -> Either KernelError (Text, Text, Maybe Scalar, Maybe Double, Text)
parseThreshold value = do
  object <- objectValue InvalidOutcomeDefinition "threshold" value
  rejectUnknownFields InvalidOutcomeDefinition
    ["metric", "operator", "value", "sustain", "sustain_unit", "raw"]
    object
  metric <- requiredText InvalidOutcomeDefinition "metric" object
    >>= nonEmptyText InvalidOutcomeDefinition "metric"
  operator <- requiredText InvalidOutcomeDefinition "operator" object
    >>= nonEmptyText InvalidOutcomeDefinition "operator"
    >>= pure . Text.strip
  scalar <- case field "value" object of
    Nothing -> Right Nothing
    Just Null -> Right Nothing
    Just (String text) -> Right (Just (ScalarText text))
    Just (Number number) -> Right (Just (ScalarNumber (normalize number)))
    Just _ -> Left (KernelError InvalidOutcomeDefinition "threshold.value must be a string, number, or null")
  sustain <- optionalNumber InvalidOutcomeDefinition "sustain" object
  case sustain of
    Just number | number < 0 ->
      Left (KernelError InvalidOutcomeDefinition "threshold.sustain must be non-negative")
    _ -> pure ()
  sustainUnit <- optionalText InvalidOutcomeDefinition "sustain_unit" object
  _ <- optionalText InvalidOutcomeDefinition "raw" object
  pure
    ( Text.toLower (Text.strip metric)
    , operator
    , scalar
    , sustain
    , Text.toLower (Text.strip sustainUnit)
    )

checkCommensurability
  :: OutcomeDefinition
  -> OutcomeDefinition
  -> Maybe Value
  -> Maybe Value
  -> Either KernelError CommensurabilityDecision
checkCommensurability left right attestationValue bridgeValue
  | null differing = checkCommensurabilityWithEvidence left right Nothing Nothing
  | otherwise = do
      attestation <- traverse (parseAttestationEvidence left right) attestationValue
      let bridgeableFields = onlyBridgeableFields differing
      case attestation of
        Just evidence | bridgeableFields ->
          checkCommensurabilityWithEvidence left right (Just evidence) Nothing
        _ | bridgeableFields -> case bridgeValue of
          Nothing -> checkCommensurabilityWithEvidence left right Nothing Nothing
          Just rawBridge -> do
            bridge <- parseBridgeEvidence left right rawBridge
            checkCommensurabilityWithEvidence left right Nothing (Just bridge)
        _ -> checkCommensurabilityWithEvidence left right attestation Nothing
  where
    differing = differingFields left right

checkCommensurabilityWithEvidence
  :: OutcomeDefinition
  -> OutcomeDefinition
  -> Maybe AttestationEvidence
  -> Maybe BridgeEvidence
  -> Either KernelError CommensurabilityDecision
checkCommensurabilityWithEvidence left right attestation bridge
  | null differing =
      Right (CommensurabilityDecision Direct True True [] "same_structured_definition" proof)
  | otherwise = do
      validateMaybe (validateAttestationPair left right) attestation
      validateMaybe (validateBridgePair left right) bridge
      let bridgeableFields = onlyBridgeableFields differing
      case attestation of
        Just _ | bridgeableFields ->
          Right (CommensurabilityDecision Attested True True differing "attested_equivalent_definitions" proof)
        _ | bridgeableFields -> case bridge of
          Nothing -> Right (CommensurabilityDecision Bridgeable False False differing "bridge_evidence_missing" Nothing)
          Just _ -> Right (CommensurabilityDecision Bridgeable False True differing "bridgeable_with_explicit_evidence" proof)
        _ -> Right (CommensurabilityDecision Irreducible False False differing "event_or_observation_process_mismatch" Nothing)
  where
    differing = differingFields left right
    proof = Just (PoolingEvidence (outcomeId left, outcomeId right))

differingFields :: OutcomeDefinition -> OutcomeDefinition -> [Text]
differingFields left right =
  ["event" | outcomeEvent left /= outcomeEvent right]
    ++ ["observation_process" | outcomeProcess left /= outcomeProcess right]
    ++ ["window" | outcomeWindow left /= outcomeWindow right]
    ++ ["thresholds" | outcomeThresholds left /= outcomeThresholds right]

onlyBridgeableFields :: [Text] -> Bool
onlyBridgeableFields = all (\fieldName -> elem fieldName ["window", "thresholds"])

levelText :: CommensurabilityLevel -> Text
levelText level = case level of
  Direct -> "direct"
  Attested -> "attested"
  Bridgeable -> "bridgeable"
  Irreducible -> "irreducible"

parseAttestationEvidence :: OutcomeDefinition -> OutcomeDefinition -> Value -> Either KernelError AttestationEvidence
parseAttestationEvidence left right value = do
  object <- objectValue InvalidEvidence "attestation" value
  rejectUnknownFields InvalidEvidence
    ["attestor", "justification", "left_definition_id", "right_definition_id", "provenance"]
    object
  attestor <- requiredText InvalidEvidence "attestor" object
    >>= nonEmptyText InvalidEvidence "attestor"
  justification <- requiredText InvalidEvidence "justification" object
    >>= nonEmptyText InvalidEvidence "justification"
  leftId <- requiredText InvalidEvidence "left_definition_id" object
    >>= nonEmptyText InvalidEvidence "left_definition_id"
  rightId <- requiredText InvalidEvidence "right_definition_id" object
    >>= nonEmptyText InvalidEvidence "right_definition_id"
  provenance <- requiredText InvalidEvidence "provenance" object
    >>= nonEmptyText InvalidEvidence "provenance"
  if samePair (outcomeId left, outcomeId right) (leftId, rightId)
    then pure (AttestationEvidence attestor justification leftId rightId provenance)
    else Left (KernelError InvalidEvidence "attestation endpoints do not match compared definitions")

parseBridgeEvidence :: OutcomeDefinition -> OutcomeDefinition -> Value -> Either KernelError BridgeEvidence
parseBridgeEvidence left right value = do
  object <- objectValue InvalidEvidence "bridge" value
  rejectUnknownFields InvalidEvidence
    [ "left_definition_id", "right_definition_id", "transformation_id"
    , "retained_observation_manifest", "provenance_reference"
    ] object
  leftId <- requiredText InvalidEvidence "left_definition_id" object
    >>= nonEmptyText InvalidEvidence "left_definition_id"
  rightId <- requiredText InvalidEvidence "right_definition_id" object
    >>= nonEmptyText InvalidEvidence "right_definition_id"
  transformation <- requiredText InvalidEvidence "transformation_id" object
    >>= nonEmptyText InvalidEvidence "transformation_id"
  manifest <- requiredText InvalidEvidence "retained_observation_manifest" object
    >>= nonEmptyText InvalidEvidence "retained_observation_manifest"
  provenance <- requiredText InvalidEvidence "provenance_reference" object
    >>= nonEmptyText InvalidEvidence "provenance_reference"
  if samePair (outcomeId left, outcomeId right) (leftId, rightId)
    then pure (BridgeEvidence leftId rightId transformation manifest provenance)
    else Left (KernelError InvalidEvidence "bridge endpoints do not match compared definitions")

validateAttestationPair :: OutcomeDefinition -> OutcomeDefinition -> AttestationEvidence -> Either KernelError ()
validateAttestationPair left right evidence
  | samePair (outcomeId left, outcomeId right) (attestationLeftId evidence, attestationRightId evidence) = Right ()
  | otherwise = Left (KernelError InvalidEvidence "attestation endpoints do not match compared definitions")

validateBridgePair :: OutcomeDefinition -> OutcomeDefinition -> BridgeEvidence -> Either KernelError ()
validateBridgePair left right evidence
  | samePair (outcomeId left, outcomeId right) (bridgeLeftId evidence, bridgeRightId evidence) = Right ()
  | otherwise = Left (KernelError InvalidEvidence "bridge endpoints do not match compared definitions")

validateMaybe :: (a -> Either e ()) -> Maybe a -> Either e ()
validateMaybe _ Nothing = Right ()
validateMaybe validate (Just value) = validate value

samePair :: (Text, Text) -> (Text, Text) -> Bool
samePair (leftA, rightA) (leftB, rightB) =
  (leftA == leftB && rightA == rightB) || (leftA == rightB && rightA == leftB)

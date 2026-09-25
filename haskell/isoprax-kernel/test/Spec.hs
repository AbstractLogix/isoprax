{-# LANGUAGE OverloadedStrings #-}

module Main (main) where

import Control.Monad (unless)
import qualified Data.ByteString as ByteString
import qualified Data.ByteString.Char8 as ByteString8
import qualified Data.ByteString.Lazy as LazyByteString
import Data.Aeson
  ( Object
  , Value (..)
  , decodeStrict'
  , encode
  , object
  , (.=)
  )
import qualified Data.Aeson.Key
import qualified Data.Aeson.KeyMap
import Data.Maybe (fromMaybe)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as TextEncoding
import Isoprax.Kernel
import Isoprax.Kernel.Protocol (handleLine)
import Test.QuickCheck
import System.Exit (exitFailure)

main :: IO ()
main = do
  results <- mapM runProperty
    [ ("direct reflexivity", property propReflexive)
    , ("commensurability symmetry", property propSymmetry)
    , ("incompatible definitions fail closed", property propIncompatibleFailClosed)
    , ("typed attestation and bridge evidence authorize only their rule", property propTypedEvidence)
    , ("threshold order is irrelevant", property propThresholdOrder)
    , ("missing bridge fails closed", property propMissingBridge)
    , ("malformed windows fail closed", property propMalformedRejected)
    , ("canonical identity ignores object key order", property propIdentityOrder)
    , ("canonical serialization round trips", property propCanonicalRoundTrip)
    , ("Stage 0 never upgrades to Semantic or Full", property propStage0Ceiling)
    ]
  unless (all isSuccess results) exitFailure

runProperty :: (String, Property) -> IO Result
runProperty (caseName, propertyValue) = do
  putStrLn ("property: " ++ caseName)
  quickCheckWithResult stdArgs { maxSuccess = 1000 } propertyValue

propReflexive :: Property
propReflexive =
  forAll (listOf1 (elements ['a' .. 'z'])) $ \event ->
    case makeDefinition "left" (Text.pack event) 7 [] of
      Left _ -> False
      Right definition ->
        case checkCommensurability definition definition Nothing Nothing of
          Right result ->
            decisionLevel result == Direct
              && decisionCommensurable result
              && decisionPoolingAllowed result
              && null (decisionDifferingFields result)
          Left _ -> False

propSymmetry :: Property
propSymmetry =
  forAll (choose (1, 180)) $ \leftDays ->
    forAll (choose (1, 180)) $ \rightDays ->
      forAll arbitrary $ \sameEvent ->
        case (makeDefinition "left" "defect" leftDays [], makeDefinition "right" (if sameEvent then "defect" else "job failure") rightDays []) of
          (Right left, Right right) ->
            case (checkCommensurability left right Nothing Nothing, checkCommensurability right left Nothing Nothing) of
              (Right forward, Right reverseDecision) ->
                decisionLevel forward == decisionLevel reverseDecision
                  && decisionCommensurable forward == decisionCommensurable reverseDecision
                  && decisionPoolingAllowed forward == decisionPoolingAllowed reverseDecision
                  && decisionDifferingFields forward == decisionDifferingFields reverseDecision
              _ -> False
          _ -> False

propIncompatibleFailClosed :: Int -> Bool
propIncompatibleFailClosed generatedInput =
  let days = abs (rem generatedInput 180) + 1
      eventMismatch = even generatedInput
      leftEvent = "defect"
      rightEvent = if eventMismatch then "job failure" else leftEvent
      leftSource = if eventMismatch then "same" else "source-a"
      rightSource = if eventMismatch then "same" else "source-b"
      attestation = object
        [ "attestor" .= ("reviewer" :: Text.Text)
        , "justification" .= ("explicit review" :: Text.Text)
        , "left_definition_id" .= ("left" :: Text.Text)
        , "right_definition_id" .= ("right" :: Text.Text)
        , "provenance" .= ("record-1" :: Text.Text)
        ]
      bridge = object
        [ "left_definition_id" .= ("left" :: Text.Text)
        , "right_definition_id" .= ("right" :: Text.Text)
        , "transformation_id" .= ("transform-1" :: Text.Text)
        , "retained_observation_manifest" .= ("observations-1" :: Text.Text)
        , "provenance_reference" .= ("record-2" :: Text.Text)
        ]
      left = parseOutcomeDefinition (definitionValueWithSource "left" leftEvent days leftSource [])
      right = parseOutcomeDefinition (definitionValueWithSource "right" rightEvent days rightSource [])
  in case (left, right) of
    (Right leftDefinition, Right rightDefinition) ->
      case checkCommensurability leftDefinition rightDefinition (Just attestation) (Just bridge) of
        Right result ->
          decisionLevel result == Irreducible
            && not (decisionCommensurable result)
            && not (decisionPoolingAllowed result)
            && decisionPoolingEvidence result == Nothing
        Left _ -> False
    _ -> False

propTypedEvidence :: Int -> Bool
propTypedEvidence generatedInput =
  let days = abs (rem generatedInput 180) + 1
      left = makeDefinition "left" "defect" days []
      right = makeDefinition "right" "defect" (days + 1) []
      attestation = object
        [ "attestor" .= ("reviewer" :: Text.Text)
        , "justification" .= ("explicit review" :: Text.Text)
        , "left_definition_id" .= ("left" :: Text.Text)
        , "right_definition_id" .= ("right" :: Text.Text)
        , "provenance" .= ("record-1" :: Text.Text)
        ]
      bridge = object
        [ "left_definition_id" .= ("left" :: Text.Text)
        , "right_definition_id" .= ("right" :: Text.Text)
        , "transformation_id" .= ("transform-1" :: Text.Text)
        , "retained_observation_manifest" .= ("observations-1" :: Text.Text)
        , "provenance_reference" .= ("record-2" :: Text.Text)
        ]
  in case (left, right) of
    (Right leftDefinition, Right rightDefinition) ->
      case (parseAttestationEvidence leftDefinition rightDefinition attestation,
            parseBridgeEvidence leftDefinition rightDefinition bridge) of
        (Right attestationProof, Right bridgeProof) ->
          case ( checkCommensurabilityWithEvidence leftDefinition rightDefinition (Just attestationProof) Nothing
               , checkCommensurabilityWithEvidence leftDefinition rightDefinition Nothing (Just bridgeProof)
               ) of
            (Right attested, Right bridged) ->
              decisionLevel attested == Attested
                && decisionPoolingAllowed attested
                && decisionCommensurable attested
                && decisionLevel bridged == Bridgeable
                && decisionPoolingAllowed bridged
                && not (decisionCommensurable bridged)
            _ -> False
        _ -> False
    _ -> False

propThresholdOrder :: Int -> Bool
propThresholdOrder generatedInput =
  let days = abs (rem generatedInput 180) + 1
  in case (makeDefinition "left" "defect" days thresholds, makeDefinition "right" "defect" days (reverse thresholds)) of
    (Right left, Right right) ->
      case checkCommensurability left right Nothing Nothing of
        Right result -> decisionLevel result == Direct && decisionDifferingFields result == []
        Left _ -> False
    _ -> False
  where
    thresholds =
      [ object ["metric" .= ("severity" :: Text.Text), "operator" .= (">=" :: Text.Text), "value" .= (2 :: Int)]
      , object ["metric" .= ("age" :: Text.Text), "operator" .= ("<" :: Text.Text), "value" .= (10 :: Int)]
      ]

propMissingBridge :: Int -> Bool
propMissingBridge generatedInput =
  let days = abs (rem generatedInput 365) + 1
  in case (makeDefinition "left" "defect" days [], makeDefinition "right" "defect" (days + 1) []) of
    (Right left, Right right) ->
      case checkCommensurability left right Nothing Nothing of
        Right result ->
          decisionLevel result == Bridgeable
            && not (decisionCommensurable result)
            && not (decisionPoolingAllowed result)
            && decisionReasonCode result == "bridge_evidence_missing"
        Left _ -> False
    _ -> False

propMalformedRejected :: Int -> Bool
propMalformedRejected generatedInput =
  let negativeDays = negate (abs (rem generatedInput 1000000) + 1)
  in case parseOutcomeDefinition (definitionValue "left" "defect" negativeDays []) of
    Left _ -> True
    Right _ -> False

propIdentityOrder :: Int -> Bool
propIdentityOrder inputNumber =
  let number = rem inputNumber 1000000
      first = ByteString8.pack
        ("{\"version\":1,\"operation\":\"identity\",\"value\":{\"b\":" ++ show number ++ ",\"a\":" ++ show number ++ "}}")
      second = ByteString8.pack
        ("{\"operation\":\"identity\",\"value\":{\"a\":" ++ show number ++ ",\"b\":" ++ show number ++ "},\"version\":1}")
  in handleLine first == handleLine second

propCanonicalRoundTrip :: Int -> Bool
propCanonicalRoundTrip generatedInput =
  let integer = rem generatedInput 1000000
      value = object
        [ "zeta" .= ("λ/雪" :: Text.Text)
        , "alpha" .= integer
        , "nested" .= object ["enabled" .= True]
        ]
  in case canonicalIdentity value of
    Left _ -> False
    Right original ->
      case decodeStrict' (TextEncoding.encodeUtf8 (identityCanonical original)) of
        Nothing -> False
        Just reparsed -> canonicalIdentity reparsed == Right original

propStage0Ceiling :: Int -> Bool
propStage0Ceiling generatedInput =
  let left = definitionValue "left" "defect" 30 []
      right = definitionValue "right" "defect" 30 []
      request = encode $ object
        [ "version" .= (1 :: Int)
        , "operation" .= ("conformance" :: Text.Text)
        , "left" .= left
        , "right" .= right
        , "left_scores" .= samples
        , "left_outcomes" .= outcomes
        , "right_scores" .= samples
        , "right_outcomes" .= outcomes
        , "min_events" .= (2 :: Int)
        , "n_bins" .= (2 :: Int)
        ]
      result = handleLine (LazyByteString.toStrict request)
      decoded = decodeStrict' result
      actualClass = case decoded of
        Just (Object response) -> fromMaybe Null (lookupField "declarable_class" response)
        _ -> Null
  in ByteString.isInfixOf "Cross-Family Conformance (Structural)" result
      && not (ByteString.isInfixOf "Cross-Family Conformance (Semantic)" result)
      && not (ByteString.isInfixOf "Full Conformance" result)
      && case actualClass of
        String text -> Text.isPrefixOf "Cross-Family Conformance (Structural)" text
        _ -> False
  where
    samples :: [Int]
    samples = if even generatedInput then [0, 1] else [0, 0]
    outcomes :: [Int]
    outcomes = [0, 1]

lookupField :: Text.Text -> Object -> Maybe Value
lookupField key = Data.Aeson.KeyMap.lookup (Data.Aeson.Key.fromText key)

makeDefinition :: Text.Text -> Text.Text -> Int -> [Value] -> Either KernelError OutcomeDefinition
makeDefinition identifier event days thresholds = parseOutcomeDefinition (definitionValue identifier event days thresholds)

definitionValue :: Text.Text -> Text.Text -> Int -> [Value] -> Value
definitionValue identifier event days thresholds =
  definitionValueWithSource identifier event days "" thresholds

definitionValueWithSource :: Text.Text -> Text.Text -> Int -> Text.Text -> [Value] -> Value
definitionValueWithSource identifier event days source thresholds =
  object
    [ "id" .= identifier
    , "event" .= event
    , "observation_process" .= object ["kind" .= ("build outcome" :: Text.Text), "parameters" .= object ["source" .= source]]
    , "window" .= object ["duration" .= days, "unit" .= ("day" :: Text.Text), "anchor" .= ("after change" :: Text.Text)]
    , "thresholds" .= thresholds
    ]

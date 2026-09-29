{-# LANGUAGE OverloadedStrings #-}

module Main (main) where

import Control.Monad (unless)
import Data.Aeson (Value (..), object, toJSON, (.=))
import Data.Text (Text)
import Data.Text qualified as Text
import Isoprax.Oracle
import System.Exit (exitFailure)
import Test.QuickCheck

main :: IO ()
main = do
  run "normalized definitions with different IDs remain commensurable" propNormalizedDefinitions
  run "changes to event, process, window, or threshold fail closed" propSemanticFieldChanges
  run "same ID with changed definition content cannot reuse calibration" propChangedContentFails
  run "different calibration policies cannot authorize pooling" propPolicyMismatchFails
  run "pooled evaluation rejects substituted samples" propSampleSubstitutionFails
  run "authorized pooling uses the evidence-bound policy" propAuthorizedPoolingSucceeds
  where
    run propertyName propertyValue = do
      putStrLn propertyName
      result <- quickCheckWithResult (stdArgs {maxSuccess = 2000}) propertyValue
      unless (isSuccess result) exitFailure

propNormalizedDefinitions :: Int -> Bool
propNormalizedDefinitions seed =
  let suffix = Text.pack (show seed)
      left = must (parseDefinition (definitionValue ("left-" <> suffix) " Pump Failure " reversedPairs))
      right = must (parseDefinition (definitionValue ("right-" <> suffix) "pump failure" objectParameters))
      relationship = establishCommensurability left right
      leftCalibration = establishCalibration left defaultPolicy scores outcomes
      rightCalibration = establishCalibration right defaultPolicy scores outcomes
  in case (relationship, leftCalibration, rightCalibration) of
       (Right commensurability, Right leftEvidence, Right rightEvidence) ->
         either (const False) (const True) (authorizePooledComparison commensurability leftEvidence rightEvidence)
       _ -> False

propSemanticFieldChanges :: Int -> Bool
propSemanticFieldChanges seed =
  let suffix = Text.pack (show seed)
      left = must (parseDefinition (definitionValue ("same-" <> suffix) "event old" objectParameters))
      changedDefinitions = map (must . parseDefinition)
        [ definitionValue ("same-" <> suffix) "event new" objectParameters
        , definitionValueWith ("same-" <> suffix) "event old" "scheduler" 1.0 0.7 objectParameters
        , definitionValueWith ("same-" <> suffix) "event old" "telemetry" 2.0 0.7 objectParameters
        , definitionValueWith ("same-" <> suffix) "event old" "telemetry" 1.0 0.8 objectParameters
        ]
  in case traverse (establishCommensurability left) changedDefinitions of
       Left _ -> True
       Right _ -> False

propChangedContentFails :: Int -> Bool
propChangedContentFails seed =
  let suffix = Text.pack (show seed)
      old = must (parseDefinition (definitionValue ("shared-" <> suffix) "event old" objectParameters))
      new = must (parseDefinition (definitionValue ("shared-" <> suffix) "event new" objectParameters))
      commensurability = establishCommensurability old old
      leftEvidence = establishCalibration new defaultPolicy scores outcomes
      rightEvidence = establishCalibration old defaultPolicy scores outcomes
  in case (commensurability, leftEvidence, rightEvidence) of
       (Right comm, Right leftCal, Right rightCal) ->
         case authorizePooledComparison comm leftCal rightCal of
           Left _ -> True
           Right _ -> False
       _ -> False

propPolicyMismatchFails :: Int -> Bool
propPolicyMismatchFails seed =
  let suffix = Text.pack (show seed)
      left = must (parseDefinition (definitionValue ("left-" <> suffix) "same event" objectParameters))
      right = must (parseDefinition (definitionValue ("right-" <> suffix) "same event" objectParameters))
      leftPolicy = must (parseCalibrationPolicy (policyValue 4 2 1.0))
      rightPolicy = must (parseCalibrationPolicy (policyValue 4 3 1.0))
      commensurability = establishCommensurability left right
      leftEvidence = establishCalibration left leftPolicy scores outcomes
      rightEvidence = establishCalibration right rightPolicy scores outcomes
  in case (commensurability, leftEvidence, rightEvidence) of
       (Right comm, Right leftCal, Right rightCal) ->
         case authorizePooledComparison comm leftCal rightCal of
           Left _ -> True
           Right _ -> False
       _ -> False

propSampleSubstitutionFails :: Int -> Bool
propSampleSubstitutionFails seed =
  let suffix = Text.pack (show seed)
      left = must (parseDefinition (definitionValue ("left-" <> suffix) "same event" objectParameters))
      right = must (parseDefinition (definitionValue ("right-" <> suffix) "same event" objectParameters))
      commensurability = establishCommensurability left right
      leftEvidence = establishCalibration left defaultPolicy scores outcomes
      rightEvidence = establishCalibration right defaultPolicy scores outcomes
      changedScores = 0.11 : drop 1 scores
  in case (commensurability, leftEvidence, rightEvidence) of
       (Right comm, Right leftCal, Right rightCal) ->
         case authorizePooledComparison comm leftCal rightCal of
           Left _ -> False
           Right authorization ->
             case authorizedPooledEce authorization changedScores outcomes scores outcomes of
               Left _ -> True
               Right _ -> False
       _ -> False

propAuthorizedPoolingSucceeds :: Int -> Bool
propAuthorizedPoolingSucceeds seed =
  let suffix = Text.pack (show seed)
      left = must (parseDefinition (definitionValue ("left-" <> suffix) "same event" objectParameters))
      right = must (parseDefinition (definitionValue ("right-" <> suffix) "same event" objectParameters))
      commensurability = establishCommensurability left right
      leftEvidence = establishCalibration left defaultPolicy scores outcomes
      rightEvidence = establishCalibration right defaultPolicy scores outcomes
  in case (commensurability, leftEvidence, rightEvidence) of
       (Right comm, Right leftCal, Right rightCal) ->
         case authorizePooledComparison comm leftCal rightCal of
           Left _ -> False
           Right authorization ->
             case authorizedPooledEce authorization scores outcomes scores outcomes of
               Left _ -> False
               Right ece -> ece >= 0 && ece <= 1
       _ -> False

definitionValue :: Text -> Text -> Value -> Value
definitionValue identifier event parameters =
  definitionValueWith identifier event " telemetry " 1.0 0.7 parameters

definitionValueWith :: Text -> Text -> Text -> Double -> Double -> Value -> Value
definitionValueWith identifier event processKind duration thresholdValue parameters = object
  [ "id" .= identifier
  , "event" .= event
  , "observation_process" .= object
      [ "kind" .= processKind
      , "parameters" .= parameters
      , "raw" .= (" raw process " :: Text)
      ]
  , "window" .= object
      [ "duration" .= duration
      , "unit" .= (" HOUR " :: Text)
      , "anchor" .= (" event " :: Text)
      , "raw" .= ("ignored display" :: Text)
      ]
  , "thresholds" .= ([object
      [ "metric" .= (" risk " :: Text)
      , "operator" .= (" > " :: Text)
      , "value" .= thresholdValue
      , "sustain" .= (Nothing :: Maybe Double)
      , "sustain_unit" .= ("" :: Text)
      , "raw" .= ("ignored display" :: Text)
      ]] :: [Value])
  , "description" .= ("display-only" :: Text)
  ]

reversedPairs :: Value
reversedPairs = toJSON
  ([ ["sensor", "s-1"], ["source", "line-1"] ] :: [[Text]])

objectParameters :: Value
objectParameters = object ["source" .= ("line-1" :: Text), "sensor" .= ("s-1" :: Text)]

policyValue :: Int -> Int -> Double -> Value
policyValue minEvents bins maxEce = object
  [ "min_events" .= minEvents
  , "n_bins" .= bins
  , "max_ece" .= maxEce
  ]

defaultPolicy :: CalibrationPolicy
defaultPolicy = must (parseCalibrationPolicy (policyValue 4 2 0.2))

scores :: [Double]
scores = [0.1, 0.9, 0.2, 0.8]

outcomes :: [Int]
outcomes = [0, 1, 0, 1]

must :: Show error => Either error value -> value
must (Right value) = value
must (Left failure) = error (show failure)

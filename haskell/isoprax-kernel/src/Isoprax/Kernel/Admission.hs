{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Admission (evaluateAdmission) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time
  ( LocalTime
  , UTCTime
  , defaultTimeLocale
  , localTimeToUTC
  , parseTimeM
  , utc
  )
import Isoprax.Kernel.Types

evaluateAdmission
  :: [AdmissionRow]
  -> [Text]
  -> [Text]
  -> Maybe ProvenanceInput
  -> Maybe PredeclarationInput
  -> AdmissionDecision
evaluateAdmission rows fittedIds gatedIds provenance predeclaration =
  AdmissionDecision
    { calibrationAdmission = calibrationGate
    , provenanceAdmission = provenanceGate
    }
  where
    calibrationGate
      | null fittedIds || null gatedIds =
          AdmissionGate False "calibration_evidence_required"
      | otherwise =
          let rowSplit = Map.fromList [(admissionRowId row, admissionRowSplit row) | row <- rows]
              fitted = traverse (\rowId -> Map.lookup rowId rowSplit) fittedIds
              gated = traverse (\rowId -> Map.lookup rowId rowSplit) gatedIds
          in case (fitted, gated) of
              (Nothing, _) -> AdmissionGate False "unknown_calibration_rows"
              (_, Nothing) -> AdmissionGate False "unknown_calibration_rows"
              (Just fitSplits, Just gateSplits)
                | not (null (intersectIds fittedIds gatedIds))
                    || any (/= "calibration_fit") fitSplits
                    || any (/= "calibration_gate") gateSplits ->
                      AdmissionGate False "calibration_fit_gate_overlap_or_split_mismatch"
                | otherwise -> AdmissionGate True "calibration_split_separated"

    provenanceGate = case provenance of
      Nothing -> AdmissionGate False "corpus_provenance_required"
      Just source
        | Text.null (Text.strip (provenanceSource source)) ->
            AdmissionGate False "corpus_provenance_required"
        | provenancePrivate source || provenancePrivileged source ->
            AdmissionGate False "private_or_privileged_provenance"
        | otherwise -> case predeclaration of
            Nothing -> AdmissionGate False "anchored_predeclaration_required"
            Just declaration
              | Text.null (Text.strip (predeclarationHash declaration))
                  || Text.null (Text.strip (predeclarationAnchor declaration)) ->
                    AdmissionGate False "predeclaration_hash_and_anchor_required"
              | otherwise -> case (parseUtc (predeclaredAt declaration), parseUtc (collectionStartedAt declaration)) of
                  (Just declared, Just started)
                    | declared < started -> AdmissionGate True "provenance_predeclaration_passed"
                    | otherwise -> AdmissionGate False "predeclaration_not_before_collection"
                  _ -> AdmissionGate False "invalid_predeclaration_timestamp"

intersectIds :: Eq a => [a] -> [a] -> [a]
intersectIds first second =
  filter (\item -> any (== item) second) first

parseUtc :: Text -> Maybe UTCTime
parseUtc value =
  let parsed = if Text.isSuffixOf "Z" value
        then Just (Text.dropEnd 1 value)
        else if Text.isSuffixOf "+00:00" value
          then Just (Text.dropEnd 6 value)
          else Nothing
  in case parsed of
      Nothing -> Nothing
      Just body ->
        (parseTimeM True defaultTimeLocale "%Y-%m-%dT%H:%M:%S%Q" (Text.unpack body) :: Maybe LocalTime)
          >>= Just . localTimeToUTC utc

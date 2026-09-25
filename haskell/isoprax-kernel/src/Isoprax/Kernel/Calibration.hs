{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Calibration
  ( evaluateCalibration
  , expectedCalibrationError
  , authorizePooledComparison
  ) where

import Data.Text (Text)
import Isoprax.Kernel.Types

evaluateCalibration
  :: Text
  -> CalibrationConfig
  -> [Double]
  -> [Int]
  -> Either KernelError CalibrationDecision
evaluateCalibration definitionId config scores outcomes = do
  if calibrationMinEvents config < 0 || calibrationBins config < 1
      || isNaN (calibrationMaxEce config) || isInfinite (calibrationMaxEce config)
      || calibrationMaxEce config < 0
    then Left (KernelError InvalidCalibrationInput "calibration configuration is invalid")
    else pure ()
  if length scores /= length outcomes
    then Left (KernelError InvalidCalibrationInput "scores and outcomes must have equal length")
    else pure ()
  if any (\score -> isNaN score || isInfinite score || score < 0 || score > 1) scores
    then Left (KernelError InvalidCalibrationInput "scores must be finite and in [0, 1]")
    else pure ()
  if any (\outcome -> outcome /= 0 && outcome /= 1) outcomes
    then Left (KernelError InvalidCalibrationInput "outcomes must be binary 0 or 1")
    else pure ()
  let count = length scores
      positives = length (filter (== 1) outcomes)
      negatives = count - positives
      ece = if count == 0 then 1 else expectedCalibrationError (calibrationBins config) scores outcomes
      hasVariance = case scores of
        [] -> False
        first : rest -> any (/= first) rest
      (passes, reason) =
        if count < calibrationMinEvents config then (False, "insufficient_labeled_events")
        else if positives == 0 || negatives == 0 then (False, "single_outcome_class")
        else if ece > calibrationMaxEce config then (False, "ece_exceeds_threshold")
        else if not hasVariance then (False, "degenerate_discrimination")
        else (True, "calibrated")
      evidence = if passes then Just (CalibratedEvidence definitionId count) else Nothing
  pure CalibrationDecision
    { calibrationPassed = passes
    , calibrationEce = ece
    , calibrationCount = count
    , calibrationReasonCode = reason
    , calibrationEvidence = evidence
    }

expectedCalibrationError :: Int -> [Double] -> [Int] -> Double
expectedCalibrationError bins scores outcomes
  | null scores = 0
  | otherwise =
      let assigned = zip scores outcomes
          edge index
            | index == bins = 1
            | otherwise = fromIntegral index * (1 / fromIntegral bins)
          ecePart index =
            let lower = edge index
                upper = edge (index + 1)
                inBin (score, _) =
                  score >= lower
                    && (if index == bins - 1 then score <= upper else score < upper)
                members = filter inBin assigned
                size = length members
            in if size == 0
                then 0
                else
                  let meanScore = sum (map fst members) / fromIntegral size
                      meanOutcome = fromIntegral (sum (map snd members)) / fromIntegral size
                  in fromIntegral size * abs (meanScore - meanOutcome)
          weighted = foldl' (\total index -> total + ecePart index) 0 [0 .. bins - 1]
      in weighted / fromIntegral (length scores)

authorizePooledComparison
  :: PoolingEvidence
  -> CalibratedEvidence
  -> CalibratedEvidence
  -> Either KernelError PoolingAuthorization
authorizePooledComparison (PoolingEvidence (leftId, rightId)) leftCal rightCal
  | matches (calibratedDefinitionId leftCal, calibratedDefinitionId rightCal) (leftId, rightId) =
      Right (PoolingAuthorization leftId rightId)
  | otherwise =
      Left (KernelError InvalidEvidence "calibration evidence does not match pooled definitions")
  where
    matches (a, b) (x, y) =
      (a == x && b == y) || (a == y && b == x)

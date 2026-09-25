{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Conformance (projectStage0) where

import Data.Text (Text)
import Isoprax.Kernel.Calibration (expectedCalibrationError)
import Isoprax.Kernel.Types

projectStage0
  :: Int
  -> CommensurabilityDecision
  -> CalibrationDecision
  -> CalibrationDecision
  -> [Double]
  -> [Int]
  -> [Double]
  -> [Int]
  -> ConformanceDecision
projectStage0 bins commensurability leftCalibration rightCalibration leftScores leftOutcomes rightScores rightOutcomes =
  ConformanceDecision
    { conformanceCommensurability = commensurability
    , conformanceLeftCalibration = leftCalibration
    , conformanceRightCalibration = rightCalibration
    , conformancePooledEce =
        if decisionPoolingAllowed commensurability
          then Just (expectedCalibrationError bins (leftScores ++ rightScores) (leftOutcomes ++ rightOutcomes))
          else Nothing
    , conformanceDeclarableClass = stage0Label
    }
  where
    base :: Text
    base = "Cross-Family Conformance (Structural)"

    withCommensurability
      | decisionCommensurable commensurability =
          base <> ", commensurability established but Semantic/Full claims are outside Stage 0"
      | decisionPoolingAllowed commensurability =
          base <> ", pooling permitted by retained-observation evidence"
      | otherwise = base

    calibrated =
      calibrationPassed leftCalibration && calibrationPassed rightCalibration

    stage0Label =
      if calibrated
        then withCommensurability
        else withCommensurability <> ", uncalibrated"

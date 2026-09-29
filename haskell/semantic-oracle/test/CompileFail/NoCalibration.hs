{-# LANGUAGE OverloadedStrings #-}

module NoCalibration where

import Data.Text (Text)
import Isoprax.Oracle

invalid :: Either Text PoolingAuthorization
invalid = authorizePooledComparison (undefined :: CommensurabilityEvidence) (undefined :: CalibrationEvidence)

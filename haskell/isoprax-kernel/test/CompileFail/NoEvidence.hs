module NoEvidence where

import Isoprax.Kernel

invalid :: CalibratedEvidence -> CalibratedEvidence -> Either KernelError PoolingAuthorization
invalid leftCalibration rightCalibration =
  authorizePooledComparison leftCalibration rightCalibration

module OneCalibration where

import Isoprax.Kernel

invalid :: PoolingEvidence -> CalibratedEvidence -> Either KernelError PoolingAuthorization
invalid proof leftCalibration = authorizePooledComparison proof leftCalibration

module NoCalibration where

import Isoprax.Kernel

invalid :: PoolingEvidence -> Either KernelError PoolingAuthorization
invalid proof = authorizePooledComparison proof

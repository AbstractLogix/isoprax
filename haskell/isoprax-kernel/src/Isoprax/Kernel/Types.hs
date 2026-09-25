{-# LANGUAGE OverloadedStrings #-}

module Isoprax.Kernel.Types where

import Data.Scientific (Scientific)
import Data.Text (Text)

data ErrorCategory
  = InvalidJson
  | DuplicateKey
  | UnsupportedVersion
  | UnknownOperation
  | InvalidOutcomeDefinition
  | InvalidEvidence
  | InvalidCalibrationInput
  | InvalidAdmissionInput
  | InvalidIdentityValue
  deriving (Eq, Ord, Show)

errorCategoryText :: ErrorCategory -> Text
errorCategoryText category = case category of
  InvalidJson -> "invalid_json"
  DuplicateKey -> "duplicate_key"
  UnsupportedVersion -> "unsupported_version"
  UnknownOperation -> "unknown_operation"
  InvalidOutcomeDefinition -> "invalid_outcome_definition"
  InvalidEvidence -> "invalid_evidence"
  InvalidCalibrationInput -> "invalid_calibration_input"
  InvalidAdmissionInput -> "invalid_admission_input"
  InvalidIdentityValue -> "invalid_identity_value"

data KernelError = KernelError
  { errorCategory :: ErrorCategory
  , errorDetail :: Text
  }
  deriving (Eq, Show)

data Scalar
  = ScalarNull
  | ScalarText Text
  | ScalarNumber Scientific
  deriving (Eq, Ord, Show)

data OutcomeDefinition = OutcomeDefinition
  { outcomeId :: Text
  , outcomeEvent :: Text
  , outcomeProcess :: (Text, [(Text, Text)], Text)
  , outcomeWindow :: (Maybe Double, Text, Text)
  , outcomeThresholds :: [(Text, Text, Maybe Scalar, Maybe Double, Text)]
  }
  deriving (Eq, Show)

data AttestationEvidence = AttestationEvidence
  { attestationAttestor :: Text
  , attestationJustification :: Text
  , attestationLeftId :: Text
  , attestationRightId :: Text
  , attestationProvenance :: Text
  }
  deriving (Eq, Show)

data BridgeEvidence = BridgeEvidence
  { bridgeLeftId :: Text
  , bridgeRightId :: Text
  , bridgeTransformationId :: Text
  , bridgeObservationManifest :: Text
  , bridgeProvenance :: Text
  }
  deriving (Eq, Show)

data CommensurabilityLevel = Direct | Attested | Bridgeable | Irreducible
  deriving (Eq, Ord, Show)

newtype PoolingEvidence = PoolingEvidence (Text, Text)
  deriving (Eq, Show)

data CommensurabilityDecision = CommensurabilityDecision
  { decisionLevel :: CommensurabilityLevel
  , decisionCommensurable :: Bool
  , decisionPoolingAllowed :: Bool
  , decisionDifferingFields :: [Text]
  , decisionReasonCode :: Text
  , decisionPoolingEvidence :: Maybe PoolingEvidence
  }
  deriving (Eq, Show)

data CalibrationConfig = CalibrationConfig
  { calibrationMinEvents :: Int
  , calibrationBins :: Int
  , calibrationMaxEce :: Double
  }
  deriving (Eq, Show)

defaultCalibrationConfig :: CalibrationConfig
defaultCalibrationConfig = CalibrationConfig 500 10 0.05

data CalibratedEvidence = CalibratedEvidence
  { calibratedDefinitionId :: Text
  , calibratedSampleCount :: Int
  }
  deriving (Eq, Show)

data CalibrationDecision = CalibrationDecision
  { calibrationPassed :: Bool
  , calibrationEce :: Double
  , calibrationCount :: Int
  , calibrationReasonCode :: Text
  , calibrationEvidence :: Maybe CalibratedEvidence
  }
  deriving (Eq, Show)

data PoolingAuthorization = PoolingAuthorization
  { authorizationLeftId :: Text
  , authorizationRightId :: Text
  }
  deriving (Eq, Show)

data AdmissionRow = AdmissionRow
  { admissionRowId :: Text
  , admissionRowSplit :: Text
  }
  deriving (Eq, Show)

data ProvenanceInput = ProvenanceInput
  { provenanceSource :: Text
  , provenancePrivate :: Bool
  , provenancePrivileged :: Bool
  }
  deriving (Eq, Show)

data PredeclarationInput = PredeclarationInput
  { predeclarationHash :: Text
  , predeclarationAnchor :: Text
  , predeclaredAt :: Text
  , collectionStartedAt :: Text
  }
  deriving (Eq, Show)

data AdmissionGate = AdmissionGate
  { admissionGatePassed :: Bool
  , admissionGateReason :: Text
  }
  deriving (Eq, Show)

data AdmissionDecision = AdmissionDecision
  { calibrationAdmission :: AdmissionGate
  , provenanceAdmission :: AdmissionGate
  }
  deriving (Eq, Show)

data ConformanceDecision = ConformanceDecision
  { conformanceCommensurability :: CommensurabilityDecision
  , conformanceLeftCalibration :: CalibrationDecision
  , conformanceRightCalibration :: CalibrationDecision
  , conformancePooledEce :: Maybe Double
  , conformanceDeclarableClass :: Text
  }
  deriving (Eq, Show)

data CanonicalIdentity = CanonicalIdentity
  { identityCanonical :: Text
  , identitySha256 :: Text
  }
  deriving (Eq, Show)

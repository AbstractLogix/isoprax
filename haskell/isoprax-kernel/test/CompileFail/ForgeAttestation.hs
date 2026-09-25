module ForgeAttestation where

import Data.Text (Text)
import Isoprax.Kernel

invalid :: AttestationEvidence
invalid = AttestationEvidence "reviewer" "reviewed" "left" "right" ("provenance" :: Text)

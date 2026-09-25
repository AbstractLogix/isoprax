module ForgeBridge where

import Data.Text (Text)
import Isoprax.Kernel

invalid :: BridgeEvidence
invalid = BridgeEvidence "left" "right" "transform" "manifest" ("provenance" :: Text)

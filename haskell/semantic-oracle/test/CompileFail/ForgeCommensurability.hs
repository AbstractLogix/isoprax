module ForgeCommensurability where

import Isoprax.Oracle (CommensurabilityEvidence)

forged :: CommensurabilityEvidence
forged = CommensurabilityEvidence "left" "right" "digest-a" "digest-b"

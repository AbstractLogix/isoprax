#!/usr/bin/env bash
set -euo pipefail

package_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$package_root"

expect_failure() {
  local file="$1"
  local symbol="$2"
  local output
  if output="$(cabal exec -- ghc -fno-code -package isoprax-kernel "$file" 2>&1)"; then
    echo "expected compilation to fail: $file" >&2
    exit 1
  fi
  if ! grep -q "$symbol" <<<"$output"; then
    echo "compilation failed for an unrelated reason: $file" >&2
    printf '%s\n' "$output" >&2
    exit 1
  fi
}

expect_failure test/CompileFail/NoEvidence.hs PoolingEvidence
expect_failure test/CompileFail/NoCalibration.hs CalibratedEvidence
expect_failure test/CompileFail/OneCalibration.hs CalibratedEvidence
expect_failure test/CompileFail/ForgeEvidence.hs PoolingEvidence
expect_failure test/CompileFail/ForgeAttestation.hs AttestationEvidence
expect_failure test/CompileFail/ForgeBridge.hs BridgeEvidence
echo "compile-fail API checks passed"

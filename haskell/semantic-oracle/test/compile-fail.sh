#!/usr/bin/env bash
set -euo pipefail

package_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$package_root"

expect_failure() {
  local file="$1"
  local symbol="$2"
  local output
  if output="$(cabal exec -- ghc -fno-code -package isoprax-semantic-oracle "$file" 2>&1)"; then
    echo "expected compilation to fail: $file" >&2
    exit 1
  fi
  if ! grep -q "$symbol" <<<"$output"; then
    echo "compilation failed for an unrelated reason: $file" >&2
    printf '%s\n' "$output" >&2
    exit 1
  fi
}

expect_failure test/CompileFail/ForgeCommensurability.hs CommensurabilityEvidence
expect_failure test/CompileFail/ForgeCalibration.hs CalibrationEvidence
expect_failure test/CompileFail/NoCalibration.hs authorizePooledComparison
echo "compile-fail API checks passed"

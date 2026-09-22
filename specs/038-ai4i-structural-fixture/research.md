# Research: AI4I 2020 Structural Fixture

## Decision 1: Use the UCI artifact as the authoritative source

- **Decision**: Pin the UCI Machine Learning Repository record, DOI
  `10.24432/C5HS5C`, CC BY 4.0 license, source ZIP checksum, and extracted CSV
  checksum. Record the Kaggle URL only as a mirror/discovery reference.
- **Rationale**: The user supplied the Kaggle mirror, but the UCI record provides
  the canonical dataset metadata and reproducible download reference. The local
  verification run identified the exact source ZIP and CSV bytes.
- **Observed source identity**: ZIP SHA-256
  `f601f14294bcf190f9d720676b7f0aea46a26cde9ab8ebc7b4f8174d9d26b252`; extracted
  CSV SHA-256 `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`.

## Decision 2: Do not fetch or vendor the external snapshot

- **Decision**: Require an explicit local CSV path. Keep only the provenance
  manifest and verifier in the repository.
- **Rationale**: This follows the existing public-label evidence boundary, keeps
  tests offline, avoids silently changing external state, and makes the artifact
  identity an explicit operator responsibility.
- **Rejected**: A runtime download path, because network availability would become
  part of verification and a changed mirror could be mistaken for the pinned data.

## Decision 3: Preserve published label inconsistencies

- **Decision**: Report the observed composite/mode disagreement instead of
  deriving or repairing `Machine failure` from the five mode flags.
- **Rationale**: The downloaded 10,000-row CSV contains 339 composite failures,
  46 TWF, 115 HDF, 95 PWF, 98 OSF, and 19 RNF labels; 9 failure rows have no mode
  flag, 18 non-failure rows have at least one mode flag, and 24 rows have multiple
  mode flags. These are important structural facts for a label-semantics test.
- **Rejected**: Normalizing the composite label to the mode OR, because that would
  destroy source evidence and conceal a reproducibility issue.

## Decision 4: Use the dataset as a negative commensurability fixture

- **Decision**: Define separate current-process sensor outcomes for the composite
  failure and each mode. Expect comparisons between them to be irreducible due to
  event mismatch, with pooling disabled.
- **Rationale**: Multiple labels in one table are not automatically one event or
  one commensurable family. The fixture tests the existing guard without claiming
  that manufacturing sensor outcomes are equivalent to JIT defect outcomes.
- **Rejected**: Treating all six labels as interchangeable classes or treating
  calibration as a semantic bridge.

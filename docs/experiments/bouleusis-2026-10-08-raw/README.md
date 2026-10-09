# Selected Bouleusis research records

## Provenance

These files are lossless gzip snapshots of selected original research records from `AbstractLogix/Bouleusis`, source commit `9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5`. The source paths, Git blob IDs, original byte counts, line counts, record counts, and SHA-256 digests are in [manifest.json](manifest.json). Decompressing each file reproduces the original source bytes. The records have not been rewritten.

The Bouleusis repository is private. The repository owner explicitly authorized public release of the selected original research data listed in the manifest. This permission applies to these selected data files only. It does not authorize publication of the Bouleusis source repository or third-party materials.

## License

The selected original research data files in this directory are released under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Reuse must follow the license terms, including attribution and a link to the license. The machine-readable `public_release` section records the scope and authorization date.

This data license is separate from the IsoPrax source-code license. It does not apply to Bouleusis source code, model weights, third-party datasets, or any material excluded in the manifest. The source repository's historical license metadata remains `NOASSERTION`; the owner's separate authorization and this public data license apply only to the selected records here.

## Privacy and third-party scan

Before release, the package was scanned for common credential patterns, email addresses, URLs, and local home-directory paths. The scan is a limited pattern check. It cannot establish the absence of every secret, personal identifier, copyrighted excerpt, or third-party right. The selected records are synthetic experiment logs. No private Bouleusis source code or model weights are included.

## Reproduction

From the repository root, run:

```sh
uv run python scripts/paper_integrity.py --check-only
```

The integrity runner checks each compressed artifact against the manifest, decompresses it, and verifies its original SHA-256, byte count, line count, and record count. The runner does not establish that the experiment's constructs or labels are scientifically valid.

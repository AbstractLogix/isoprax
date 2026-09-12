# Data Model

Release identity is the tuple:

```text
(git tag vX.Y.Z, pyproject.toml project.version, CHANGELOG.md [X.Y.Z] entry)
```

The tag must equal the package version with a `v` prefix. The matching
changelog section must contain at least one descriptive bullet.

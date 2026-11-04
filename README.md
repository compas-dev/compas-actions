# compas-actions

Bounded GitHub Actions that make the safe path easy for COMPAS repositories.

The v2 contract shares repeatable mechanics without hiding repository policy.
Calling workflows keep their matrices, permissions, Conda/native provisioning,
direct quality commands, artifact composition, and trusted-publishing jobs.
For compatibility and simple hybrid jobs, `ci` and `setup-python` can provision
Conda from an explicit, repository-owned environment file. New hybrid/native
workflows should keep provisioning visible in the caller, as the OCC example
does, when additional system or native steps are part of the contract.

## Actions

| Action | Responsibility |
| --- | --- |
| `ci` | Set up one caller-owned matrix job and optionally run existing Invoke tasks |
| `setup-python` | Run frozen `uv sync` or provision an explicit Conda environment |
| `docs` | Build strict MkDocs documentation or deploy it with Mike |
| `package` | Build or verify distributions, inspect wheels, install them, and smoke-test imports |
| `prepare-release` | Build, verify, and upload one pure-Python distribution set |
| `release-assets` | Upload caller-built assets, with optional Invoke generation |
| `release-check` | Detect and validate repository-owned release metadata changes |
| `release-pr` | Bump a version and open a human-reviewed release pull request |
| `pr-checks` | Enforce changelog policy |
| `github-release` | Download verified artifacts and create a GitHub release |
| `ghpython-components` | Build Rhino 8 CPython components from an immutable componentizer revision |

The preferred v2 CI job keeps direct commands visible and locally reproducible:

```yaml
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  - uses: compas-dev/compas-actions/setup-python@<immutable-v2-commit>
    with:
      python-version: ${{ matrix.python }}
      dependency-groups: dev
      extras: ""
  - run: uv run ruff check .
  - run: uv run ruff format --check .
  - run: uv run pyright
  - run: uv run pytest
```

Repositories with established Invoke tasks can migrate incrementally with the
`ci` action or the optional pre-build inputs on `docs`, `prepare-release`, and
`release-assets`. Under uv, these always execute as `uv run invoke ...`; direct
commands remain the default in new examples.

Existing v1 consumers remain reproducible by pinning the v1 commit. V2
consumers must pin a reviewed full commit SHA with a readable version comment;
moving major tags are not an accepted security boundary.

## Profiles

- [Pure Python](examples/ci.yml) uses `setup-python` and direct commands.
- [OCC/Conda](examples/occ-conda.yml) provisions PythonOCC visibly and keeps
  native imports in the caller. Its documentation step sets
  `setup-project: false` and `prepared-conda-environment: compas` to reuse that
  prepared environment through `conda run` without uv sync.
- [CGAL/native wheel](examples/cgal-cibuildwheel.yml) keeps CMake and
  cibuildwheel visible, then uses `package` to verify the exact wheel set.

## Releases

Use a release pull request as the version and changelog authority. After merge:

1. `release-check` detects the reviewed release.
2. Repository jobs run their visible test/build matrices.
3. `prepare-release`, or a native caller plus `package`, builds and verifies the
   exact artifacts once.
4. A caller-owned job publishes those artifacts with PyPI OIDC.
5. `github-release` downloads the same artifacts and creates the release.
6. `docs` deploys versioned documentation where applicable.

The PyPI environment, `id-token: write`, workflow identity, and publishing step
remain visible in the calling repository. These actions never publish to PyPI.

`package` runs Twine validation, checks wheel metadata, installs each wheel in a
fresh environment when it is compatible with the current runner, and optionally
imports named modules. Native jobs can set `build: false` and point it at wheels
produced visibly by cibuildwheel. Every target-platform wheel must also be
installed and import-smoked on its matching runner; aggregate release jobs only
perform structural checks on non-host wheels.

## Security

Every external action used inside this repository is pinned to a reviewed full
commit SHA. Action updates should arrive through reviewed dependency pull
requests. Deploying documentation, publishing packages, moving tags, and
changing repository settings remain explicit maintainer operations.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the boundary and
[MIGRATION.md](MIGRATION.md) for v1-to-v2 changes.

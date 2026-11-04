# Migration guide

The new repository was designed after inspecting these existing repositories:

- `compas-actions.build`
- `compas-actions.docs`
- `compas-actions.docversions`
- `compas-actions.ghpython_components`
- `compas-actions.publish`

It does not preserve their input surface. Migrate one workflow at a time and
keep the old repositories available until all consumers have moved.

## Build and test

Replace one `compas-actions.build` or v1 `ci` step with `setup-python` followed
by the same direct commands contributors run locally. The caller keeps the
matrix because a composite action runs on one selected runner:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: compas-dev/compas-actions/setup-python@<immutable-v2-commit>
        with:
          python-version: ${{ matrix.python }}
          dependency-groups: dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pyright
      - run: uv run pytest
```

Hybrid repositories may use the compatible Conda inputs on `setup-python`, but
their environment file, matrix, compilers, and native build steps remain visible
in the caller workflow.

Repositories that still expose stable Invoke tasks may instead keep the v2
`ci` action during migration. Its v1 inputs remain available, while uv setup is
lock-based; Invoke runs through `uv run invoke`. New workflows should prefer
the direct form above.

## Pull requests

Replace `Zomzog/changelog-checker` with `pr-checks`. The unified action checks
the pull request diff directly and supports the same skip-label policy without
requiring a GitHub token or a legacy Node action:

```yaml
- uses: compas-dev/compas-actions/pr-checks@<immutable-v2-commit>
  with:
    changelog-path: CHANGELOG.md
    skip-label: no changelog
```

## Releases

`compas-actions.publish` combined unrelated trust boundaries. Replace it with:

1. A caller-owned manual workflow that invokes `release-pr` with an explicit
   SemVer component and opens a reviewable `release/vX.Y.Z` pull request.
2. `release-check`, called from PR checks and from the `main` push workflow, to
   validate and detect the merged version change.
3. `prepare-release`, called from a read-only pure-Python job, which builds,
   installs, smoke-tests, and uploads workflow artifacts. Native callers build
   visibly and call `package` with `build: false` to verify their wheel set.
4. A caller-owned `pypa/gh-action-pypi-publish` job using OIDC.
5. `github-release`, called from a `contents: write` job only after PyPI
   succeeds.

The release PR preserves a manually written Keep a Changelog file. The merge
strategy does not affect versioning because the release is detected from the
version configuration and changelog in the merged tree, not commit messages.

Generated files are produced by a visible caller command and passed to
`release-assets`. The PyPI and GitHub release jobs download only what they need.
Existing Invoke-based generation can temporarily use `run-prebuild: true` and
`invoke-tasks`; uv execution is always `uv run invoke`.

Do not pass a PyPI token. Configure a Trusted Publisher on PyPI and make its
workflow and environment names exactly match the caller.

## Documentation

`compas-actions.docs` and `compas-actions.docversions` are replaced by the
`docs` action. Sphinx sites must migrate to MkDocs before using the new
repository.

## Grasshopper components

`compas-actions.ghpython_components` is replaced by `ghpython-components`.
Only Rhino 8 CPython components are supported. The action is self-contained for
installing the standalone `ghpython_componentizer` package and must run on
Windows after Python has been installed. The package downloads the required
Grasshopper assembly itself.

## Versioning and rollout

Use a full reviewed commit SHA during testing and after release. Once the
interfaces settle:

1. create `v2.0.0`;
2. create a readable `v2` release tag for discovery;
3. keep the immutable release commit in calling workflows with a `# v2.x.y` comment;
4. migrate a small pure-Python package first, then a package with pre-build
   assets, MkDocs, Conda, and finally Rhino components.

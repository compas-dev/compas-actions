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

Replace one `compas-actions.build` step with the `ci` action. The caller keeps
the matrix because a composite action runs on one selected runner:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: compas-dev/compas-actions/ci@main
        with:
          python-version: ${{ matrix.python }}
          invoke-tasks: lint test
          check-import: true
```

Use `setup-python` and normal `run: invoke ...` steps when a repository needs
custom steps between environment setup and its checks.

## Pull requests

Replace `Zomzog/changelog-checker` with `pr-checks`. The unified action checks
the pull request diff directly and supports the same skip-label policy without
requiring a GitHub token or a legacy Node action:

```yaml
- uses: compas-dev/compas-actions/pr-checks@main
  with:
    changelog-path: CHANGELOG.md
    skip-label: no changelog
```

## Releases

`compas-actions.publish` combined unrelated trust boundaries. Replace it with:

1. `prepare-release`, called from a read-only job, which builds and uploads
   workflow artifacts.
2. A caller-owned `pypa/gh-action-pypi-publish` job using OIDC.
3. `github-release`, called from a `contents: write` job only after PyPI
   succeeds.

Generated files belong in an `invoke pre-build` task. Pass their paths through
`release-assets`; the preparation job builds once and uploads package and extra
artifacts once each. The PyPI and GitHub release jobs download only what they
need.

Do not pass a PyPI token. Configure a Trusted Publisher on PyPI and make its
workflow and environment names exactly match the caller.

## Documentation

`compas-actions.docs` and `compas-actions.docversions` are replaced by the
`mkdocs` action. Sphinx sites must migrate to MkDocs before using the new
repository.

## Grasshopper components

`compas-actions.ghpython_components` is replaced by `ghpython-components`.
Only Rhino 8 CPython components are supported. The action is self-contained for
NuGet/Grasshopper assembly setup and must run on Windows after the Python project
dependencies have been installed.

## Versioning and rollout

Use `@main` only during the initial test period. Once the interfaces settle:

1. create `v1.0.0`;
2. maintain a movable `v1` branch or tag for low-friction consumers;
3. use readable version tags consistently in calling workflows;
4. migrate a small pure-Python package first, then a package with pre-build
   assets, MkDocs, Conda, and finally Rhino components.

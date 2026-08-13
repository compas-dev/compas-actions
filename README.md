# compas-actions

Modern, composable GitHub Actions for COMPAS projects.

This repository implements the direction proposed in
[compas-actions.build#7](https://github.com/compas-dev/compas-actions.build/issues/7):
one versioned repository with narrow actions and explicit caller-owned jobs. It
is a clean break rather than a compatibility bundle.

## Actions

| Action | Responsibility |
| --- | --- |
| `ci` | Check out, install, and test one Python/OS combination |
| `release-pr` | Bump the version and open a human-reviewed release PR |
| `release-check` | Validate release metadata in PR and post-merge workflows |
| `prepare-release` | Build distributions and upload release artifacts |
| `github-release` | Download artifacts and create a tagged GitHub release |
| `docs` | Build MkDocs or deploy a version with Mike |
| `pr-checks` | Require a changelog update or an explicit skip label |
| `setup-python` | Prepare a custom uv, pip, or Conda job |
| `package` | Build and validate distributions in a custom job |
| `ghpython-components` | Build Rhino 8 CPython Grasshopper components |

Every public entry point uses the regular action syntax:

```yaml
- uses: compas-dev/compas-actions/ci@main
```

The calling workflow owns its runner, matrix, environment, dependencies, and
permissions. This keeps the interface readable and keeps security boundaries
visible where they are enforced.

## CI example

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.11", "3.12", "3.13"]
    steps:
      - uses: compas-dev/compas-actions/ci@main
        with:
          python-version: ${{ matrix.python }}
          invoke-tasks: lint test
```

## Secure release structure

The complete example is in [examples/release.yml](examples/release.yml). It
uses four separate jobs:

1. `ci` runs with `contents: read`.
2. `prepare-release` builds once and uploads workflow artifacts with
   `contents: read`.
3. A caller-owned PyPA job publishes with `contents: read` and
   `id-token: write`.
4. `github-release` creates the release with `contents: write`.

The trusted publisher remains explicit in the caller:

```yaml
publish:
  needs: prepare
  runs-on: ubuntu-latest
  environment:
    name: pypi
    url: https://pypi.org/p/YOUR_PROJECT
  permissions:
    contents: read
    id-token: write
  steps:
    - uses: actions/download-artifact@v8.0.1
      with:
        name: python-package-distributions
        path: dist
    - uses: pypa/gh-action-pypi-publish@v1.14.2
```

Configure the matching GitHub owner, repository, workflow filename, and `pypi`
environment as a Trusted Publisher on PyPI.

## Release by pull request

`release-pr` turns an explicit `patch`, `minor`, or `major` choice into a
`release/vX.Y.Z` pull request. It updates `bump-my-version` files, rolls the
manual `Unreleased` changelog section into the release, and adds a fresh
`Unreleased` section. It never tags or publishes.

`release-check` validates that version-changing pull requests use the expected
release branch, contain matching changelog headings, and modify only files
listed by the version configuration. After merge, it exposes the version and
tag to the caller-owned trusted-publishing workflow. This flow reads repository
state rather than commit messages, so merge, squash, and rebase strategies are
all supported.

Use a GitHub App installation token for `release-pr` when automated pull
requests should run required checks without manual workflow approval.

## Versions

`@main` is useful while bootstrapping this repository. Consumers should move to
the readable `@v1` release tag after the first release.

## Deliberate exclusions

- IronPython and Rhino 7 component generation
- Sphinx and the old `docversions` site mutation action
- PyPI API-token uploads
- compatibility inputs from the old monolithic actions
- hidden publishing or permission escalation

Documentation uses MkDocs and Mike. Grasshopper generation targets Rhino 8
CPython and CoreCLR only.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design and
[MIGRATION.md](MIGRATION.md) for the old-to-new mapping.

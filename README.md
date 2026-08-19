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
| `release-assets` | Run an Invoke task and upload what it produces as release assets |
| `github-release` | Download artifacts and create a tagged GitHub release |
| `docs` | Build MkDocs or deploy a version with Mike |
| `pr-checks` | Require a changelog update or an explicit skip label |
| `setup-python` | Prepare a custom uv or Conda job |
| `package` | Build and validate distributions in a custom job |
| `ghpython-components` | Build Rhino 8 CPython components with `ghpython_componentizer` |

Every public entry point uses the regular action syntax:

```yaml
- uses: compas-dev/compas-actions/ci@v1
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
      - uses: compas-dev/compas-actions/ci@v1
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

A package that ships more than its distributions -- generated protobuf
bindings, schema bundles, compiled assets -- adds a `release-assets` job
alongside `prepare-release`. Both upload to the same artifact name, so
`github-release` attaches whatever is there:

```yaml
assets:
  needs: release
  runs-on: ubuntu-latest
  steps:
    - uses: compas-dev/compas-actions/release-assets@v1
      with:
        invoke-tasks: create-class-assets
        paths: dist/proto/*.zip
```

Use it instead of `prepare-release`'s `release-assets` input when the build is
slow or needs tools the wheel build does not, since that input ties asset
generation to `invoke pre-build` on every matrix job.

When a release collects assets from more than one job, have each upload under
its own name and let `github-release` gather them:

```yaml
- uses: compas-dev/compas-actions/github-release@v1
  with:
    release-assets-artifact-pattern: github-release-assets-*
```

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

The minimal setup uses `github.token`; a maintainer then approves the generated
pull request's workflow runs. Repositories that later need unattended checks
can instead pass a GitHub App installation token.

## Versions

`@main` is useful while bootstrapping this repository. Consumers should move to
the readable `@v1` release tag after the first release.

## Releasing

Run the `release` workflow from the Actions tab and pick `patch`, `minor` or
`major`. It works out the next version from the existing tags, creates the
annotated point tag, moves the major tag consumers pin to, and publishes a
GitHub release with generated notes.

Releases run from the default branch only. A major release creates a new major
tag and leaves the previous one where it is, so callers on the old one keep
working until they choose to move.

## Deliberate exclusions

- IronPython and Rhino 7 component generation
- Sphinx and the old `docversions` site mutation action
- PyPI API-token uploads
- compatibility inputs from the old monolithic actions
- hidden publishing or permission escalation

Documentation uses MkDocs and Mike. Grasshopper generation targets Rhino 8
CPython only and delegates component generation to
[`ghpython_componentizer`](https://github.com/compas-dev/ghpython_componentizer).

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design and
[MIGRATION.md](MIGRATION.md) for the old-to-new mapping.

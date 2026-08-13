# Architecture

## Inventory

The previous repositories mix orchestration, tooling, and permissions:

| Repository | Responsibilities found | New home |
| --- | --- | --- |
| `compas-actions.build` | checkout, environment setup, pre-build, lint, test, import checks, Grasshopper | `ci`, `setup-python`, `ghpython-components` |
| `compas-actions.publish` | changelog, release, Grasshopper, package build, token upload | `prepare-release`, caller-owned OIDC publish, `github-release` |
| `compas-actions.docs` | environment setup, Sphinx/MkDocs build and deployment | `docs` |
| `compas-actions.docversions` | mutate a Sphinx-style `gh-pages` tree | intentionally retired |
| `compas-actions.ghpython_components` | IronPython/CPython component generation | Rhino 8 CPython-only `ghpython-components`, backed by the standalone `ghpython_componentizer` package |

Representative consumers include pure-Python matrices, OS-specific Conda
environments, `cibuildwheel` packages, generated protobuf archives, and Windows
Grasshopper builds.

## Public interface

Every public automation is a composite action in a named directory:

```text
compas-actions/ci@v1
compas-actions/prepare-release@v1
compas-actions/github-release@v1
compas-actions/docs@v1
compas-actions/pr-checks@v1
compas-actions/release-pr@v1
compas-actions/release-check@v1
```

Callers define job structure. In particular, callers own `runs-on`, matrix
expansion, `needs`, environments, and permissions. The small amount of repeated
job scaffolding is the cost of a clean action API and makes trust boundaries
directly reviewable in each repository.

There are no public reusable workflows and no generic shell-command action.

## Release data flow

```text
workflow_dispatch
  -> release-pr (contents: write, pull-requests: write; no publishing identity)
       -> reviewed release/vX.Y.Z pull request
            -> merge to main
                 -> release-check

CI job (contents: read)
  -> prepare job (contents: read)
       -> python-package-distributions artifact
       -> optional github-release-assets artifact
            -> PyPI job (contents: read, id-token: write)
            -> GitHub release job (contents: write)
```

The package build happens once. The PyPI publisher is deliberately not wrapped:
its workflow filename, environment, and OIDC subject are part of the PyPI trust
policy and must remain caller-owned.

## Versioning

All actions share one repository version. Breaking changes require a new major
version. A movable major tag (`v1`) is the shared, readable consumer interface.

## Modern-only boundary

The first major version targets supported GitHub-hosted runners, current action
runtimes, uv/pip, optional Conda for native packages, PyPI Trusted Publishing,
MkDocs/Mike, and Rhino 8 CPython. It contains no compatibility wrapper,
IronPython implementation, Sphinx implementation, or API-token publisher.

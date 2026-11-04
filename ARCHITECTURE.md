# Architecture

## Inventory

The previous repositories mix orchestration, tooling, and permissions:

| Repository | Responsibilities found | New home |
| --- | --- | --- |
| `compas-actions.build` | checkout, environment setup, pre-build, lint, test, import checks, Grasshopper | `ci` or `setup-python` plus visible caller commands, `ghpython-components` |
| `compas-actions.publish` | changelog, release, Grasshopper, package build, token upload | `prepare-release`, caller-owned OIDC publish, `github-release` |
| `compas-actions.docs` | environment setup, Sphinx/MkDocs build and deployment | `docs` |
| `compas-actions.docversions` | mutate a Sphinx-style `gh-pages` tree | intentionally retired |
| `compas-actions.ghpython_components` | IronPython/CPython component generation | Rhino 8 CPython-only `ghpython-components`, backed by the standalone `ghpython_componentizer` package |

Representative consumers include pure-Python matrices, OS-specific Conda
environments, `cibuildwheel` packages, generated protobuf archives, and Windows
Grasshopper builds.

`ci` and `setup-python` retain bounded Conda environment-file provisioning as a
compatibility and convenience path. This does not move native policy into the
actions: new hybrid/native workflows keep their environment files, matrices,
system packages, compilers, and build commands visible in caller YAML.

## Public interface

Every public automation is a composite action in a named directory:

```text
compas-actions/setup-python@<immutable-v2-commit>
compas-actions/ci@<immutable-v2-commit>
compas-actions/prepare-release@<immutable-v2-commit>
compas-actions/release-assets@<immutable-v2-commit>
compas-actions/github-release@<immutable-v2-commit>
compas-actions/docs@<immutable-v2-commit>
compas-actions/pr-checks@<immutable-v2-commit>
compas-actions/release-pr@<immutable-v2-commit>
compas-actions/release-check@<immutable-v2-commit>
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
version. Consumers pin a reviewed immutable commit and add a readable version
comment. Release tags aid discovery but are not the execution trust boundary.

## Modern-only boundary

The second major version targets supported GitHub-hosted runners, current action
runtimes, locked uv projects, optional bounded Conda setup, caller-owned native provisioning, PyPI Trusted Publishing,
MkDocs/Mike, and Rhino 8 CPython. It contains no compatibility wrapper,
IronPython implementation, Sphinx implementation, or API-token publisher.

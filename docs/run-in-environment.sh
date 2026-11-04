#!/usr/bin/env bash
set -euo pipefail

environment_name="$1"
shift
if [[ "${1:-}" != "--" ]]; then
  echo "expected -- before the command" >&2
  exit 2
fi
shift

if [[ -n "$environment_name" ]]; then
  if [[ ! "$environment_name" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "invalid Conda environment name: $environment_name" >&2
    exit 2
  fi
  exec conda run --no-capture-output -n "$environment_name" "$@"
fi

exec "$@"

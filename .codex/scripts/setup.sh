#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "${script_dir}/../.." && pwd -P)"
market_snapshot_dir="${repo_root}/market-snapshot"
frontend_dir="${repo_root}/web-ui"

missing_tools=()
for tool in python3.13 poetry node npm; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        missing_tools+=("${tool}")
    fi
done

if ((${#missing_tools[@]} > 0)); then
    printf 'error: missing machine-level prerequisite(s) in the Bash environment: %s\n' \
        "${missing_tools[*]}" >&2
    printf 'Install them outside this setup script and ensure they are available on PATH.\n' >&2
    exit 1
fi

python313="$(command -v python3.13)"
if ! python_version="$("${python313}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"; then
    printf 'error: python3.13 was found at %s but could not be executed.\n' "${python313}" >&2
    exit 1
fi
if [[ "${python_version}" != "3.13" ]]; then
    printf 'error: python3.13 must provide Python 3.13; found %s.\n' "${python_version}" >&2
    exit 1
fi

required_files=(
    "${repo_root}/pyproject.toml"
    "${repo_root}/poetry.lock"
    "${repo_root}/poetry.toml"
    "${market_snapshot_dir}/.env.example"
    "${frontend_dir}/package.json"
    "${frontend_dir}/package-lock.json"
)
for required_file in "${required_files[@]}"; do
    if [[ ! -f "${required_file}" ]]; then
        printf 'error: required repository file is missing: %s\n' "${required_file}" >&2
        exit 1
    fi
done

if [[ ! -e "${market_snapshot_dir}/.env" ]]; then
    cp -- "${market_snapshot_dir}/.env.example" "${market_snapshot_dir}/.env"
    printf 'Created market-snapshot/.env from .env.example.\n'
else
    printf 'Using existing market-snapshot/.env.\n'
fi

printf 'Installing repository Python dependencies into .venv...\n'
(
    cd -- "${repo_root}"
    POETRY_VIRTUALENVS_IN_PROJECT=true poetry env use "${python313}"
    POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --sync --no-interaction
)

poetry_env_path="$({
    cd -- "${repo_root}"
    POETRY_VIRTUALENVS_IN_PROJECT=true poetry env info --path
})"
if [[ "${poetry_env_path}" = /* ]]; then
    poetry_env_candidate="${poetry_env_path}"
else
    poetry_env_candidate="${repo_root}/${poetry_env_path}"
fi
if [[ ! -d "${poetry_env_candidate}" ]]; then
    printf 'error: Poetry reported an environment that does not exist: %s\n' \
        "${poetry_env_candidate}" >&2
    exit 1
fi
if [[ ! -d "${repo_root}/.venv" ]]; then
    printf 'error: Poetry did not create the required worktree-local environment: %s\n' \
        "${repo_root}/.venv" >&2
    exit 1
fi

poetry_env_resolved="$(cd -- "${poetry_env_candidate}" && pwd -P)"
expected_venv_resolved="$(cd -- "${repo_root}/.venv" && pwd -P)"
if [[ "${poetry_env_resolved}" != "${expected_venv_resolved}" ]]; then
    printf 'error: Poetry environment is not worktree-local.\n' >&2
    printf 'expected: %s\nactual:   %s\n' \
        "${expected_venv_resolved}" "${poetry_env_resolved}" >&2
    exit 1
fi

printf 'Installing frontend dependencies into web-ui/node_modules...\n'
(
    cd -- "${frontend_dir}"
    npm ci
)

printf 'Verifying development environment readiness...\n'
cd -- "${repo_root}"
poetry run python dev.py doctor

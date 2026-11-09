#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "${script_dir}/.." && pwd -P)"
runtime_dir="${repo_root}/ui_http/data/one-click"
state_file="${runtime_dir}/linux-launcher.state"
url='http://127.0.0.1:5173/'

action="${1:-start}"
if [[ $# -gt 1 ]]; then
    printf 'Usage: bash scripts/market-lab.sh [start|status|stop]\n' >&2
    exit 2
fi
case "${action}" in
    start|stop|status) ;;
    *) printf 'Usage: bash scripts/market-lab.sh [start|status|stop]\n' >&2; exit 2 ;;
esac

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

process_start_time() {
    local pid="$1"
    [[ -r "/proc/${pid}/stat" ]] || return 1
    awk '{print $22}' "/proc/${pid}/stat"
}

same_process() {
    local pid="$1" expected="$2" actual
    [[ "${pid}" =~ ^[1-9][0-9]*$ && "${expected}" =~ ^[1-9][0-9]*$ ]] || return 1
    actual="$(process_start_time "${pid}" 2>/dev/null)" || return 1
    [[ "${actual}" == "${expected}" ]]
}

read_state() {
    [[ -f "${state_file}" ]] || return 1
    read -r owner_pid owner_start backend_pid backend_start frontend_pid frontend_start < "${state_file}" || return 1
    same_process "${owner_pid}" "${owner_start}"
}

port_listening() {
    [[ -n "$(ss -H -ltn "sport = :$1")" ]]
}

port_owned_by_group() {
    local port="$1" group="$2" line pid actual_group
    while IFS= read -r line; do
        while [[ "${line}" =~ pid=([0-9]+) ]]; do
            pid="${BASH_REMATCH[1]}"
            line="${line#*pid=${pid}}"
            actual_group="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ')"
            [[ "${actual_group}" == "${group}" ]] && return 0
        done
    done < <(ss -H -ltnp "sport = :${port}")
    return 1
}

status() {
    if read_state; then
        printf 'Market Lab launcher running (PID %s).\n' "${owner_pid}"
        for service in backend frontend; do
            local pid_var="${service}_pid" start_var="${service}_start" port
            [[ "${service}" == backend ]] && port=8011 || port=5173
            if same_process "${!pid_var}" "${!start_var}" && port_owned_by_group "${port}" "${!pid_var}"; then
                printf '%s: ready on 127.0.0.1:%s\n' "${service}" "${port}"
            elif same_process "${!pid_var}" "${!start_var}"; then
                printf '%s: starting (PID %s)\n' "${service}" "${!pid_var}"
            elif [[ "${!pid_var}" == 0 ]]; then
                printf '%s: pending startup\n' "${service}"
            else
                printf '%s: stopped\n' "${service}"
            fi
        done
        return 0
    fi
    if [[ -f "${state_file}" ]]; then
        printf 'Market Lab launcher is not running (stale state file).\n'
    else
        printf 'Market Lab launcher is not running.\n'
    fi
    for port in 8011 5173; do
        if port_listening "${port}"; then
            printf 'Port %s is occupied by another or unverified process.\n' "${port}"
        fi
    done
}

stop() {
    if ! read_state; then
        status
        return 0
    fi
    printf 'Stopping Market Lab launcher (PID %s)...\n' "${owner_pid}"
    kill -TERM "${owner_pid}" 2>/dev/null || fail 'Could not signal the launcher.'
    local attempt
    for ((attempt = 0; attempt < 100; attempt++)); do
        if ! same_process "${owner_pid}" "${owner_start}"; then
            printf 'Market Lab services stopped.\n'
            return 0
        fi
        sleep 0.1
    done
    fail 'Launcher did not stop within 10 seconds; inspect its logs and process state.'
}

check_prerequisites() {
    local tool version
    for tool in python3.13 poetry node npm ss ps setsid flock curl awk tr; do
        command -v "${tool}" >/dev/null 2>&1 || fail "Environment missing: ${tool} is not available on PATH."
    done
    version="$(python3.13 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" || fail 'Python 3.13 could not be executed.'
    [[ "${version}" == '3.13' ]] || fail "Python 3.13 is required; found ${version}."
    poetry --version >/dev/null || fail 'Poetry could not be executed.'
    npm --version >/dev/null || fail 'npm could not be executed.'
    node -e 'const [major, minor] = process.versions.node.split(".").map(Number); process.exit((major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major > 22 ? 0 : 1)' \
        || fail 'Node.js must be 20.19+ or 22.12+.'
}

assert_free_ports() {
    local port
    for port in 8011 5173; do
        port_listening "${port}" && fail "Port ${port} is occupied; the other program was not terminated."
    done
    return 0
}

environment_ready() {
    [[ -x "${repo_root}/.venv/bin/python" && -d "${repo_root}/ui_web/node_modules" ]] || return 1
    poetry run python -c 'import sys, fastapi, uvicorn, jwt, argon2; assert sys.version_info[:2] == (3, 13)' >/dev/null 2>&1 || return 1
    poetry run lab --help >/dev/null 2>&1 || return 1
    (cd -- "${repo_root}/ui_web" && npm ls --depth=0 >/dev/null 2>&1)
}

ensure_environment() {
    export POETRY_VIRTUALENVS_IN_PROJECT=true
    if ! environment_ready; then
        printf 'Project dependencies missing or incomplete; running existing Linux bootstrap...\n'
        bash "${repo_root}/.codex/scripts/setup.sh" || fail 'Project dependency installation failed.'
    fi
    local poetry_env
    poetry_env="$(poetry env info --path)" || fail 'Could not inspect the Poetry environment.'
    [[ -d "${poetry_env}" && "$(cd -- "${poetry_env}" && pwd -P)" == "$(cd -- "${repo_root}/.venv" && pwd -P)" ]] \
        || fail 'Poetry must use the repository root .venv.'
}

has_local_setting() {
    [[ -f "${repo_root}/.env" ]] || return 1
    grep -Eq "^[[:space:]]*(export[[:space:]]+)?$1[[:space:]]*=" "${repo_root}/.env"
}

configure_auth() {
    if [[ ! ${LAB_AUTH_MODE+x} ]] && ! has_local_setting LAB_AUTH_MODE; then
        export LAB_AUTH_MODE='loopback-http'
    fi
    if [[ ! ${LAB_AUTH_ORIGIN+x} ]] && ! has_local_setting LAB_AUTH_ORIGIN; then
        export LAB_AUTH_ORIGIN='http://127.0.0.1:5173'
    fi
    if [[ ! ${LAB_AUTH_JWT_SECRET+x} ]] && ! has_local_setting LAB_AUTH_JWT_SECRET; then
        local secret_file="${runtime_dir}/jwt-secret"
        if [[ ! -f "${secret_file}" ]]; then
            (umask 077; set -C; python3.13 -c 'import secrets; print(secrets.token_urlsafe(32))' > "${secret_file}") \
                || [[ -f "${secret_file}" ]] || fail 'Could not create local JWT secret.'
        fi
        [[ -r "${secret_file}" ]] || fail 'Local JWT secret is not readable.'
        export LAB_AUTH_JWT_SECRET="$(<"${secret_file}")"
    fi
    poetry run python -c 'from ui_http.auth._session import AuthConfig; c = AuthConfig.from_environment(); c.validate_listener("127.0.0.1"); assert not c.secure and c.browser_origin == ("http", "127.0.0.1", 5173)' >/dev/null 2>&1 \
        || fail 'Auth configuration is invalid for local HTTP; existing settings were not changed.'
}

write_state() {
    local temp_file="${state_file}.$$"
    printf '%s %s %s %s %s %s\n' "$$" "${owner_start}" "${backend_pid}" "${backend_start}" "${frontend_pid}" "${frontend_start}" > "${temp_file}"
    mv -f -- "${temp_file}" "${state_file}"
}

stop_group() {
    local pid="$1" start="$2" attempt
    same_process "${pid}" "${start}" || return 0
    kill -TERM -- "-${pid}" 2>/dev/null || true
    for ((attempt = 0; attempt < 30; attempt++)); do
        same_process "${pid}" "${start}" || return 0
        sleep 0.1
    done
    if same_process "${pid}" "${start}"; then
        kill -KILL -- "-${pid}" 2>/dev/null || true
    fi
}

cleanup() {
    local exit_code=$?
    trap - EXIT INT TERM
    stop_group "${frontend_pid:-0}" "${frontend_start:-0}"
    stop_group "${backend_pid:-0}" "${backend_start:-0}"
    if [[ -f "${state_file}" ]]; then
        local recorded_pid recorded_start _rest
        read -r recorded_pid recorded_start _rest < "${state_file}" || true
        if [[ "${recorded_pid:-}" == "$$" && "${recorded_start:-}" == "${owner_start:-}" ]]; then
            rm -f -- "${state_file}"
        fi
    fi
    exit "${exit_code}"
}

start_service() {
    local service="$1" log_file="${runtime_dir}/${run_id}-$1.log"
    setsid bash -c 'exec poetry run lab serve "$1"' _ "${service}" 9>&- > "${log_file}" 2>&1 &
    local pid=$!
    local start_time
    start_time="$(process_start_time "${pid}")" || fail "${service} exited before startup; see ${log_file}."
    if [[ "${service}" == backend ]]; then
        backend_pid="${pid}"; backend_start="${start_time}"
    else
        frontend_pid="${pid}"; frontend_start="${start_time}"
    fi
    write_state
}

http_ready() {
    local endpoint="$1" expected="$2" code
    code="$(curl --noproxy '*' --silent --max-time 2 --output /dev/null --write-out '%{http_code}' "${endpoint}" 2>/dev/null)" || return 1
    [[ "${code}" == "${expected}" ]]
}

start() {
    cd -- "${repo_root}"
    umask 077
    mkdir -p -- "${runtime_dir}"
    exec 9>"${runtime_dir}/linux-launcher.lock"
    flock -n 9 || fail 'A Market Lab Linux launcher is already running.'
    owner_start="$(process_start_time "$$")"
    backend_pid=0 backend_start=0 frontend_pid=0 frontend_start=0
    trap cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    write_state

    printf 'Checking Linux development prerequisites...\n'
    check_prerequisites
    assert_free_ports
    ensure_environment
    configure_auth
    printf 'Checking backend imports...\n'
    poetry run python -c 'import ui_http.app' || fail 'Backend import preflight failed.'
    assert_free_ports

    run_id="$(date +%Y%m%d-%H%M%S)-$$"
    printf 'Starting services. Logs: %s\n' "${runtime_dir}"
    start_service backend
    start_service frontend

    local deadline=$((SECONDS + 90))
    while ((SECONDS < deadline)); do
        same_process "${backend_pid}" "${backend_start}" || fail "Backend exited during startup; see ${runtime_dir}/${run_id}-backend.log."
        same_process "${frontend_pid}" "${frontend_start}" || fail "Frontend exited during startup; see ${runtime_dir}/${run_id}-frontend.log."
        if port_owned_by_group 8011 "${backend_pid}" && port_owned_by_group 5173 "${frontend_pid}" \
            && http_ready 'http://127.0.0.1:8011/openapi.json' 401 && http_ready "${url}" 200; then
            printf 'Both services are ready: %s\n' "${url}"
            printf 'Keep this terminal open. Press Ctrl+C to stop, or run bash scripts/market-lab.sh stop elsewhere.\n'
            while :; do
                same_process "${backend_pid}" "${backend_start}" || fail "Backend exited; see ${runtime_dir}/${run_id}-backend.log."
                same_process "${frontend_pid}" "${frontend_start}" || fail "Frontend exited; see ${runtime_dir}/${run_id}-frontend.log."
                sleep 0.5
            done
        fi
        sleep 0.5
    done
    fail "Service startup timed out after 90 seconds; see logs in ${runtime_dir}."
}

case "${action}" in
    start) start ;;
    status) status ;;
    stop) stop ;;
esac

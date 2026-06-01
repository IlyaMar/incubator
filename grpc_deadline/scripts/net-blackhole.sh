#!/usr/bin/env bash
# macOS packet-filter blackhole: silently drop TCP on given ports (no RST/ICMP).
# Requires sudo.
#
# Loads rules into the *main* pf ruleset (not an orphan anchor).
# For --loopback, skips all non-lo0 interfaces so only localhost is affected.
#
# Usage:
#   sudo ./scripts/net-blackhole.sh on 50051
#   sudo ./scripts/net-blackhole.sh on --loopback 50051
#   sudo ./scripts/net-blackhole.sh off
#   sudo ./scripts/net-blackhole.sh status

set -euo pipefail

STATE_DIR="/tmp/com.incubator.grpc_deadline"
PF_FILE="${STATE_DIR}/rules.pf"
STATE_FILE="${STATE_DIR}/state"
SYSTEM_PF="/etc/pf.conf"

usage() {
	cat <<'EOF'
Usage:
  net-blackhole.sh on  [--loopback] <port> [port...]
  net-blackhole.sh off
  net-blackhole.sh status

Options:
  --loopback   Drop only on lo0 (typical for localhost gRPC tests).

Examples:
  sudo ./scripts/net-blackhole.sh on 50051
  sudo ./scripts/net-blackhole.sh on --loopback 50051
  sudo ./scripts/net-blackhole.sh off
EOF
}

require_root() {
	if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
		echo "error: run with sudo (pfctl needs root)" >&2
		exit 1
	fi
}

validate_port() {
	local p="$1"
	if [[ ! "$p" =~ ^[0-9]+$ ]] || (( p < 1 || p > 65535 )); then
		echo "error: invalid port: $p" >&2
		exit 1
	fi
}

pf_enabled() {
	pfctl -s info 2>/dev/null | grep -q "Status: Enabled"
}

skip_all_except_lo0() {
	local iface skip=()
	for iface in $(ifconfig -l); do
		[[ "$iface" == "lo0" ]] && continue
		skip+=("$iface")
	done
	if [[ ${#skip[@]} -gt 0 ]]; then
		# macOS has no "set skip off"; omit lo0 from the skip list instead.
		printf 'set skip on { %s }\n' "${skip[*]}"
	fi
}

write_rules() {
	local loopback_only="$1"
	shift
	local ports=("$@")

	mkdir -p "$STATE_DIR"
	: >"$PF_FILE"

	if [[ "$loopback_only" == "1" ]]; then
		skip_all_except_lo0 >>"$PF_FILE"
	fi

	for port in "${ports[@]}"; do
		validate_port "$port"
		if [[ "$loopback_only" == "1" ]]; then
			cat >>"$PF_FILE" <<EOF
block drop quick on lo0 proto tcp from any to any port $port
block drop quick on lo0 proto tcp from any port $port to any
EOF
		else
			cat >>"$PF_FILE" <<EOF
block drop quick proto tcp from any to any port $port
block drop quick proto tcp from any port $port to any
block drop quick on lo0 proto tcp from any to any port $port
block drop quick on lo0 proto tcp from any port $port to any
EOF
		fi
	done

	echo "pass" >>"$PF_FILE"
}

pf_load_rules() {
	local out rc
	out=$(pfctl -f "$PF_FILE" 2>&1) || rc=$?
	rc=${rc:-0}
	printf '%s\n' "$out" | grep -v '^No ALTQ' | grep -v '^ALTQ related' || true
	return "$rc"
}

save_state() {
	local loopback_only="$1"
	shift
	local ports=("$@")

	mkdir -p "$STATE_DIR"
	{
		echo "ports=${ports[*]}"
		echo "loopback_only=$loopback_only"
		if pf_enabled; then
			echo "pf_was_enabled=1"
		else
			echo "pf_was_enabled=0"
		fi
	} >"$STATE_FILE"
}

cmd_on() {
	local loopback_only=0
	local ports=()

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--loopback)
			loopback_only=1
			shift
			;;
		-h | --help)
			usage
			exit 0
			;;
		-*)
			echo "error: unknown option: $1" >&2
			usage >&2
			exit 1
			;;
		*)
			ports+=("$1")
			shift
			;;
		esac
	done

	if [[ ${#ports[@]} -eq 0 ]]; then
		echo "error: specify at least one port" >&2
		usage >&2
		exit 1
	fi

	if [[ -f "$STATE_FILE" ]]; then
		echo "error: blackhole already active; run 'off' first" >&2
		exit 1
	fi

	write_rules "$loopback_only" "${ports[@]}"

	if ! pf_load_rules; then
		rm -rf "$STATE_DIR"
		echo "error: pfctl failed to load rules (see $PF_FILE)" >&2
		exit 1
	fi

	pfctl -e 2>/dev/null | grep -v '^No ALTQ' | grep -v '^ALTQ related' || true

	save_state "$loopback_only" "${ports[@]}"

	echo "blackhole ON, ports: ${ports[*]}"
	if [[ "$loopback_only" == "1" ]]; then
		echo "scope: lo0 only (other interfaces in pf skip list)"
	else
		echo "scope: all interfaces"
	fi
	echo
	echo "active rules:"
	pfctl -sr 2>/dev/null | grep -v '^No ALTQ' || true
	echo
	echo "skip interfaces:"
	pfctl -s skip 2>/dev/null | grep -v '^No ALTQ' || echo "(none)"
}

cmd_off() {
	if [[ ! -f "$STATE_FILE" ]]; then
		echo "blackhole already off"
		rm -rf "$STATE_DIR"
		return 0
	fi

	# shellcheck disable=SC1090
	source "$STATE_FILE"

	pfctl -f "$SYSTEM_PF" 2>&1 | grep -v '^No ALTQ' || true

	if [[ "${pf_was_enabled:-0}" != "1" ]]; then
		pfctl -d 2>/dev/null | grep -v '^No ALTQ' || true
	fi

	rm -rf "$STATE_DIR"
	echo "blackhole OFF (restored $SYSTEM_PF)"
}

cmd_status() {
	echo "pf info:"
	pfctl -s info 2>/dev/null | grep -v '^No ALTQ' | head -5 || true
	echo
	echo "skip interfaces (lo0 listed => localhost bypasses pf):"
	pfctl -s skip 2>/dev/null | grep -v '^No ALTQ' || echo "(none)"
	echo
	echo "main rules:"
	if pfctl -sr 2>/dev/null | grep -v '^No ALTQ' | grep -q .; then
		pfctl -sr 2>/dev/null | grep -v '^No ALTQ'
	else
		echo "(none)"
	fi
	echo
	if [[ -f "$STATE_FILE" ]]; then
		echo "blackhole state:"
		cat "$STATE_FILE"
		echo
		echo "rules file ($PF_FILE):"
		cat "$PF_FILE"
	else
		echo "blackhole: off"
	fi
}

main() {
	local cmd="${1:-}"
	shift || true

	case "$cmd" in
	on)
		require_root
		cmd_on "$@"
		;;
	off)
		require_root
		cmd_off
		;;
	status)
		require_root
		cmd_status
		;;
	"" | -h | --help | help)
		usage
		;;
	*)
		echo "error: unknown command: $cmd" >&2
		usage >&2
		exit 1
		;;
	esac
}

main "$@"

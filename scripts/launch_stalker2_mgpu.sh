#!/usr/bin/env bash
# GAME PCI is an assertion about the existing game configuration, not a selector.
# The bridge discovers the actual game adapter from its swapchain after launch.
set -euo pipefail
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
usage() {
    echo "Usage: $0 --game-pci DOMAIN:BUS:DEVICE.FUNCTION [--dry-run]"
    echo 'Supply the verified GAME/RENDER PCI address; NVIDIA indices are not accepted.'
    echo 'Keep Steam game Launch Options: PROTON_LOG=1 %command%'
}
normalize() {
    local pci=${1,,}
    [[ $pci =~ ^(0000|00000000):[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$ ]] ||
        die "Invalid PCI address: $1 (expected domain 0000)"
    printf '00000000:%s' "${pci#*:}"
}
game=''
dry_run=false
while (($#)); do
    case $1 in
        --game-pci)
            (($# >= 2)) || die '--game-pci needs an address'
            game=$(normalize "$2"); shift 2 ;;
        --dry-run) dry_run=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die "Unknown argument: $1" ;;
    esac
done
[[ -n $game ]] || { usage >&2; die 'GAME PCI is required; refusing to guess'; }
((EUID != 0)) || die 'Run as your desktop user; only power-limit operations may use sudo'
for cmd in nvidia-smi flatpak; do
    command -v "$cmd" >/dev/null || die "Missing command: $cmd"
done
smi=$(command -v nvidia-smi)
flatpak info com.valvesoftware.Steam >/dev/null || die 'Flatpak Steam is unavailable'
game_dir='/mnt/ssd/steam/steamapps/common/S.T.A.L.K.E.R. 2 Heart of Chornobyl'
[[ -d $game_dir ]] || die "Game directory missing: $game_dir"
neural=00000000:0c:00.0
present=00000000:43:00.0
[[ $game != "$neural" ]] || die 'GAME cannot equal NEURAL: the bridge rejects this topology'
inventory=$("$smi" --query-gpu=index,pci.bus_id,name,power.limit --format=csv,noheader) ||
    die 'NVIDIA GPU inventory failed'
declare -A indices names counts
while IFS=, read -r index pci name _limit; do
    # Trim CSV whitespace, preserving spaces within GPU names.
    index=${index//[[:space:]]/}
    pci=${pci//[[:space:]]/}
    [[ -n $pci ]] || continue
    pci=$(normalize "$pci")
    [[ $index =~ ^[0-9]+$ ]] || die 'Invalid NVIDIA inventory index'
    counts[$pci]=$(( ${counts[$pci]:-0} + 1 ))
    indices[$pci]=$index
    names[$pci]=${name# }
done <<< "$inventory"
declare -A seen
participants=()
for pci in "$game" "$neural" "$present"; do
    [[ ${counts[$pci]:-0} == 1 ]] || die "PCI $pci must resolve to exactly one NVIDIA GPU"
    [[ ${names[$pci]} == *'RTX 3090'* ]] || die "Unexpected GPU at $pci: ${names[$pci]}"
    if [[ ! ${seen[$pci]:-} ]]; then
        participants+=("$pci"); seen[$pci]=1
    fi
done
printf 'GAME GPU    : PCI %s / index %s (caller-confirmed)\n' "$game" "${indices[$game]}"
printf 'NEURAL GPU  : PCI %s / index %s\n' "$neural" "${indices[$neural]}"
printf 'PRESENT GPU : PCI %s / index %s\n' "$present" "${indices[$present]}"
printf 'TARGET      : ASUS (existing display configuration)\nPOWER LIMIT : 350 W\n'
echo 'Steam Launch Options must retain PROTON_LOG=1 %command%, including when Steam is already running.'
if $dry_run; then
    printf 'Would set 350 W on PCI %s\n' "${participants[@]}"
    echo 'Would request Flatpak Steam launch of AppID 1643320. No changes made.'
    exit 0
fi
for pci in "${participants[@]}"; do
    # NVIDIA exit code 4 means insufficient permissions; do not elevate other failures.
    if "$smi" -i "$pci" -pl 350; then
        :
    else
        rc=$?
        [[ $rc == 4 ]] || die "Power-limit operation failed for $pci (exit $rc); not launching"
        command -v sudo >/dev/null || die 'sudo is required for the power-limit operation'
        sudo -- "$smi" -i "$pci" -pl 350 || die "Power-limit operation failed for $pci; not launching"
    fi
    actual=$("$smi" -i "$pci" --query-gpu=power.limit --format=csv,noheader,nounits) ||
        die "Cannot verify power limit for $pci"
    actual=${actual//[[:space:]]/}
    [[ $actual =~ ^350(\.0+)?$ ]] || die "Unexpected power limit for $pci: $actual; not launching"
done
"$smi" --query-gpu=index,pci.bus_id,name,power.limit,power.max_limit --format=csv ||
    die 'Final GPU report failed; not launching'
# Existing per-game Launch Options remain authoritative for an already running Steam.
# No shader processing, cache changes, bridge controls, or automatic power reset.
exec flatpak run --env=PROTON_LOG=1 com.valvesoftware.Steam -applaunch 1643320

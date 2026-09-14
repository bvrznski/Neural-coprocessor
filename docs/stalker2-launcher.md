# Controlled STALKER 2 launcher

Run `scripts/launch_stalker2_mgpu.sh --game-pci <verified-render-PCI>` from
your desktop account. Add `--dry-run` to inspect the mapping without changing
power or starting Steam. Four-digit and eight-digit zero domains are accepted.

The GAME argument asserts the physical GPU used by the existing configuration;
it does not select or force a render device. Confirm it against the current
game adapter configuration before using the launcher. The bridge's authoritative
game identity comes from the swapchain at runtime (`src/adapter.cpp`), so the
launcher cannot discover it reliably before game launch. No NVIDIA numeric
index, identical model name, or old log is used to guess it. GAME must differ
from NEURAL, matching the bridge's safety gate.

NEURAL is PCI `0000:0C:00.0`; PRESENT is PCI `0000:43:00.0`, with the existing
ASUS display configuration. All participating PCI identities must resolve
uniquely to RTX 3090s. The launcher deduplicates these identities, sets only
their power limits to 350 W, verifies readback, and prints the final GPU table.
Only an NVIDIA permission error triggers sudo, for that power-limit command.
If a later operation fails, already applied limits remain; there is no rollback.

Steam must retain the per-game Launch Options `PROTON_LOG=1 %command%`.
These were verified in the installed Flatpak Steam configuration on 2026-09-14.
The launcher additionally passes `--env=PROTON_LOG=1` to Flatpak for a newly
started Steam process; environment changes cannot update an existing Steam
process. It preserves existing launch options and requests AppID 1643320 through
`com.valvesoftware.Steam`. Steam launch-request success does not prove that the
game started or the MGPU pipeline works.

The launcher does not request shader precompilation. Continue using Steam's
existing skip workflow if Steam itself offers shader processing. No shader
caches, prefix, display settings, driver settings other than power limits,
bridge configuration, or hotkeys are modified.

## Validation, 2026-09-14

- `bash -n scripts/launch_stalker2_mgpu.sh`: passed.
- `shellcheck scripts/launch_stalker2_mgpu.sh`: passed, no diagnostics.
- Temporary Python harness with mocked NVIDIA, sudo and Flatpak commands:
  12 executed, 12 passed, 0 failed. Cases: two-GPU deduplication, third render
  GPU inclusion, duplicate PCI, missing PCI, inventory failure, power failure,
  readback mismatch, sudo success, sudo failure, dry run, GAME equals NEURAL,
  and missing GAME argument. Indices were deliberately reordered. Checks
  confirmed unrelated PCI 44 was never modified and failures never launched.
- Read-only host inventory resolved NEURAL to index 1 and PRESENT to index 2;
  these are observations, never constants in the script.
- No live power-limit changes or game launch were performed.

Starting revision: `7e7090add873ace772e12cb9177011c62b438d6b`, branch
`mgpu-pci-0c`. Existing uncommitted presentation code and backup files are
outside this launcher change. Runtime presentation behavior is not validated
by these launcher checks.

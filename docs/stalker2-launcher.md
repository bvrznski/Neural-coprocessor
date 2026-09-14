# Controlled STALKER 2 launcher

## Optional MGPU optimization profiles (2026-09-14)

Append `--profile native-upscale` to reduce the neural processing resolution to
the game's own render extent, followed by bridge SR. This uses the existing
`SRUpscale=1`, `SRScale=0`, `SRMvLowRes=0` path documented and implemented in
`src/dllmain.cpp`. The game must already use upscaling; at native/DLAA resolution
this does not provide the intended saving and the bridge may decline SR.
Image quality and frametime require in-game comparison; no measured FPS gain
is claimed on this four-3090 machine. The upstream architecture and measurements
are described at https://github.com/maohgad-web/Neural-coprocessor .

`--profile native` keeps full-resolution neural rendering (`SRUpscale=0`). Both
profiles select one neural pass, coherent ring transport, no frame stride and
disabled diagnostic probes/profiling. Most of these common settings already
match the installed configuration; their presence is not a new performance gain.
Intensity, monitor selection, transport calibration, crash flags and auto-arm
are preserved. No new DLL or Vulkan layer is introduced.

No profile is applied by default. Use `--dry-run` with a profile to preview
without changing files or GPU power. Applying creates an exact-byte
`mgpu.ini.backup-*` alongside the INI and atomically replaces only the relevant
settings. Duplicate relevant keys/sections and unsupported encodings abort.
The launcher refuses profile selection while STALKER 2 is running. Close the
game before using the standalone helper too. Restore the printed backup over
`mgpu.ini` with the game closed for an exact rollback; `native` is a preset,
not a restoration of all previous settings.

Example (replace the address with the verified GAME PCI):

```bash
scripts/launch_stalker2_mgpu.sh --game-pci 0000:43:00.0 --profile native-upscale --dry-run
```

Validation: Bash syntax and ShellCheck; seven Python unit tests covering SR
pairing, unrelated state, native mode, CRLF/BOM/comments, malformed/ambiguous
input, idempotence, read-only preview, backup/restore and symlink rejection.
Three additional mocked launcher checks passed: profile preview, refusal when
the game is running, and refusal when process inspection fails. The installed
INI remained byte-identical. The installed INI was previewed only. No game launch, GPU power change or live
profile application is part of this validation. Uncommitted presentation-path
work in `src/gpu1_context.cpp` is outside this change and remains unvalidated.

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

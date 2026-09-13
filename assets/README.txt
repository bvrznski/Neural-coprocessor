MGPU BRIDGE - INSTALL
=====================

Cross-adapter DLSS Neural Rendering: the game renders on one GPU, the neural
work runs on a second one that is not rendering the game.

This is research code. Read it before you run it - see ACKNOWLEDGEMENTS.md in
the repository, which is not a formality.

THIS IS AN INJECTED PATH, NOT NVIDIA'S. DLSS Neural Rendering is reached here by
injecting through ReShade, not by a game's own DLSS 5 integration. An injected
neural stage sees the frame at a different point than an engine-native one and
makes none of the scheduling decisions a native integration can. Performance and
image quality may differ from NVIDIA's official implementation in either
direction, and the measurements published with this project were taken on two
machines in September 2026 - driver versions, the DLSS-NR model inside them, and
games all move. Treat any absolute number you read about this project as
historical and check your own.


IF YOU ARE UPGRADING FROM 0.1.0, READ THIS FIRST
------------------------------------------------

Two things moved, and a 0.1.0 install left alone will not work.

  1. nvngx_dlssnr.dll NO LONGER SITS BESIDE THE GAME EXECUTABLE. It goes in a
     folder called mgpu, next to the add-on. Move it and DELETE the copy beside
     the executable.

     Some titles load anything named nvngx_*.dll that sits next to their own
     executable. When they do, the neural stage binds to the wrong GPU before
     this add-on's thread exists. Its own subfolder keeps it out of their way.

     The panel says INSTALL PROBLEM if it finds a copy beside the executable.
     Believe it.

  2. mgpu_depth_tap.fx IS NEW AND IS REQUIRED. It goes in ReShade's Shaders
     folder. It needs no effect packages - it is self-contained. Without it
     the bridge waits for a depth buffer that never arrives and never arms.


WHAT YOU NEED FIRST
-------------------

1. ReShade 6.8.0 or newer, installed WITH ADD-ON SUPPORT.

   This is the single most common reason nothing happens. The effects-only
   build of ReShade never loads .addon64 files at all, and it does not say so -
   no error, no log line, because the add-on was never loaded to write one. If
   the log has no "Registered add-on \"MGPU Bridge\"" line, this is why.

2. A second NVIDIA GPU in the machine, with a current driver.

   GEFORCE RTX 50-SERIES. NVIDIA documents DLSS Neural Rendering as a
   50-series feature. This add-on drives the NGX libraries already on your
   machine and cannot enable something they will not run. THIS ADD-ON DOES NOT
   CHECK YOUR HARDWARE: on a card that cannot run it, expect the add-on to
   load, log normally, and produce nothing.

   40-series has since been reported working by a contributor running an
   RTX 4080 SUPER with an RTX 5060 Ti. That report also ruled out PCIe
   bandwidth as the cause of a smoothness issue seen at high load.

   It is the SECOND card that runs the neural stage, so that is the one the
   requirement applies to.

   You do NOT need a shader pack. Ticking effect packages in the ReShade
   installer is optional - this add-on needs add-on support and one shader file
   that ships in this download, and nothing else.

   YOU DO NOT NEED ANY OTHER ADD-ON. This one reaches DLSS Neural Rendering on
   its own: it creates its own D3D12 device on the second GPU and drives the
   NGX libraries directly. Nothing else has to be present.

   DO NOT RUN A SECOND NEURAL PATH ALONGSIDE IT. Untested, and this project has
   already seen two independent NGX consumers sharing one parameter block
   produce a visibly wrong image while every transport counter stayed clean.
   One neural path at a time.

3. TWO MONITORS - ONE ON EACH CARD. This is a requirement, not a nicety. The
   neural output is displayed by the card that produced it, so nothing has to
   travel back across the link. With both monitors on the render card, the same
   build measured 33% lower throughput and roughly double the latency on the
   development machine.

   A SINGLE DISPLAY IS NOT SUPPORTED, and the reason is structural rather than
   a missing feature. The bridge presents the second card's output through its
   own swapchain, in its own window. With one screen that window has to share
   glass with the game, and getting it there reliably means presenting into the
   game's swapchain instead - a different architecture, not a setting.

   A headless second card works and is slower, and there is nothing to look at.

4. A DIRECTX 12 GAME. D3D11 AND VULKAN TITLES DO NOTHING - the add-on loads,
   finds no D3D12 render device, stands down, and says so in the log and in
   the ReShade overlay panel. There is no bridge window on those titles: no
   D3D12 device means no window at all, which is why the message is in the
   panel. Some Unity titles can be forced with -force-d3d12.

   This is a limit of this add-on, not of DLSS Neural Rendering itself, which
   NVIDIA documents against Vulkan. Everything here is built on ReShade's
   D3D12 path.

NOTHING FROM NVIDIA IS INCLUDED HERE, AND NONE OF IT MAY BE. The two NGX
modules do not arrive the same way:

  _nvngx.dll          the driver core. Already resident in the game process on
                      a current driver - that is logged rather than assumed.

  nvngx_dlssnr.dll    the DLSS-NR snippet. Loaded from the mgpu subfolder next
                      to the add-on. On the machines this was built on it was
                      already present in the game folder. THIS PROJECT DOES NOT
                      SHIP IT, CANNOT SHIP IT, AND DOES NOT DOCUMENT HOW TO
                      OBTAIN IT. If the neural stage never starts and the log
                      shows the snippet failing to load, that file is what is
                      missing.

Do not put either of them in a package you hand to somebody else.


INSTALL
-------

Almost everything goes in ONE folder: the one containing the game's .exe. There
are two exceptions and both are named below.

Finding that folder: in Steam, right-click the game -> Manage -> Browse local
files, then keep going down until you see the .exe. For Unreal Engine titles it
is usually several levels down, like

    ...\<Game>\Binaries\Win64\

WHAT THE FOLDER SHOULD LOOK LIKE WHEN YOU ARE DONE

    <the folder with the game .exe>\
        Game.exe                          the game (already there)
        dxgi.dll                          ReShade, ADD-ON-ENABLED build.
                                          You install this yourself with the
                                          ReShade installer. Some installs name
                                          it d3d12.dll instead - either is fine,
                                          it is whatever your ReShade installer
                                          created for this game.
        ReShade.ini                       yours, ReShade makes it on first run
        ReShadePreset.ini                 yours, ReShade makes it on first run

        nvngx.dll_mgpu_bridge.addon64     <- from this download
        mgpu.ini                          <- from this download
        gpu1.ini                          <- from this download
        ReShade2.ini                      <- from this download

        mgpu\
            nvngx_dlssnr.dll              <- NOT from this download. Yours.
                                             NOT beside the .exe.

        reshade-shaders\Shaders\
            mgpu_depth_tap.fx             <- from this download

CREATE A FOLDER CALLED mgpu BESIDE THE GAME EXECUTABLE, AND PUT YOUR
nvngx_dlssnr.dll INSIDE IT. It does not exist until you make it, nothing in this
download creates it, and the name has to be exactly mgpu - that is what the log
and the panel refer to. Do not leave a copy beside the executable; the panel says
INSTALL PROBLEM if it finds one.

mgpu_depth_tap.fx goes wherever your ReShade shaders live. That is usually
reshade-shaders\Shaders\ in the game folder; if your ReShade.ini points
EffectSearchPaths somewhere else, use that instead. YOU DO NOT NEED TO ENABLE
IT in the effects list - the add-on switches it on itself every time it looks.

This README and LICENSE are also in the download. They are for you rather than
for the game folder; copying them there does nothing either way.

WHY THE TAP SHADER IS NOT OPTIONAL

ReShade only binds a depth buffer while an enabled technique consumes one. The
tap consumes depth and draws nothing you can see. Without it in the shader path
ReShade never binds depth, the bridge waits for a buffer that never comes, and
the panel sits on "waiting for a frame" forever. The log says TAP = ABSENT when
the file is missing, and names it.

THREE THINGS THAT ARE NOT IN THIS DOWNLOAD, AND WHY

  1. ReShade itself. Download it from reshade.me and run its installer against
     this game, and TICK ADD-ON SUPPORT when it asks. The effects-only build
     will not load the add-on and will not tell you so. You do not need to tick
     any effect packages.

  2. The NGX modules that do the neural work, and they do not arrive the same
     way as each other.

     _nvngx.dll is the driver core and is already resident in the game process
     on a current driver - 616.64 was used for every figure published with this
     project. Nothing to do about that one.

     nvngx_dlssnr.dll is the DLSS-NR snippet and goes in the mgpu subfolder.
     On the machines this was built on it was already present in the game
     folder. This project does not ship it, cannot ship it, and does not
     document how to obtain it - if the neural stage never starts, check the
     log for the snippet failing to load, because that is the likely reason.

     No NVIDIA binary is redistributed by this project, and you should not
     redistribute one either.

  3. Your own ReShade.ini and ReShadePreset.ini. Deliberately left out, because
     shipping ours would overwrite your existing setup. See "CHECK YOUR OWN
     ReShade.ini" below for the two settings worth changing.

gpu1.ini ships EMPTY on purpose - no techniques, no sort order. It is the preset
ReShade assigns to the bridge's own window, so anything enabled in it is drawn
on top of the neural output. A stale copy of this file once carried a motion-flow
debug view and cost a night of wrong diagnoses; CI now fails the build if it
ships with anything enabled.

DO NOT RENAME THE ADD-ON. The filename must contain the literal substring
"nvngx.dll". The DLSS-NR snippet resolves the module owning its caller's return
address, takes that module's file path, and requires it to contain that
substring. Rename the file and the snippet refuses to resolve; the bridge loads,
logs normally, and produces nothing.

mgpu.ini must sit BESIDE the add-on, not in the working directory. Each game
folder needs its own copy. The log line beginning [MGPU][P7.2] names the exact
file that took effect - if it names somewhere unexpected, or is missing, every
setting is at its default no matter what you edited.


RUN
---

This build ships with AutoArm=1, so the stream arms itself once the game is
presenting. You do not have to press anything.

THE BRIDGE CAN TAKE A WHILE TO ARM, AND THAT IS NORMAL. It does not arm until
the game has bound a depth buffer and a velocity buffer, and neither exists in
a menu. Across the five titles this build was validated on, the wait from
request to armed ran from under two seconds to about forty-five. Get into
gameplay and it clears. If it NEVER clears, read the [R63] and [R78] lines in
the log - they say which of the two is missing.

To arm by hand instead, set AutoArm=0 in mgpu.ini, get into gameplay - not a
menu - and press CTRL+ALT+F10. Do that before measuring anything: an automatic
arm can land in a menu or a loading screen.

Controls, live, no relaunch:

    Panel               the ReShade overlay (Home). The MGPU Bridge panel is
                        registered on both the game's overlay and the bridge
                        window's, so you can drive it without leaving the game.
    CTRL+ALT+F10        arm the stream by hand
    CTRL+ALT+F7         view: neural output -> input -> split
    CTRL+ALT+LEFT/RIGHT move the split seam. Add SHIFT for a coarse step.
                        These need no overlay open, so the seam can be dragged
                        across a face with nothing on screen but the game.
    CTRL+ALT+F8         pick which pass the intensity keys act on
    CTRL+ALT+F9 / F11   intensity down / up

Split shows the frame handed TO the model on the left and what it produced on
the right, in one window, THE SAME FRAME, with a white seam between them. It is
the only honest way to compare the two: no two runs of a game contain the same
frame.


THE SETTINGS WORTH KNOWING ABOUT
--------------------------------

Everything in mgpu.ini is commented. These are the ones that change what you
see, and all of them need a restart.

    Depth=1        Send the game's depth to the second card and bind it.
    MVec=3         Send the game's motion vectors and bind them.

        These are what 0.2.0 adds. The model derives motion from colour on its
        own, which is what 0.1.0 ran on and it works. Feeding it the engine's
        real depth and velocity gives it ground truth instead of an estimate,
        and the gain is image stability: less jitter and sizzle on faces and
        fine geometry while the camera moves. A frame that cannot supply them -
        a menu, a load screen - falls back to the derived motion rather than
        being bound against the wrong buffer.

        Depth=1 needs mgpu_depth_tap.fx. MVec=0 turns motion vectors off.

    SRUpscale=0    DLSS Super Resolution on the second card. OFF by default.
    SRQuality=2    2 quality, 1 balanced, 0 performance.
    SRScale=0      Which resolution neural rendering runs at. 0 means the
                   game's own - see the two upscalers below.
    SRMvLowRes=0   Rides with SRScale. Never set one without the other.

        With SRUpscale off, neural rendering runs at the full display
        resolution. That is the most expensive arrangement and the one every
        published measurement used.

        Turn it on and the second card does its neural work smaller, then
        lets DLSS enlarge the result - worth it when the second card is the
        weaker of the two. This is its own setting and does not depend on the
        game's DLSS, which can be set to anything, or turned off entirely.

        THERE ARE TWO WAYS TO DO THAT, and the panel calls them:

          Native Upscaling      SRScale=0  SRMvLowRes=0   THE DEFAULT
              Upscales from the game's own render resolution. The game's
              motion vectors already describe that resolution, so they are
              used exactly as reported with nothing rescaled. It does
              nothing on a title that is not upscaling - there is no smaller
              frame to start from, and the log says so.

          Experimental Upscaler SRScale=67 SRMvLowRes=1
              Works from a downscaled resolution chosen here instead, with
              the mode buttons, and rescales the game's motion vectors to
              match. More performance, and it works on every title including
              one rendering at native. Possible cost in quality. Untested
              beyond one rig.

        USE THE PANEL RATHER THAN EDITING THESE BY HAND. SRScale and
        SRMvLowRes are one setting: the panel always writes both, and the
        combination they must never form is the one that fails at arm.

    Frames=0       Run until the game closes. Set a number (60..100000) for a
                   bounded run that ends with a summary.

    Passes=1       One neural pass per frame. The build maximum is 2 and is
                   enforced in code.

    Monitor=auto   Which of the second card's outputs the window opens on.


CHECK YOUR OWN ReShade.ini
--------------------------

Two settings in your existing ReShade.ini are worth setting by hand:

  [OVERLAY]
  AutoSavePreset=0

    With this at 1, anything you toggle in the overlay is written back to the
    preset when the game closes. Presets then drift between runs with nobody
    editing a file, and the run you measure is not the run you repeat. Set it
    to 0 while taking measurements.

  [GENERAL]
  PresetPath=.\ReShadePreset.ini

    Whatever you point this at, make sure you know what is enabled in it. Any
    effect enabled for the GAME is drawn before the frame reaches the bridge,
    so it becomes part of what the neural stage sees.


IF SOMETHING LOOKS WRONG, READ THE LOG FIRST
--------------------------------------------

The instrumentation is deliberately loud, and these lines answer almost
everything. If a log line and this README disagree, believe the log.

  Registered add-on "MGPU Bridge"
      Absent: ReShade has no add-on support, or the file is not in this folder.

  [MGPU][R53] TECHNIQUE LANE: ... TAP = ON
      TAP = ABSENT means mgpu_depth_tap.fx is not in the shader path or failed
      to compile, and with Depth=1 the bridge will never arm.

  [MGPU][P1.6] ... | N of 14 techniques ENABLED
      Printed once per runtime, for the GAME and for the BRIDGE. Anything
      listed here is being drawn on top of what you are looking at. This line
      exists because a stale bridge preset once drew a motion-flow debug view
      over the neural output and three code hypotheses were spent on it.

  [MGPU][P7.2] mgpu.ini read from ...
      The settings file that actually took effect. Not the one you edited,
      necessarily.

  [MGPU][P4.0] stream REQUESTED - ... passes=N, ...
      Every setting in force for this run, in one line. If it disagrees with
      your mgpu.ini, the P7.2 line above says why.

  [MGPU][R63] / [MGPU][R78] stream arm HELD
      The bridge is waiting for depth or for motion vectors. Normal in a menu.
      Permanent means the tap is missing, or the title's velocity buffer was
      never identified.


RUNNING WITHOUT A FRAME BOUND
-----------------------------

THIS BUILD SHIPS WITH Frames=0 - the stream runs until the game closes and
prints no summary. Set Frames to a number (60..100000) if you want a bounded
run that ends with a summary, which is what the measurement runs used.

This is implemented as a bound that is never reached, NOT as a stop-and-restart
control: no neural feature and no texture is ever torn down and rebuilt while
the game is live, because that path has never been exercised and is the riskiest
code that could exist here. Nothing new runs; the same single stream simply
never satisfies the condition that ends it.


SCREENSHOTS WITH THE OVERLAY VISIBLE
------------------------------------

PrintScreen saves a clean frame with no overlay, which is usually what you want.
To also get a copy WITH the overlay - useful when you want the pass count and
the split seam visible in the shot - set this in ReShade.ini, and in ReShade2.ini
for the bridge window:

    [SCREENSHOT]
    SaveOverlayShot=1

ReShade then writes a second image alongside the clean one.


KNOWN LIMITATIONS
-----------------

THE ONE BAD FAILURE THIS PROJECT SAW WAS AT SIX PASSES. One development
session ended with the game rendering black on both displays after several
minutes, on a six-pass run. The exact mechanism was never isolated - a later
twenty-minute run at TWO passes sat at 174W of a 180W limit and was completely
stable, so simply being at the power limit is not the explanation. This build
allows at most two passes and the bound is enforced in code, so the condition
that produced it is not reachable from the settings file.

The bridge window's own frame rate falls as the pass count rises. The game's
does not. That is the architecture working, not a fault.

Interacting with the bridge window takes keyboard focus away from the game. A
controller sidesteps this entirely.

DO NOT CHANGE RESOLUTION, DLSS MODE OR GRAPHICS PRESETS WHILE THE STREAM IS
ARMED. The stream is armed once, against the game's swapchain exactly as it
stands at that instant - source size, format and row pitch are fixed then.
Anything that makes the game rebuild its swapchain leaves the bridge consuming
against an arrangement that no longer exists. On the development machine this
produced a run of dropped and reordered frames beginning a second after the
change, and the session could freeze. Set the game up first, then let it arm. To
change something afterwards, close the game and relaunch. The same applies to
anything you change in the panel.

FRAME GENERATION IS UNTESTED. It was enabled once and that session ended badly,
on a machine that was also failing on ordinary settings changes, so nothing is
established either way. It is not recommended and it has not been characterised.

WASHED OR FLAT COLOUR? Open the panel (Home over the bridge window) and take the
"tone" slider down - 0.00 fixed it on the development rig, and yours may differ.
Colour handling is not implemented in this add-on and on one of the two titles
tested the output comes back washed; the cause is not established. Motion
vectors for UI and HUD elements are also still missing.

THE BRIDGE WINDOW SHOULD OPEN ON THE SECOND MONITOR BY ITSELF. If it opens on
the game's display instead, set Monitor=<n> in mgpu.ini and check the
[MGPU][P7.10] line in ReShade.log - it names which monitor it chose and how.
Earlier builds always opened on the game's display and had to be dragged once
per launch; that is fixed, and a build that still does it is telling you the
placement fell back, which the log will say.

EXTERNAL FPS OVERLAYS FLICKER, AND IT IS NOT YOUR SETUP. This add-on puts a
second swapchain inside the game's process. RivaTuner / MSI Afterburner assume
one swapchain per process and flip between the two present streams; the NVIDIA
overlay does not recognise the bridge window at all. Use ReShade's own counter -
there are two ReShade runtimes here, so each draws its own FPS for its own
window, and the game's rate and the bridge's rate are different numbers by
design. Set ShowFPS=1 under [OVERLAY] in ReShade.ini AND in ReShade2.ini.

For screen recording, use a display capture or a Windows Graphics Capture window
source rather than "game capture", which adds a third Present hook to a process
that already has two.


No warranty. See LICENSE. Not affiliated with, endorsed by, or supported by
NVIDIA.

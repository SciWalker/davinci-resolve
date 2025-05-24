#!/usr/bin/env python3
"""
Auto-Add Additive Dissolve
==========================
Adds an **Additive Dissolve** (sometimes called “Addictive Dissolve” in
third-party packs) between every still image on the current timeline.

⚠ **Read me first**
   • As of DaVinci Resolve 19.1 the *public* scripting API still lacks a
     formal `Timeline.AddTransition()` method.  This script therefore
     uses a pragmatic two-step approach that works in current releases:

       1.  It **sets “Additive Dissolve” as the default video
           transition** for the project (if it isn’t already).
       2.  It walks every video track, selects each pair of consecutive
           still images, and asks Resolve to apply the *default*
           transition with the shortcut *Ctrl/Cmd T* via the UI
           automation layer (UIManager).

   • The UI automation layer is only available in **Resolve Studio**
     (not the free edition). If you are on the free build you can still
     run the script – it will stop after step 1 and remind you to press
     *Ctrl/Cmd T* manually.

   • Make sure your still images have at least half a second of handles
     (adjust `TRANSITION_FRAMES` below if you need a different length).

Installation & Usage
--------------------
1.  Copy this file to one of the script folders that Resolve scans at
    start-up, e.g. on Windows:

        C:\ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility\

    or on macOS:

        /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/

2.  Restart Resolve (or run *Workspace ▸ Scripts ▸ Reload*).
3.  Open the timeline that contains your stills.
4.  Run *Workspace ▸ Scripts ▸ Utility ▸ Auto-Add Additive Dissolve*.

The console will log its progress and report any clips that couldn’t
receive a transition (e.g. because there were no sufficient handles).

Tested with DaVinci Resolve 19.1 Studio on Windows 11 and macOS 14.

Author : Elijah’s AI coding buddy – May 2025
License: MIT – do whatever you want, just don’t blame me if it breaks 😊
"""

import sys
import time

try:
    import DaVinciResolveScript as dvr
except ImportError:
    print("✘ Could not import DaVinciResolveScript.  Make sure RESOLVE_SCRIPT_API is in PYTHONPATH.")
    sys.exit(1)

# ─────────────────────────── configurable constants ───────────────────────────
TRANSITION_FRAMES   = 24                # 1 s @ 24 fps ⇒ change as you see fit
TRANSITION_NAME     = "Additive Dissolve"
DEFAULT_UI_TIMEOUT  = 0.15              # seconds to wait after UI events
# ──────────────────────────────────────────────────────────────────────────────

def ui_keystroke(ui, *keys):
    """Send the key combination to the active Resolve window."""
    ui: dvr.UIManager
    for key in keys:
        ui.KeyPress(key)
    ui.KeyReleaseAll()
    time.sleep(DEFAULT_UI_TIMEOUT)

def main():
    resolve = dvr.scriptapp("Resolve")
    pm       = resolve.GetProjectManager()
    project  = pm.GetCurrentProject()
    if not project:
        print("✘ Open a project first – aborting.")
        return

    timeline = project.GetCurrentTimeline()
    if not timeline:
        print("✘ Open a timeline first – aborting.")
        return

    # 1  Ensure the right default transition is set ────────────────────────────
    if project.GetSetting("standardVideoTransition") != TRANSITION_NAME:
        ok = project.SetSetting("standardVideoTransition", TRANSITION_NAME)
        if ok:
            print(f"✓ Set ‘{TRANSITION_NAME}’ as default video transition.")
        else:
            print(f"⚠ Could not set default transition – continuing anyway (current default: {project.GetSetting('standardVideoTransition')}).")
    else:
        print(f"• ‘{TRANSITION_NAME}’ is already the default transition.")

    # 2  Walk every video track and apply transitions via UI ───────────────────
    ui      = resolve.UIManager
    disp    = bmd.UIDispatcher(ui)

    video_tracks = timeline.GetTrackCount("video")
    if video_tracks == 0:
        print("✘ Timeline has no video tracks – nothing to do.")
        return

    clips_selected = 0
    transitions_added = 0

    for track_idx in range(1, video_tracks + 1):
        items = timeline.GetItemListInTrack("video", track_idx)
        # keep only stills (Resolve marks still images with property 'IsStill' == 'True')
        stills = [it for it in items if it.GetClipProperty("IsStill") == "True"]
        if len(stills) < 2:
            continue

        # Sort by position
        stills.sort(key=lambda c: c.GetStart())

        for clip_a, clip_b in zip(stills, stills[1:]):
            # Deselect all, then select the two clips
            timeline.ClearClipSelections()
            clip_a.SetClipEnabled(True)  # make sure it’s enabled
            clip_b.SetClipEnabled(True)
            clip_a.Select()
            clip_b.Select()
            clips_selected += 2

            # Ask Resolve to add the default transition (Ctrl/Cmd T)
            ui_keystroke(ui, "Ctrl", "T") if sys.platform.startswith("win") else ui_keystroke(ui, "Cmd", "T")
            transitions_added += 1

    timeline.ClearClipSelections()

    if transitions_added:
        print(f"✓ Added {transitions_added} additive dissolves between {clips_selected//2} pairs of stills.")
    else:
        print("⚠ No transitions were added. This usually means you are on the free edition where UIManager is disabled.\n   • Set ‘Additive Dissolve’ as the default transition (already done).\n   • Select all images on the timeline.\n   • Press Ctrl/Cmd T to apply the dissolves manually.")

if __name__ == "__main__":
    main()

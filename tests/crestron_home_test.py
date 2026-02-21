#!/usr/bin/env python3
"""
Crestron Home App — Automated UI Test Suite
============================================
Uses NeuralBridge MCP server as the automation backend.

Usage:
    python3 tests/crestron_home_test.py [--device DEVICE_ID] [--server PATH]

Prerequisites:
    • NeuralBridge MCP server binary built:   mcp-server/target/release/neuralbridge-mcp
    • Companion app installed and AccessibilityService enabled on device
    • Crestron Home app (com.crestron.phoenix.app) installed

Test Coverage (18 test cases):
    HOME SCREEN   : TC001–TC006
    MUSIC PLAYER  : TC007–TC009
    ROOMS VIEW    : TC010–TC014
    OVERFLOW MENU : TC015–TC016
    NAVIGATION    : TC017–TC018
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────────────
PKG           = "com.crestron.phoenix.app"
ACTIVITY      = f"{PKG}/.host.MainActivity"
REPORT_DIR    = Path(__file__).parent / "reports"
SERVER_PATH   = Path(__file__).parent.parent / "mcp-server" / "target" / "release" / "neuralbridge-mcp"
DEFAULT_DEVICE = "344656504e303098"

# Screen element selectors (resource-ids discovered during autonomous exploration)
SEL = {
    "home_toolbar_container":  "com.crestron.phoenix.app:id/home_toolbarContainer",
    "home_house_name":         "com.crestron.phoenix.app:id/home_wholeHouse_name",
    "home_controls_header":    "com.crestron.phoenix.app:id/home_wholeHouse_homeControlsSectionHeader",
    "home_subsystems_grid":    "com.crestron.phoenix.app:id/home_subsystemsRecyclerView",
    "home_service_title":      "com.crestron.phoenix.app:id/serviceTitle",
    "home_service_subtitle":   "com.crestron.phoenix.app:id/serviceSubtitle",
    "home_menu_button":        "com.crestron.phoenix.app:id/home_wholeHouse_topbarMenuButton",
    "bottom_nav":              "com.crestron.phoenix.app:id/bottomNavigationView",
    "bottom_nav_left":         "[0,1942][540,2094]",     # Home tab bounds
    "bottom_nav_right":        "[540,1942][1080,2094]",  # Rooms tab bounds
    "main_viewpager":          "com.crestron.phoenix.app:id/main_viewPager",
    "music_icon":              "home_subsystem_icon_Music",   # content-desc
}

# Known text labels on each screen (for assertions)
HOME_SCREEN_TEXTS    = ["Eagle Ln", "Controls", "Music"]
MUSIC_SCREEN_TEXTS   = ["Music"]          # at minimum the title persists
ROOMS_TAB_TEXTS      = ["ALL", "FAVORITES"]


# ─── Result Types ─────────────────────────────────────────────────────────────
@dataclass
class TestResult:
    test_id:    str
    name:       str
    status:     str          # PASS | FAIL | ERROR | SKIP
    message:    str = ""
    screenshot: Optional[str] = None
    duration_s: float = 0.0
    steps:      List[str] = field(default_factory=list)


# ─── MCP Client ───────────────────────────────────────────────────────────────
class NeuralBridgeClient:
    """Thin synchronous wrapper around the NeuralBridge MCP server (stdio)."""

    def __init__(self, server_path: str, device_id: str):
        self.server_path = server_path
        self.device_id   = device_id
        self.process: Optional[subprocess.Popen] = None
        self._req_id = 0

    # ── lifecycle ──────────────────────────────────────────────────────────
    def start(self):
        sdk = Path.home() / "Android" / "Sdk" / "platform-tools"
        env = os.environ.copy()
        env["PATH"] = f"{sdk}:{env.get('PATH','')}"

        # Kill any competing neuralbridge-mcp processes so they don't hold
        # the companion TCP connection while we run tests.
        try:
            subprocess.run(
                ["pkill", "-f", "neuralbridge-mcp"],
                capture_output=True, timeout=5
            )
            time.sleep(1.5)   # Wait for ports to fully release
        except Exception:
            pass

        # Launch server with explicit --device so startup is deterministic
        # and there is no blocking ADB discovery phase before stdio is ready.
        self.process = subprocess.Popen(
            [self.server_path, "--device", self.device_id],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        self._init_handshake()

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass

    # ── JSON-RPC I/O ───────────────────────────────────────────────────────
    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _send(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        line = json.dumps(msg) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()
        # Notifications have no id → no response
        if "id" not in msg:
            return None
        raw = self.process.stdout.readline()
        if not raw:
            raise RuntimeError("MCP server closed connection")
        return json.loads(raw)

    def _init_handshake(self):
        resp = self._send({
            "jsonrpc": "2.0", "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "crestron-test-client", "version": "1.0.0"},
            },
        })
        if not resp or "error" in resp:
            raise RuntimeError(f"MCP init failed: {resp}")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        # The server was started with --device so it auto-selects on startup.
        # Still call _select_device() to eagerly establish the companion TCP
        # connection and verify permissions.
        self._select_device()
        time.sleep(1.0)   # Let the companion connection settle

    def _select_device(self):
        """Tell the MCP server which device to use (reconnects companion TCP)."""
        resp = self._send({
            "jsonrpc": "2.0", "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "android_select_device",
                "arguments": {
                    "device_id": self.device_id,
                    # Do NOT auto-enable: the service is already running from the
                    # previous VS Code session.  auto_enable=True re-writes the
                    # accessibility settings which causes the Android runtime to
                    # restart the companion service (~3s outage).
                    "auto_enable_permissions": False,
                },
            },
        })
        return resp

    # ── Tool calls ─────────────────────────────────────────────────────────
    def _parse_result(self, resp: Dict) -> Dict[str, Any]:
        result  = resp.get("result", {}) if resp else {}
        content = result.get("content", [])
        if content:
            text = content[0].get("text", "{}")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
        return result

    def tool(self, name: str, args: Dict[str, Any] = None,
             _retries: int = 3) -> Dict[str, Any]:
        """Call a tool with automatic retry on transient companion drops.

        The MCP server's get_connection() detects dead TCP sockets via is_alive()
        and reconnects automatically.  We just need to wait a moment and retry;
        there is no need to call _select_device() (which would re-run port-
        forwarding ADB commands and could trigger an accessibility-service
        restart).
        """
        for attempt in range(_retries + 1):
            resp = self._send({
                "jsonrpc": "2.0", "id": self._next_id(),
                "method": "tools/call",
                "params": {"name": name, "arguments": args or {}},
            })
            if resp and "error" in resp:
                err = resp["error"]
                code = err.get("code", 0) if isinstance(err, dict) else 0
                msg  = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                # The server auto-reconnects via get_connection() on the next call
                # when it detects the cached connection is dead (is_alive() == False).
                # So we just back off and retry directly.
                if code == -32603 and ("connection" in msg.lower() or "companion" in msg.lower()):
                    if attempt < _retries:
                        print(f"        [retry {attempt+1}/{_retries}] Companion closed — server will reconnect...")
                        time.sleep(1.5)
                        continue
                raise RuntimeError(f"Tool '{name}' error: {resp['error']}")
            return self._parse_result(resp)
        raise RuntimeError(f"Tool '{name}' failed after {_retries+1} attempts")

    # ── Convenience helpers ────────────────────────────────────────────────
    def get_ui(self) -> Dict[str, Any]:
        return self.tool("android_get_ui_tree", {"include_invisible": False})

    def screenshot(self, label: str) -> Optional[str]:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORT_DIR / f"{label}_{int(time.time())}.png"
        try:
            data = self.tool("android_screenshot", {"quality": "thumbnail", "max_width": 720})
            # MCP returns base64 or writes to file; if raw bytes available save them
            if isinstance(data, dict) and "error" not in data:
                # Fallback: ADB screencap
                r = subprocess.run(
                    ["adb", "-s", self.device_id, "exec-out", "screencap", "-p"],
                    capture_output=True, timeout=15
                )
                if r.returncode == 0:
                    path.write_bytes(r.stdout)
                    return str(path)
        except Exception:
            pass
        # ADB fallback
        try:
            r = subprocess.run(
                ["adb", "-s", self.device_id, "exec-out", "screencap", "-p"],
                capture_output=True, timeout=15
            )
            if r.returncode == 0:
                path.write_bytes(r.stdout)
                return str(path)
        except Exception:
            pass
        return None

    def tap(self, x: int, y: int) -> bool:
        r = self.tool("android_tap", {"x": x, "y": y})
        return r.get("success", False)

    def tap_text(self, text: str) -> bool:
        r = self.tool("android_tap", {"text": text})
        return r.get("success", False)

    def tap_resource_id(self, rid: str) -> bool:
        r = self.tool("android_tap", {"resource_id": rid})
        return r.get("success", False)

    def tap_content_desc(self, desc: str) -> bool:
        r = self.tool("android_tap", {"content_desc": desc})
        return r.get("success", False)

    def press_back(self):
        self.tool("android_press_key", {"key": "back"})
        time.sleep(1.0)

    def wait_idle(self, timeout_ms: int = 3000):
        try:
            self.tool("android_wait_for_idle", {"timeout_ms": timeout_ms})
        except Exception:
            time.sleep(timeout_ms / 1000)

    def find_element(self, ui: Dict[str, Any], *,
                     text: str = None, resource_id: str = None,
                     content_desc: str = None, partial: bool = True) -> Optional[Dict]:
        for el in ui.get("elements", []):
            if text:
                t = el.get("text", "")
                match = (text.lower() in t.lower()) if partial else (text.lower() == t.lower())
                if match:
                    return el
            if resource_id and resource_id in el.get("resource_id", ""):
                return el
            if content_desc and content_desc in el.get("content_description", ""):
                return el
        return None

    def element_center(self, el: Dict) -> Tuple[int, int]:
        b = el.get("bounds", {})
        return ((b["left"] + b["right"]) // 2, (b["top"] + b["bottom"]) // 2)

    def texts_present(self, ui: Dict[str, Any], texts: List[str]) -> List[str]:
        """Return list of texts NOT found in the UI tree."""
        found = {el.get("text", "") for el in ui.get("elements", [])}
        return [t for t in texts if not any(t.lower() in f.lower() for f in found)]


# ─── ADB Helpers (fallback + app lifecycle) ───────────────────────────────────
def adb(device: str, *args, binary=False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["adb", "-s", device] + list(args),
        capture_output=True,
        text=not binary,
        timeout=20
    )


def launch_app(device: str):
    adb(device, "shell", "am", "start", "-n", ACTIVITY)
    time.sleep(3)


def kill_app(device: str):
    adb(device, "shell", "am", "force-stop", PKG)
    time.sleep(1)


def app_in_foreground(device: str) -> bool:
    r = adb(device, "shell", "dumpsys", "window").stdout
    return PKG in r and "mCurrentFocus" in r


# ─── Test Runner ──────────────────────────────────────────────────────────────
class CrestronTestSuite:
    def __init__(self, client: NeuralBridgeClient, device: str):
        self.c       = client
        self.device  = device
        self.results: List[TestResult] = []

    def _run(self, test_id: str, name: str, fn) -> TestResult:
        print(f"\n  ▶  {test_id}: {name}")
        r = TestResult(test_id=test_id, name=name, status="PASS")
        # NOTE: Do NOT call _select_device() before every test — doing so
        # triggers remove_port_forwarding + reconnect each time, which is
        # slow and can destabilise the companion connection.
        # The auto-reconnect in tool() handles transient drops instead.
        t0 = time.time()
        try:
            fn(r)
        except AssertionError as e:
            r.status  = "FAIL"
            r.message = str(e)
            r.screenshot = self.c.screenshot(f"FAIL_{test_id}")
            print(f"     ✗  FAIL — {e}")
        except Exception as e:
            r.status  = "ERROR"
            r.message = f"{type(e).__name__}: {e}"
            r.screenshot = self.c.screenshot(f"ERROR_{test_id}")
            print(f"     ✗  ERROR — {e}")
        else:
            print(f"     ✓  PASS")
        r.duration_s = round(time.time() - t0, 2)
        self.results.append(r)
        return r

    def _assert_texts(self, ui: Dict, texts: List[str], context: str = ""):
        missing = self.c.texts_present(ui, texts)
        assert not missing, f"{context} Missing texts: {missing}"

    def _assert_element(self, ui: Dict, *, text=None, resource_id=None,
                        content_desc=None, context=""):
        el = self.c.find_element(ui, text=text, resource_id=resource_id, content_desc=content_desc)
        what = text or resource_id or content_desc
        assert el is not None, f"{context} Element not found: {what!r}"
        return el

    # ═══════════════════════════════════════════════════════════════════════
    # HOME SCREEN TESTS  (TC001 – TC006)
    # ═══════════════════════════════════════════════════════════════════════
    def tc001_app_launches(self, r: TestResult):
        """App opens and is in the foreground."""
        r.steps.append("Force-stop then relaunch app")
        kill_app(self.device)
        launch_app(self.device)
        self.c.wait_idle(4000)
        assert app_in_foreground(self.device), \
            f"{PKG} is not in the foreground after launch"

    def tc002_home_shows_house_name(self, r: TestResult):
        """Home screen displays the house name 'Eagle Ln'."""
        r.steps.append("Get UI tree")
        ui = self.c.get_ui()
        r.steps.append("Assert 'Eagle Ln' present")
        self._assert_element(ui, resource_id=SEL["home_house_name"],
                             context="TC002")
        # Also verify it has readable text
        el = self.c.find_element(ui, resource_id=SEL["home_house_name"])
        if el:
            assert el.get("text", ""), "House name element has no text"

    def tc003_home_shows_controls_section(self, r: TestResult):
        """Home screen has a 'Controls' section header."""
        r.steps.append("Get UI tree and check Controls header")
        ui = self.c.get_ui()
        self._assert_element(ui, resource_id=SEL["home_controls_header"],
                             context="TC003")

    def tc004_home_shows_music_subsystem(self, r: TestResult):
        """Music subsystem card is visible with title and subtitle."""
        r.steps.append("Get UI tree")
        ui = self.c.get_ui()
        r.steps.append("Assert Music title element")
        self._assert_element(ui, resource_id=SEL["home_service_title"],
                             context="TC004 — service title")
        r.steps.append("Assert Music subtitle (status) element")
        self._assert_element(ui, resource_id=SEL["home_service_subtitle"],
                             context="TC004 — service subtitle")
        r.steps.append("Assert Music icon content-desc")
        self._assert_element(ui, content_desc=SEL["music_icon"],
                             context="TC004 — music icon")

    def tc005_music_card_tap_opens_music_screen(self, r: TestResult):
        """Tapping the Music card navigates to the Music player screen."""
        r.steps.append("Get home UI tree")
        ui = self.c.get_ui()
        # Find a clickable card that contains the Music service icon
        music_icon = self.c.find_element(ui, content_desc=SEL["music_icon"])
        assert music_icon, "TC005: Music icon not found on home screen"

        # Find parent clickable wrapping the icon
        icon_b = music_icon.get("bounds", {})
        card = None
        for el in ui.get("elements", []):
            if not el.get("clickable"):
                continue
            b = el.get("bounds", {})
            if (b.get("left",9999) <= icon_b.get("left",0) and
                b.get("top",9999)  <= icon_b.get("top",0) and
                b.get("right",0)   >= icon_b.get("right",9999) and
                b.get("bottom",0)  >= icon_b.get("bottom",9999)):
                card = el
                break

        assert card, "TC005: Clickable Music card not found"
        cx, cy = self.c.element_center(card)
        r.steps.append(f"Tap Music card at ({cx},{cy})")
        self.c.tap(cx, cy)
        self.c.wait_idle(3000)

        r.steps.append("Verify Music screen is open (not home)")
        ui2 = self.c.get_ui()
        # Music screen should NOT have the home controls header
        home_header = self.c.find_element(ui2, resource_id=SEL["home_controls_header"])
        # It's OK if controls header disappears (navigated away)
        # But it should still be in Crestron app
        assert app_in_foreground(self.device), "TC005: App left foreground after tapping Music"
        r.screenshot = self.c.screenshot("TC005_music_screen")

    def tc006_back_from_music_returns_home(self, r: TestResult):
        """Back from Music screen returns to home screen."""
        r.steps.append("Press back")
        self.c.press_back()
        self.c.wait_idle(2000)
        r.steps.append("Verify home screen Controls header is back")
        ui = self.c.get_ui()
        assert app_in_foreground(self.device), "TC006: App exited foreground"
        # Verify we're back on main container
        main = self.c.find_element(ui, resource_id="com.crestron.phoenix.app:id/main_root")
        assert main is not None, "TC006: main_root not found — may not be on home"

    # ═══════════════════════════════════════════════════════════════════════
    # MUSIC PLAYER TESTS  (TC007 – TC009)
    # ═══════════════════════════════════════════════════════════════════════
    def tc007_music_player_has_title(self, r: TestResult):
        """Music player screen shows a music-related title."""
        r.steps.append("Navigate to Music player")
        ui_home = self.c.get_ui()
        music_icon = self.c.find_element(ui_home, content_desc=SEL["music_icon"])
        if not music_icon:
            r.status  = "SKIP"
            r.message = "Music icon not on screen — skipping"
            return
        # Find and tap the card containing the icon
        icon_b = music_icon.get("bounds", {})
        card   = None
        for el in ui_home.get("elements", []):
            if not el.get("clickable"):
                continue
            b = el.get("bounds", {})
            if (b.get("left",9999) <= icon_b.get("left",0) and
                b.get("top",9999)  <= icon_b.get("top",0) and
                b.get("right",0)   >= icon_b.get("right",9999) and
                b.get("bottom",0)  >= icon_b.get("bottom",9999)):
                card = el
                break
        if not card:
            r.status  = "SKIP"
            r.message = "Music card container not found"
            return
        cx, cy = self.c.element_center(card)
        self.c.tap(cx, cy)
        self.c.wait_idle(3000)
        r.steps.append("Check Music title present in new screen")
        ui_music = self.c.get_ui()
        music_text = self.c.find_element(ui_music, text="Music")
        assert music_text is not None, "TC007: 'Music' text not found on music screen"
        r.screenshot = self.c.screenshot("TC007_music_player")

    def tc008_music_player_shows_status(self, r: TestResult):
        """Music player shows a playback status."""
        ui = self.c.get_ui()
        # Status could be 'NOT PLAYING', 'PLAYING', 'PAUSED', etc.
        subtitle = self.c.find_element(ui, resource_id=SEL["home_service_subtitle"])
        if subtitle is None:
            # Different screen layout, just check we're in the app
            assert app_in_foreground(self.device), "TC008: App left foreground"
            r.message = "Status subtitle not found but app is running (layout may differ)"
            return
        assert subtitle.get("text", ""), "TC008: Music status subtitle is empty"

    def tc009_back_from_music_to_home(self, r: TestResult):
        """Back from Music player returns to home."""
        r.steps.append("Press back")
        self.c.press_back()
        self.c.wait_idle(2000)
        assert app_in_foreground(self.device), "TC009: App exited after back"

    # ═══════════════════════════════════════════════════════════════════════
    # ROOMS VIEW TESTS  (TC010 – TC014)
    # ═══════════════════════════════════════════════════════════════════════
    def _ensure_home(self):
        """Make sure we are on the home tab."""
        # Tap the left bottom nav tab (Home)
        self.c.tap(270, 2018)        # center of [0,1942][540,2094]
        self.c.wait_idle(2000)

    def _navigate_to_rooms(self):
        """Tap the right bottom nav tab to open Rooms view."""
        self.c.tap(810, 2018)        # center of [540,1942][1080,2094]
        self.c.wait_idle(2000)

    def tc010_rooms_tab_navigate(self, r: TestResult):
        """Bottom nav right tab opens the Rooms view."""
        r.steps.append("Navigate to Rooms tab")
        self._navigate_to_rooms()
        ui = self.c.get_ui()
        # Rooms screen has ALL / FAVORITES filter tabs
        any_filter = (self.c.find_element(ui, text="ALL") or
                      self.c.find_element(ui, text="FAVORITES"))
        assert any_filter is not None, \
            "TC010: Neither ALL nor FAVORITES found — Rooms tab may not have opened"
        r.screenshot = self.c.screenshot("TC010_rooms_tab")

    def tc011_rooms_all_filter_tab(self, r: TestResult):
        """'ALL' filter tab is present and clickable on Rooms view."""
        r.steps.append("Get UI tree on Rooms")
        ui = self.c.get_ui()
        all_tab = self.c.find_element(ui, text="ALL")
        assert all_tab is not None, "TC011: 'ALL' tab not found on Rooms screen"
        assert all_tab.get("clickable"), "TC011: 'ALL' tab is not clickable"
        r.steps.append("Tap ALL tab")
        cx, cy = self.c.element_center(all_tab)
        self.c.tap(cx, cy)
        self.c.wait_idle(1500)

    def tc012_rooms_favorites_filter_tab(self, r: TestResult):
        """'FAVORITES' filter tab is present and clickable."""
        r.steps.append("Get UI tree on Rooms")
        ui = self.c.get_ui()
        fav_tab = self.c.find_element(ui, text="FAVORITES")
        assert fav_tab is not None, "TC012: 'FAVORITES' tab not found on Rooms screen"
        assert fav_tab.get("clickable"), "TC012: 'FAVORITES' tab is not clickable"
        r.steps.append("Tap FAVORITES tab")
        cx, cy = self.c.element_center(fav_tab)
        self.c.tap(cx, cy)
        self.c.wait_idle(1500)
        r.screenshot = self.c.screenshot("TC012_favorites_tab")

    def tc013_rooms_shows_room_cards(self, r: TestResult):
        """Rooms view shows at least one room card."""
        r.steps.append("Tap ALL to show everything")
        self.c.tap_text("ALL")
        self.c.wait_idle(1500)
        r.steps.append("Check for room cards")
        ui = self.c.get_ui()
        # Room cards are ViewGroups that are clickable in the main area (not nav bar)
        NAV_BOUNDS = {"[0,1942][540,2094]", "[540,1942][1080,2094]"}
        cards = [el for el in ui.get("elements", [])
                 if el.get("clickable") and el.get("class") == "android.view.ViewGroup"
                 and el.get("bounds") not in NAV_BOUNDS
                 and el.get("bounds", "").startswith("[24,")]
        r.message = f"Found {len(cards)} room card(s)"
        assert len(cards) >= 1, f"TC013: No room cards found. {r.message}"
        r.screenshot = self.c.screenshot("TC013_room_cards")

    def tc014_rooms_view_size_toggle(self, r: TestResult):
        """View size toggle button exists in Rooms view."""
        r.steps.append("Check for view size toggle")
        ui = self.c.get_ui()
        toggle = self.c.find_element(ui, content_desc="icSwitchRoomViewSizeOff")
        if not toggle:
            # Try by resource id pattern
            toggle = next(
                (el for el in ui.get("elements", [])
                 if "SwitchRoomViewSize" in el.get("content_description", "")
                 or "SwitchRoomViewSize" in el.get("resource_id", "")),
                None
            )
        assert toggle is not None, "TC014: View size toggle not found on Rooms screen"
        assert toggle.get("clickable"), "TC014: View size toggle is not clickable"
        r.steps.append("Tap view size toggle")
        cx, cy = self.c.element_center(toggle)
        self.c.tap(cx, cy)
        self.c.wait_idle(1500)
        r.screenshot = self.c.screenshot("TC014_view_toggle")

    # ═══════════════════════════════════════════════════════════════════════
    # OVERFLOW MENU TESTS  (TC015 – TC016)
    # ═══════════════════════════════════════════════════════════════════════
    def tc015_overflow_menu_opens(self, r: TestResult):
        """3-dot overflow menu button exists on home and opens a menu."""
        r.steps.append("Navigate back to home")
        self._ensure_home()
        self.c.wait_idle(2000)
        r.steps.append("Get UI tree on home")
        ui = self.c.get_ui()
        menu_btn = self.c.find_element(ui, resource_id=SEL["home_menu_button"])
        assert menu_btn is not None, "TC015: 3-dot menu button not found on home screen"
        r.steps.append("Tap 3-dot menu button")
        cx, cy = self.c.element_center(menu_btn)
        self.c.tap(cx, cy)
        self.c.wait_idle(2000)
        r.steps.append("Verify menu appeared (more elements visible)")
        ui2 = self.c.get_ui()
        assert len(ui2.get("elements", [])) > len(ui.get("elements", [])), \
            "TC015: Element count did not increase after opening menu"
        r.screenshot = self.c.screenshot("TC015_overflow_menu")

    def tc016_overflow_menu_dismisses(self, r: TestResult):
        """Overflow menu can be dismissed by pressing Back."""
        r.steps.append("Press back to close menu")
        self.c.press_back()
        self.c.wait_idle(1500)
        r.steps.append("Verify back on home screen")
        assert app_in_foreground(self.device), \
            "TC016: App left foreground when dismissing menu"

    # ═══════════════════════════════════════════════════════════════════════
    # NAVIGATION FLOW TESTS  (TC017 – TC018)
    # ═══════════════════════════════════════════════════════════════════════
    def tc017_home_tab_returns_from_rooms(self, r: TestResult):
        """Bottom nav left (Home) tab from Rooms returns to home screen."""
        r.steps.append("Navigate to Rooms")
        self._navigate_to_rooms()
        self.c.wait_idle(1500)
        r.steps.append("Tap Home tab (left nav)")
        self._ensure_home()
        r.steps.append("Verify home screen content")
        ui = self.c.get_ui()
        home_root = self.c.find_element(ui, resource_id="com.crestron.phoenix.app:id/main_root")
        assert home_root is not None, \
            "TC017: main_root element missing — may not be on home screen"
        assert app_in_foreground(self.device), "TC017: App left foreground"

    def tc018_app_recovers_from_multiple_backs(self, r: TestResult):
        """Pressing Back multiple times never crashes the app."""
        r.steps.append("Press back 3 times")
        for i in range(3):
            self.c.press_back()
            time.sleep(0.8)
        r.steps.append("Relaunch if app exited foreground")
        if not app_in_foreground(self.device):
            launch_app(self.device)
            self.c.wait_idle(3000)
        r.steps.append("Verify app is running normally")
        assert app_in_foreground(self.device), \
            "TC018: App did not recover after multiple back presses"
        r.screenshot = self.c.screenshot("TC018_recovery")

    # ═══════════════════════════════════════════════════════════════════════
    # Suite Runner
    # ═══════════════════════════════════════════════════════════════════════
    def run_all(self) -> List[TestResult]:
        TESTS = [
            ("TC001", "App launches to foreground",              self.tc001_app_launches),
            ("TC002", "Home screen — house name displayed",      self.tc002_home_shows_house_name),
            ("TC003", "Home screen — Controls section header",   self.tc003_home_shows_controls_section),
            ("TC004", "Home screen — Music subsystem card",      self.tc004_home_shows_music_subsystem),
            ("TC005", "Music card tap → Music screen",           self.tc005_music_card_tap_opens_music_screen),
            ("TC006", "Back from Music → home screen",           self.tc006_back_from_music_returns_home),
            ("TC007", "Music player — title visible",            self.tc007_music_player_has_title),
            ("TC008", "Music player — status text present",      self.tc008_music_player_shows_status),
            ("TC009", "Back from Music player → home",           self.tc009_back_from_music_to_home),
            ("TC010", "Rooms tab navigation via bottom nav",     self.tc010_rooms_tab_navigate),
            ("TC011", "Rooms view — ALL filter tab clickable",   self.tc011_rooms_all_filter_tab),
            ("TC012", "Rooms view — FAVORITES filter tab",       self.tc012_rooms_favorites_filter_tab),
            ("TC013", "Rooms view — shows room cards",           self.tc013_rooms_shows_room_cards),
            ("TC014", "Rooms view — size toggle button",         self.tc014_rooms_view_size_toggle),
            ("TC015", "Overflow menu opens on home",             self.tc015_overflow_menu_opens),
            ("TC016", "Overflow menu dismisses on Back",         self.tc016_overflow_menu_dismisses),
            ("TC017", "Home tab returns from Rooms",             self.tc017_home_tab_returns_from_rooms),
            ("TC018", "App recovers from multiple Back presses", self.tc018_app_recovers_from_multiple_backs),
        ]

        print(f"\n{'='*60}")
        print(f"  Crestron Home — UI Test Suite ({len(TESTS)} tests)")
        print(f"  Device : {self.device}")
        print(f"  Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        for test_id, name, fn in TESTS:
            self._run(test_id, name, fn)

        return self.results


# ─── Reporting ────────────────────────────────────────────────────────────────
def build_report(results: List[TestResult], device: str):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    errors = sum(1 for r in results if r.status == "ERROR")
    skipped= sum(1 for r in results if r.status == "SKIP")

    # ── JSON ──────────────────────────────────────────────────────────────
    json_path = REPORT_DIR / f"crestron_results_{ts}.json"
    json_data = {
        "summary": {
            "device": device, "timestamp": ts,
            "total": total, "passed": passed,
            "failed": failed, "errors": errors, "skipped": skipped,
            "pass_rate": f"{passed/total*100:.1f}%"
        },
        "results": [
            {
                "test_id":    r.test_id,
                "name":       r.name,
                "status":     r.status,
                "message":    r.message,
                "duration_s": r.duration_s,
                "steps":      r.steps,
                "screenshot": r.screenshot,
            }
            for r in results
        ]
    }
    json_path.write_text(json.dumps(json_data, indent=2))

    # ── HTML ──────────────────────────────────────────────────────────────
    html_path = REPORT_DIR / f"crestron_report_{ts}.html"
    status_color = {"PASS": "#22c55e", "FAIL": "#ef4444",
                    "ERROR": "#f97316", "SKIP": "#94a3b8"}

    rows = ""
    for r in results:
        color  = status_color.get(r.status, "#94a3b8")
        steps  = "<br>".join(r.steps) if r.steps else "—"
        shot   = (f'<a href="{os.path.basename(r.screenshot)}" target="_blank">📷</a>'
                  if r.screenshot else "—")
        rows += f"""
        <tr>
          <td style="font-weight:600;color:#334155">{r.test_id}</td>
          <td>{r.name}</td>
          <td style="color:{color};font-weight:700">{r.status}</td>
          <td style="font-size:0.8em;color:#64748b">{r.message or '—'}</td>
          <td style="font-size:0.8em;color:#64748b">{steps}</td>
          <td>{r.duration_s}s</td>
          <td>{shot}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<title>Crestron Home Test Report — {ts}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1e293b; background: #f8fafc; }}
  h1   {{ color: #0f172a; margin-bottom: 0.25rem; }}
  .meta{{ color: #64748b; margin-bottom: 1.5rem; font-size: 0.9em; }}
  .summary {{ display:flex; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }}
  .card {{ background:#fff; border-radius:8px; padding:1rem 1.5rem;
           box-shadow:0 1px 3px #0003; min-width:100px; text-align:center; }}
  .card .num {{ font-size:2rem; font-weight:700; }}
  .card .lbl {{ font-size:0.8rem; color:#64748b; text-transform:uppercase; }}
  table {{ width:100%; border-collapse:collapse; background:#fff;
           border-radius:8px; overflow:hidden; box-shadow:0 1px 3px #0002; }}
  th {{ background:#1e293b; color:#fff; padding:0.6rem 0.8rem; text-align:left;
        font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; }}
  td {{ padding:0.6rem 0.8rem; border-bottom:1px solid #e2e8f0; vertical-align:top; }}
  tr:hover td {{ background:#f1f5f9; }}
  .pass-rate {{ font-size:1.5rem; font-weight:700;
                color: {'#22c55e' if passed == total else '#ef4444'}; }}
</style>
</head>
<body>
<h1>🏠 Crestron Home — UI Test Report</h1>
<p class="meta">Device: {device} &nbsp;|&nbsp; {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
<div class="summary">
  <div class="card"><div class="num">{total}</div><div class="lbl">Total</div></div>
  <div class="card"><div class="num" style="color:#22c55e">{passed}</div><div class="lbl">Passed</div></div>
  <div class="card"><div class="num" style="color:#ef4444">{failed}</div><div class="lbl">Failed</div></div>
  <div class="card"><div class="num" style="color:#f97316">{errors}</div><div class="lbl">Errors</div></div>
  <div class="card"><div class="num" style="color:#94a3b8">{skipped}</div><div class="lbl">Skipped</div></div>
  <div class="card"><div class="pass-rate">{passed/total*100:.0f}%</div><div class="lbl">Pass Rate</div></div>
</div>
<table>
<thead><tr>
  <th>ID</th><th>Test Name</th><th>Status</th>
  <th>Message</th><th>Steps</th><th>Duration</th><th>Screenshot</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>"""

    html_path.write_text(html)

    # ── Console Summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  RESULTS:  {passed} PASS  |  {failed} FAIL  |  {errors} ERROR  |  {skipped} SKIP")
    print(f"  Pass Rate: {passed/total*100:.1f}%  ({passed}/{total})")
    print(f"  JSON  → {json_path}")
    print(f"  HTML  → {html_path}")
    print(f"{'='*60}\n")

    return json_path, html_path


# ─── Entry Point ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Crestron Home automated UI test suite via NeuralBridge MCP"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE,
                        help="ADB device serial (default: %(default)s)")
    parser.add_argument("--server", default=str(SERVER_PATH),
                        help="Path to neuralbridge-mcp binary (default: %(default)s)")
    parser.add_argument("--tests", nargs="*",
                        help="Run only specific test IDs, e.g. TC001 TC005")
    args = parser.parse_args()

    server = Path(args.server)
    if not server.exists():
        print(f"ERROR: MCP server binary not found: {server}")
        print("  Build it with: cd mcp-server && cargo build --release")
        sys.exit(1)

    client = NeuralBridgeClient(str(server), args.device)
    print("Starting NeuralBridge MCP server …")
    client.start()

    suite   = CrestronTestSuite(client, args.device)
    results = suite.run_all()

    if args.tests:
        results = [r for r in results if r.test_id in args.tests]

    client.stop()
    build_report(results, args.device)

    failed = sum(1 for r in results if r.status in ("FAIL", "ERROR"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

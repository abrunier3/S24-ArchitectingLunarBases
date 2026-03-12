#Test_Scripts/telemetry_dashboard_V9
"""
╔══════════════════════════════════════════════════════════════════╗
║         LUNAR SPACEPORT — TELEMETRY DASHBOARD                   ║
║         Omniverse Kit Script (paste into Script Editor)         ║
╠══════════════════════════════════════════════════════════════════╣
║  1. Open Script Editor:  Window ▶ Script Editor                 ║
║  2. Paste this file in and edit the config block below.         ║
║  3. Press Run (Ctrl+Enter).                                      ║
║  4. Press ▶ Play on the Omniverse timeline — values update.     ║
║  5. Press ■ Stop — dashboard resets to t=0.                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ════════════════════════════════════════════════════════════════════
#  USER CONFIGURATION
# ════════════════════════════════════════════════════════════════════

JSON_FILE_PATH = r"C:\Users\msiddiqui75\Desktop\SoS_Grand_Challenge_Work\Scripts\lunar_spaceport_log.json"

# Real-world seconds of playback per one simulated hour in the JSON.
#   2.0  →  2 s of video = 1 h of sim
#   0.5  →  0.5 s of video = 1 h of sim  (faster)
SECONDS_PER_SIM_HOUR = 2.0

WINDOW_WIDTH  = 680
WINDOW_HEIGHT = 900

# ── ENTITY CONFIG ────────────────────────────────────────────────────
#
# Each entry maps an attribute name to a (display_name, unit) tuple.
#   display_name : human-readable label shown in the dashboard
#   unit         : string appended after the value, e.g. "kg", "kWh", ""
#
# Set SHOW_ALL_ENTITIES = True to auto-discover every entity/attribute
# from the JSON (units will show as "" for all auto-discovered attrs).

SHOW_ALL_ENTITIES = False

ENTITY_CONFIG = {
    "ISRU_Plant": {
        "LOX_Stored":           ("LOX Stored",            "kg"),
        "total_energy_consumed":("Total Energy Consumed",  "kWh"),
        "processing_uptime":    ("Processing Uptime",      "h"),
        "total_LOX_production": ("Total LOX Production",   "kg"),
        "regolith_recieved":    ("Regolith Received",      "kg"),
    },
    "Solar_Power_System": {
        "current_power_output":     ("Power Output",           "kW"),
        "battery_charge":           ("Battery Charge",         "kWh"),
        "battery_capacity":         ("Battery Capacity",       "kWh"),
        "total_energy_generated":   ("Total Energy Generated", "kWh"),
        "total_energy_from_battery":("Energy from Battery",    "kWh"),
    },
    "Power_Manager": {
        "current_energy_demand":    ("Energy Demand",     "kW"),
        "current_energy_production":("Energy Production", "kW"),
    },
    "Habitat-1": {
        "Energy_Consumed_kWh": ("Energy Consumed", "kWh"),
    },
    "CommArray-1": {
        "Energy_Consumed_kWh": ("Energy Consumed", "kWh"),
    },
    "LZ-Alpha": {
        "LOX_Stored":          ("LOX Stored",      "kg"),
        "Energy_Consumed_kWh": ("Energy Consumed", "kWh"),
    },
    "ChargeStation-1": {
        "total_energy_consumed": ("Energy Consumed",  "kWh"),
        "total_energy_delivered":("Energy Delivered", "kWh"),
    },
    "Regolith Cargo Rover": {
        "battery_charge":        ("Battery Charge",    "kWh"),
        "total_distance_traveled":("Distance Traveled","km"),
        "total_energy_consumed": ("Energy Consumed",   "kWh"),
    },
    "LOX Cargo Rover": {
        "battery_charge":        ("Battery Charge",    "kWh"),
        "total_distance_traveled":("Distance Traveled","km"),
        "total_energy_consumed": ("Energy Consumed",   "kWh"),
    },
}

# Attributes to skip when SHOW_ALL_ENTITIES = True.
EXCLUDED_ATTRS = {"Name", "Spike_Events_Array"}

# ════════════════════════════════════════════════════════════════════
#  IMPLEMENTATION — no need to edit below this line
# ════════════════════════════════════════════════════════════════════

import json
import omni.ui as ui
import omni.timeline
import carb

# ── Data helpers ──────────────────────────────────────────────────────

def _fmt(v):
    """Format a number compactly, without any unit suffix."""
    if isinstance(v, bool): return str(v)
    if not isinstance(v, (int, float)): return str(v)
    a = abs(v)
    if a == 0: return "0"
    if a >= 1_000_000: return f"{v/1_000_000:.3f} M"
    if a >= 1_000:     return f"{v/1_000:.2f} k"
    if a < 0.001:      return f"{v:.3e}"
    return f"{v:.3f}"

def _sim_time_label(h):
    hh = int(h)
    mm = int((h - hh) * 60)
    return f"{hh:04d} h  {mm:02d} m"

def _load_data(path):
    """Load JSON, return (sorted_times, snapshots, entity_attr_map).

    entity_attr_map structure:
      SHOW_ALL_ENTITIES=False  →  { entity: { attr: (display_name, unit) } }
      SHOW_ALL_ENTITIES=True   →  { entity: { attr: (attr, "")           } }
    """
    with open(path) as f:
        raw = json.load(f)

    snaps = {}
    for k, v in raw.items():
        try: snaps[float(k)] = v
        except ValueError: pass
    times = sorted(snaps)

    if SHOW_ALL_ENTITIES:
        ea = {}
        for snap in snaps.values():
            for ent, fields in snap.items():
                if ent not in ea: ea[ent] = {}
                if isinstance(fields, dict):
                    for attr, val in fields.items():
                        if attr not in EXCLUDED_ATTRS and attr not in ea[ent]:
                            if isinstance(val, (int, float)) or not isinstance(val, (list, dict)):
                                ea[ent][attr] = (attr, "")
        ea = {e: dict(sorted(a.items())) for e, a in sorted(ea.items())}
    else:
        ea = ENTITY_CONFIG

    return times, snaps, ea

def _snap_at(h, times, snaps):
    if h <= times[0]: return snaps[times[0]]
    lo, hi = 0, len(times) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if times[mid] <= h: lo = mid
        else: hi = mid - 1
    return snaps[times[lo]]

# ── Colours (0xAARRGGBB) ─────────────────────────────────────────────

C_BG           = 0xFF0B1018   # near-black blue
C_SECTION_BG   = 0xFF0F1A2A   # section card background
C_SECTION_HDR  = 0xFF0D2235   # slightly lighter header stripe per section
C_HDR_BG       = 0xFF07101A   # top header bar
C_TIME_BG      = 0xFF081A0E   # sim-time bar
C_ROW_ALT      = 0xFF0D1520   # alternating row tint
C_DIVIDER      = 0xFF152030   # subtle row separator

C_CYAN         = 0xFF00D4FF   # accent / header text
C_CYAN_DIM     = 0xFF0088AA   # dimmer cyan for section titles
C_GREEN        = 0xFF39FF8A   # sim time
C_GREEN_DIM    = 0xFF20A055   # unit suffix
C_ORANGE       = 0xFFFF8C42   # section header entity name
C_YELLOW       = 0xFFFFD166   # attr display name
C_VALUE        = 0xFFEEF4FF   # bright white-ish for values
C_STATUS_OK    = 0xFF39FF8A
C_STATUS_STOP  = 0xFF4A6A85
C_STATUS_PAUSE = 0xFFFFD166
C_FOOTER       = 0xFF3A5570

# ── Dashboard class ───────────────────────────────────────────────────

class LunarTelemetryDashboard:

    def __init__(self):
        self._times, self._snaps, self._ea = [], {}, {}
        try:
            self._times, self._snaps, self._ea = _load_data(JSON_FILE_PATH)
            print(f"[LunarTelemetry] {len(self._times)} timesteps "
                  f"({self._times[0]}–{self._times[-1]} h)")
        except Exception as exc:
            print(f"[LunarTelemetry] ERROR loading JSON: {exc}")

        self._elapsed = 0.0

        # Widget refs updated at runtime
        self._lbl_simtime  = None
        self._lbl_status   = None
        # (entity, attr) → (value_label, unit_label)
        self._lbl_values   = {}

        self._window = None
        self._build_window()

        if self._times:
            self._refresh(0.0)

        tl     = omni.timeline.get_timeline_interface()
        stream = tl.get_timeline_event_stream()
        self._sub_tick  = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.CURRENT_TIME_TICKED,
            self._on_tick,  name="LunarTelemetry_Tick")
        self._sub_play  = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.PLAY,
            self._on_play,  name="LunarTelemetry_Play")
        self._sub_pause = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.PAUSE,
            self._on_pause, name="LunarTelemetry_Pause")
        self._sub_stop  = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.STOP,
            self._on_stop,  name="LunarTelemetry_Stop")
        print("[LunarTelemetry] Ready — press ▶ Play on the Omniverse timeline.")

    # ── Timeline callbacks ────────────────────────────────────────────

    def _on_tick(self, event):
        dt = 1.0 / 60.0
        try:
            dt = float(event.payload.get("dt", dt))
        except Exception:
            pass
        dt = min(max(dt, 0.0), 0.2)
        self._elapsed += dt
        sim_h = self._elapsed / SECONDS_PER_SIM_HOUR
        if self._times:
            max_h = self._times[-1]
            if sim_h >= max_h:
                sim_h = max_h
                self._set_status("● END OF DATA  —  press ■ Stop then ▶ Play to restart",
                                 C_STATUS_PAUSE)
                self._refresh(sim_h)
                return
        self._refresh(sim_h)

    def _on_play(self, event):
        self._set_status("● PLAYING", C_STATUS_OK)
        print("[LunarTelemetry] Playing.")

    def _on_pause(self, event):
        self._set_status("● PAUSED", C_STATUS_PAUSE)
        print("[LunarTelemetry] Paused.")

    def _on_stop(self, event):
        self._elapsed = 0.0
        self._set_status("● STOPPED  —  press ▶ Play on the timeline", C_STATUS_STOP)
        if self._times:
            self._refresh(0.0)
        print("[LunarTelemetry] Stopped. Reset to t=0.")

    def _set_status(self, text, color):
        if self._lbl_status:
            self._lbl_status.text = text
            self._lbl_status.set_style({"color": color, "font_size": 12})

    # ── Display refresh ───────────────────────────────────────────────

    def _refresh(self, sim_h):
        if self._lbl_simtime:
            self._lbl_simtime.text = _sim_time_label(sim_h)
        if not self._snaps:
            return
        snap = _snap_at(sim_h, self._times, self._snaps)
        for (ent, attr), (val_lbl, unit_lbl) in self._lbl_values.items():
            try:
                raw = snap[ent][attr]
                val_lbl.text = _fmt(raw)
            except (KeyError, TypeError):
                val_lbl.text = "—"

    # ── Window construction ───────────────────────────────────────────

    def _build_window(self):
        self._window = ui.Window(
            "⊙  Lunar Spaceport — Telemetry",
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
        )
        self._window.frame.set_style({"Window": {"background_color": C_BG}})

        with self._window.frame:
            with ui.ScrollingFrame(
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            ):
                with ui.VStack(spacing=0):
                    self._build_header()
                    self._build_simtime_bar()
                    self._build_status_bar()
                    ui.Spacer(height=6)
                    for ent, attr_map in self._ea.items():
                        self._build_section(ent, attr_map)
                        ui.Spacer(height=4)
                    ui.Spacer(height=6)
                    self._build_footer()
                    ui.Spacer(height=8)

    # ─── Header ──────────────────────────────────────────────────────

    def _build_header(self):
        with ui.ZStack(height=62):
            ui.Rectangle(style={"background_color": C_HDR_BG})
            with ui.VStack():
                ui.Spacer(height=10)
                ui.Label(
                    "LUNAR SPACEPORT",
                    style={"color": C_CYAN, "font_size": 18},
                    alignment=ui.Alignment.CENTER,
                )
                ui.Spacer(height=3)
                ui.Label(
                    "DES TELEMETRY DASHBOARD",
                    style={"color": C_CYAN_DIM, "font_size": 11},
                    alignment=ui.Alignment.CENTER,
                )
                ui.Spacer(height=8)
        # Thin accent line under header
        with ui.ZStack(height=2):
            ui.Rectangle(style={"background_color": C_CYAN_DIM})

    # ─── Sim-time bar ─────────────────────────────────────────────────

    def _build_simtime_bar(self):
        with ui.ZStack(height=46):
            ui.Rectangle(style={"background_color": C_TIME_BG})
            with ui.HStack():
                ui.Spacer(width=14)
                with ui.VStack():
                    ui.Spacer(height=6)
                    ui.Label(
                        "SIMULATION TIME",
                        style={"color": C_GREEN_DIM, "font_size": 10},
                        alignment=ui.Alignment.LEFT,
                    )
                    ui.Spacer(height=2)
                    self._lbl_simtime = ui.Label(
                        _sim_time_label(0.0),
                        style={"color": C_GREEN, "font_size": 20},
                        alignment=ui.Alignment.LEFT,
                    )
                    ui.Spacer(height=6)

    # ─── Status bar ───────────────────────────────────────────────────

    def _build_status_bar(self):
        with ui.ZStack(height=28):
            ui.Rectangle(style={"background_color": 0xFF080D14})
            with ui.HStack():
                ui.Spacer(width=14)
                self._lbl_status = ui.Label(
                    "● STOPPED  —  press ▶ Play on the timeline",
                    style={"color": C_STATUS_STOP, "font_size": 12},
                    alignment=ui.Alignment.LEFT_CENTER,
                )

    # ─── Entity section ───────────────────────────────────────────────

    def _build_section(self, entity, attr_map):
        """
        attr_map: { attr_key: (display_name, unit) }
        """
        with ui.CollapsableFrame(
            entity,
            collapsed=False,
            style={
                "font_size": 14,
                "color": C_ORANGE,
                "background_color": C_SECTION_BG,
                "secondary_color": C_SECTION_HDR,
                "border_color": C_DIVIDER,
                "border_width": 1,
                "margin": 4,
            },
        ):
            with ui.VStack(spacing=0):
                for i, (attr, (display_name, unit)) in enumerate(attr_map.items()):
                    # Alternate row background — no ZStack, just a plain HStack
                    # with the background set on the HStack style directly so it
                    # fills the full declared height with no gaps or borders.
                    row_bg = C_ROW_ALT if i % 2 == 0 else C_SECTION_BG

                    with ui.HStack(
                        height=34,
                        style={"background_color": row_bg},
                    ):
                        ui.Spacer(width=16)

                        # Attribute display name
                        ui.Label(
                            display_name,
                            style={"color": C_YELLOW, "font_size": 13},
                            width=ui.Percent(48),
                            alignment=ui.Alignment.LEFT_CENTER,
                        )

                        # Value
                        val_lbl = ui.Label(
                            "—",
                            style={"color": C_VALUE, "font_size": 13},
                            width=ui.Percent(28),
                            alignment=ui.Alignment.RIGHT_CENTER,
                        )

                        # Unit suffix
                        unit_lbl = ui.Label(
                            f" {unit}" if unit else "",
                            style={"color": C_GREEN_DIM, "font_size": 12},
                            width=ui.Percent(16),
                            alignment=ui.Alignment.LEFT_CENTER,
                        )

                        ui.Spacer(width=8)

                    # Store both labels
                    self._lbl_values[(entity, attr)] = (val_lbl, unit_lbl)

                ui.Spacer(height=4)

    # ─── Footer ───────────────────────────────────────────────────────

    def _build_footer(self):
        t_max = self._times[-1] if self._times else "?"
        with ui.ZStack(height=22):
            ui.Rectangle(style={"background_color": C_HDR_BG})
            with ui.HStack():
                ui.Spacer(width=14)
                ui.Label(
                    f"{SECONDS_PER_SIM_HOUR} s playback = 1 sim hour   ·   "
                    f"{len(self._times)} timesteps   ·   "
                    f"t_max = {t_max} h",
                    style={"color": C_FOOTER, "font_size": 10},
                    alignment=ui.Alignment.LEFT_CENTER,
                )

    # ── Cleanup ───────────────────────────────────────────────────────

    def destroy(self):
        self._sub_tick  = None
        self._sub_play  = None
        self._sub_pause = None
        self._sub_stop  = None
        if self._window:
            self._window.destroy()
            self._window = None


# ════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════

if "_lunar_dash" in dir():
    try:
        _lunar_dash.destroy()  # noqa
    except Exception:
        pass

_lunar_dash = LunarTelemetryDashboard()
print("[LunarTelemetry] Dashboard launched.")
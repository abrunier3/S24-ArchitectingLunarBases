import omni.ext
import omni.ui as ui
import omni.timeline


SECONDS_PER_SIM_HOUR = 2.0


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] STARTUP")

        self.elapsed_seconds = 0.0
        self.timeline_sub = None

        self.window = ui.Window("LSP1 Pipeline", width=420, height=220)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline loaded.")
                ui.Button("Start Clock Test", clicked_fn=self._start_clock)
                ui.Button("Pause Clock Test", clicked_fn=self._pause_clock)
                self.status = ui.Label("Status: waiting")
                self.time_label = ui.Label("Sim Time: 0.00 hr")

    def _start_clock(self):
        try:
            timeline = omni.timeline.get_timeline_interface()
            stream = timeline.get_timeline_event_stream()

            if not self.timeline_sub:
                self.timeline_sub = stream.create_subscription_to_pop_by_type(
                    omni.timeline.TimelineEventType.CURRENT_TIME_TICKED,
                    self._on_timeline_tick
                )

            timeline.play()
            self.status.text = "Status: clock running"
            print("[LSP1 Pipeline] Clock running")

        except Exception as e:
            self.status.text = f"Status: timeline failed: {e}"
            print("[LSP1 Pipeline] Timeline failed:", repr(e))

    def _pause_clock(self):
        timeline = omni.timeline.get_timeline_interface()
        timeline.pause()
        self.status.text = "Status: paused"

    def _on_timeline_tick(self, event):
        dt = event.payload.get("dt", 0.0)
        self.elapsed_seconds += dt

        sim_hours = self.elapsed_seconds / SECONDS_PER_SIM_HOUR
        self.time_label.text = f"Sim Time: {sim_hours:.2f} hr"

    def on_shutdown(self):
        print("[LSP1 Pipeline] SHUTDOWN")

        self.timeline_sub = None

        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None

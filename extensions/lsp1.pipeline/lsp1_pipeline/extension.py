import omni.ext
import omni.ui as ui


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] STARTUP")

        self.window = ui.Window("LSP1 Pipeline", width=420, height=180)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline loaded.")
                ui.Button("Test ScenarioPlayer Import", clicked_fn=self._test_import)
                self.status = ui.Label("Status: waiting")

    def _test_import(self):
        try:
            from .scenario_player import ScenarioPlayer
            self.player = ScenarioPlayer()
            self.status.text = "Status: ScenarioPlayer import OK"
            print("[LSP1 Pipeline] ScenarioPlayer import OK")
        except Exception as e:
            self.status.text = f"Status: import failed: {e}"
            print("[LSP1 Pipeline] ScenarioPlayer import failed:", repr(e))

    def on_shutdown(self):
        print("[LSP1 Pipeline] SHUTDOWN")
        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None

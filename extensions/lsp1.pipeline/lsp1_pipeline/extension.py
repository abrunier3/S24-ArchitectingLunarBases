import omni.ext
import omni.ui as ui


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] MINIMAL EXTENSION STARTED")
        self.window = ui.Window("LSP1 Pipeline - Minimal Test", width=300, height=120)

        with self.window.frame:
            with ui.VStack():
                ui.Label("LSP1 Pipeline loaded successfully.")

    def on_shutdown(self):
        print("[LSP1 Pipeline] SHUTDOWN")
        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None

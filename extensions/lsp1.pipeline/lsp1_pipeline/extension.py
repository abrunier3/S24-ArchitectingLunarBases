import os
import omni.ext
import omni.ui as ui
import omni.kit.app


class Lsp1PipelineExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id
        self._window = ui.Window("LSP1 Pipeline", width=520, height=260)

        default_manifest = self._default_manifest_path()
        self._manifest_model = ui.SimpleStringModel(default_manifest)

        with self._window.frame:
            with ui.VStack(spacing=10):
                ui.Label("Manifest (JSON)", height=20)
                ui.StringField(model=self._manifest_model)

                with ui.HStack(spacing=10):
                    ui.Button("Build / Open World", clicked_fn=self._on_build)
                    ui.Button("Validate Metadata", clicked_fn=self._on_validate)

                self._status = ui.Label("", height=120)

        self._set_status("Ready.")

    def on_shutdown(self):
        self._window = None

    def _default_manifest_path(self) -> str:
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_path = ext_manager.get_extension_path(self._ext_id)
        repo_root = os.path.normpath(os.path.join(ext_path, "..", ".."))
        return os.path.join(repo_root, "database", "json", "lsp1.json")

    def _set_status(self, msg: str):
        if hasattr(self, "_status") and self._status:
            self._status.text = msg
        else:
            print(msg)

    def _on_build(self):
        try:
            from .builder import build_world_from_manifest
            path = self._manifest_model.get_value_as_string()
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Manifest not found: {path}")
            world = build_world_from_manifest(path)
            self._set_status(f"Built and opened:\n{world}")
        except Exception as e:
            self._set_status(f"ERROR:\n{e}")

    def _on_validate(self):
        try:
            from .builder import validate_metadata
            path = self._manifest_model.get_value_as_string()
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Manifest not found: {path}")
            report = validate_metadata(path)
            self._set_status(report)
        except Exception as e:
            self._set_status(f"ERROR:\n{e}")
import os
import omni.ext
import omni.ui as ui



class Lsp1PipelineExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id
        self._window = ui.Window("LSP1 Pipeline", width=520, height=260, dockPreference=ui.DockPreference.LEFT)

        default_manifest = self._default_manifest_path()
        self._manifest_model = ui.SimpleStringModel(default_manifest)

        with self._window.frame:
            with ui.VStack(spacing=10):
                ui.Label("Manifest (JSON)", height=20)
                ui.StringField(self._manifest_model)

                with ui.HStack(spacing=10):
                    ui.Button("Build / Open World", clicked_fn=self._on_build)
                    ui.Button("Validate Metadata", clicked_fn=self._on_validate)

                self._status = ui.Label("", word_wrap=True, height=120)

        self._set_status("Ready.")

    def on_shutdown(self):
        self._window = None

    def _default_manifest_path(self) -> str:
        # extension folder: .../extensions/lsp1.pipeline
        ext_path = omni.ext.get_extension_path(self._ext_id)
        # repo root assumed two levels up: extensions/lsp1.pipeline -> repo
        repo_root = os.path.normpath(os.path.join(ext_path, "..", ".."))
        return os.path.join(repo_root, "database", "manifests", "lsp1_assets.json")

    def _set_status(self, msg: str):
        self._status.text = msg

    def _on_build(self):
        try:
            path = self._manifest_model.as_string
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Manifest not found: {path}")
            world = build_world_from_manifest(path)
            self._set_status(f"Built and opened:\n{world}")
        except Exception as e:
            self._set_status(f"ERROR:\n{e}")

    def _on_validate(self):
        try:
            path = self._manifest_model.as_string
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Manifest not found: {path}")
            report = validate_metadata(path)
            self._set_status(report)
        except Exception as e:
            self._set_status(f"ERROR:\n{e}")

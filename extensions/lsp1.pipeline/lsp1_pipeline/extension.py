import os
import omni.ext
import omni.ui as ui
import omni.kit.app

from .scenario_player import ScenarioPlayer


class Lsp1PipelineExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id
        self._player = ScenarioPlayer()
        self._playing = False
        self._current_time = 0.0
        self._scenario_duration = 16.0
        self._update_sub = None

        self._window = ui.Window("LSP1 Pipeline", width=620, height=420)

        default_manifest = self._default_manifest_path()
        default_scenario = self._default_scenario_path()

        self._manifest_model = ui.SimpleStringModel(default_manifest)
        self._scenario_model = ui.SimpleStringModel(default_scenario)
        self._time_model = ui.SimpleFloatModel(0.0)

        with self._window.frame:
            with ui.VStack(spacing=8, height=0):
                ui.Label("Manifest (JSON)", height=20)
                ui.StringField(model=self._manifest_model)

                with ui.HStack(spacing=8, height=28):
                    ui.Button("Build / Open World", clicked_fn=self._on_build)
                    ui.Button("Validate Metadata", clicked_fn=self._on_validate)

                ui.Spacer(height=8)
                ui.Line()

                ui.Label("Scenario (JSON)", height=20)
                ui.StringField(model=self._scenario_model)

                with ui.HStack(spacing=8, height=28):
                    ui.Button("Load Scenario", clicked_fn=self._on_load_scenario)
                    ui.Button("Play", clicked_fn=self._on_play)
                    ui.Button("Pause", clicked_fn=self._on_pause)
                    ui.Button("Reset", clicked_fn=self._on_reset)

                ui.Label("Scenario Time (hr)", height=20)
                with ui.HStack(spacing=8, height=28):
                    self._time_drag = ui.FloatDrag(model=self._time_model, min=0.0, max=1000.0)
                    ui.Button("Apply Time", clicked_fn=self._on_apply_time)

                self._status = ui.Label("Ready.", height=140, word_wrap=True)

        # Update loop for playback
        update_stream = omni.kit.app.get_app().get_update_event_stream()
        self._update_sub = update_stream.create_subscription_to_pop(self._on_update, name="lsp1.pipeline.update")

    def on_shutdown(self):
        self._playing = False
        self._player = None
        self._update_sub = None
        self._window = None

    def _default_manifest_path(self) -> str:
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_path = ext_manager.get_extension_path(self._ext_id)
        repo_root = os.path.normpath(os.path.join(ext_path, "..", ".."))
        return os.path.join(repo_root, "database", "json", "world_build", "landing_site_world_build.json")

    def _default_scenario_path(self) -> str:
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_path = ext_manager.get_extension_path(self._ext_id)
        repo_root = os.path.normpath(os.path.join(ext_path, "..", ".."))
        return os.path.join(repo_root, "database", "json", "scenarios", "isru_nominal_temp.json")

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
            self._set_status(f"Built and opened world:\n{world}")
        except Exception as e:
            self._set_status(f"ERROR building world:\n{e}")

    def _on_validate(self):
        try:
            from .builder import validate_metadata
            path = self._manifest_model.get_value_as_string()
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Manifest not found: {path}")
            report = validate_metadata(path)
            self._set_status(report)
        except Exception as e:
            self._set_status(f"ERROR validating metadata:\n{e}")

    def _on_load_scenario(self):
        try:
            path = self._scenario_model.get_value_as_string()
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Scenario not found: {path}")

            self._player.load(path)
            self._playing = False
            self._current_time = 0.0

            # Duration from scenario JSON if present
            self._scenario_duration = float(self._player.scenario.get("duration", 16.0))
            self._time_model.set_value(0.0)

            # Set drag max to scenario duration
            self._time_drag.model.set_max(self._scenario_duration)

            # Apply initial state
            self._player.update(0.0)

            self._set_status(
                f"Scenario loaded:\n{path}\n"
                f"Duration: {self._scenario_duration:.2f} hr\n"
                f"Use Play or drag time and click Apply Time."
            )
        except Exception as e:
            self._set_status(f"ERROR loading scenario:\n{e}")

    def _on_play(self):
        if not self._player or not self._player.scenario:
            self._set_status("Load a scenario first.")
            return
        self._playing = True
        self._set_status(f"Playing scenario at t={self._current_time:.2f} hr")

    def _on_pause(self):
        self._playing = False
        self._set_status(f"Paused at t={self._current_time:.2f} hr")

    def _on_reset(self):
        if not self._player or not self._player.scenario:
            self._set_status("Load a scenario first.")
            return

        self._playing = False
        self._current_time = 0.0
        self._time_model.set_value(0.0)
        self._player.load(self._scenario_model.get_value_as_string())
        self._player.update(0.0)
        self._set_status("Scenario reset to t=0.00 hr")

    def _on_apply_time(self):
        try:
            if not self._player or not self._player.scenario:
                self._set_status("Load a scenario first.")
                return

            self._playing = False
            self._current_time = float(self._time_model.get_value_as_float())
            self._current_time = max(0.0, min(self._current_time, self._scenario_duration))

            # Reload then replay up to selected time so events reapply cleanly
            self._player.load(self._scenario_model.get_value_as_string())
            self._player.update(self._current_time)

            self._set_status(f"Applied scenario time: {self._current_time:.2f} hr")
        except Exception as e:
            self._set_status(f"ERROR applying time:\n{e}")

    def _on_update(self, e):
        if not self._playing:
            return
        if not self._player or not self._player.scenario:
            return

        try:
            # dt is seconds; convert to scenario hours with a temporary speed factor
            dt_seconds = e.payload.get("dt", 0.0) if hasattr(e, "payload") and e.payload else 0.0
            speed_hr_per_sec = 0.5  # temporary playback speed
            self._current_time += dt_seconds * speed_hr_per_sec

            if self._current_time >= self._scenario_duration:
                self._current_time = self._scenario_duration
                self._playing = False

            self._time_model.set_value(self._current_time)
            self._player.update(self._current_time)

            self._set_status(f"Scenario time: {self._current_time:.2f} / {self._scenario_duration:.2f} hr")
        except Exception as e:
            self._playing = False
            self._set_status(f"ERROR during playback:\n{e}")
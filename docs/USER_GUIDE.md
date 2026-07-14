# ECLIPSE Pipeline User Guide

This guide explains how to use the ECLIPSE lunar base pipeline from the browser interface to Omniverse visualization.

## 1. What The Tool Does

The pipeline connects four main steps:

1. The browser interface configures the mission architecture.
2. GitHub Actions parses SysML, updates JSON, converts CAD previews, runs DES, and regenerates USD outputs.
3. The Omniverse manifest collects the latest scene, terrain, waypoints, DES results, and rover playback data.
4. The Omniverse extension loads the generated scene and plays the mission visualization.

The main user-facing files are:

```text
ScenarioIndex.html
clean_database/sysml/<Scenario_Name>.sysml
clean_database/scenarios/<Scenario_Name>.json
clean_database/json/<Scenario_Name>/<Scenario_Name>.json
clean_database/usd/scenes/scene.usda
clean_database/scenes/waypoints.usda
outputs/scenarios/<Scenario_Name>/graph.json
outputs/scenarios/<Scenario_Name>/des_results.json
extensions/lsp1.pipeline/data/manifest.json
```

## 2. Prerequisites

You need:

- a GitHub account with write access to this repository;
- a GitHub Personal Access Token that can dispatch workflows and write repository contents;
- a local clone of the repository if you want to use Omniverse;
- NVIDIA Omniverse or Omniverse Kit with extension support;
- Git installed and visible from Omniverse if you want to use the extension pull button.

For the browser interface, the token is entered when prompted and stored only in the current browser session.

## 3. Branch Consistency

The browser interface dispatches workflows on the branch defined by `GH_REF` in `ScenarioIndex.html`.

The Omniverse extension pull button currently pulls the branch hardcoded in:

```text
extensions/lsp1.pipeline/lsp1_pipeline/extension.py
```

Before running a full end-to-end test, make sure both point to the same branch. Otherwise the browser may generate outputs on one branch while Omniverse pulls another branch.

For the current cleanup test, the browser interface is configured to use:

```text
cleanup-branch
```

Before public release, set the branch back to the branch used by the deployed interface.

## 4. Use The Browser Interface

Open the latest interface:

```text
https://abrunier3.github.io/S24-ArchitectingLunarBases/ScenarioIndex.html
```

If you are testing a non-deployed branch, open the local `ScenarioIndex.html` file or deploy GitHub Pages from that branch.

### Mission Scenario

Click `Start building your mission now` to open the scenario selector. Choose
the ISRU reference, a saved scenario, or `Build New Scenario`. For a new ISRU or
generic scenario, enter its name immediately. The normalized name becomes the
common stem of its configuration and SysML file, and both are preserved on
GitHub. Saved scenarios are loaded from the browser cache and from
`clean_database/scenarios/` in the repository.

### Step 1 - Build Requirements

Use this section to inspect or define the high-level system requirements. These requirements contextualize the mission architecture but do not by themselves run the pipeline.

### Step 2 - Mission Network Activation

Click `Run Graph`.

This triggers:

```text
.github/workflows/run_graph.yml
```

The workflow:

- parses `clean_database/sysml/<Scenario_Name>.sysml`;
- updates `clean_database/json/<Scenario_Name>/`;
- writes `outputs/scenarios/<Scenario_Name>/graph.json`;
- commits the generated files back to the selected branch.

After the graph loads, activate or deactivate the modules you want to keep in the mission scenario.

### Step 3 - CAD Model Submission

For each module that needs a CAD model:

1. Select the module.
2. Upload a USD, USDA, USDC, USDZ, STEP, STP, STL, or OBJ file.
3. Review detected metadata such as material, units, dimensions, up axis, and signed front axis.
4. If metadata is detected from the CAD file, treat it as the source of truth.
5. If metadata is not detected, fill the missing fields manually.
6. Publish the CAD model.

This triggers:

```text
.github/workflows/convert_cad.yml
```

The workflow:

- stores CAD files under `clean_database/cad_models/<ModuleName>/`;
- converts STEP/STP/STL/OBJ inputs into Omniverse-ready USD;
- generates browser preview assets under `outputs/cad_previews/`;
- extracts CAD metadata;
- updates the corresponding asset JSON.

### Step 4 - Urban Planning

Choose the scenario mode, then use the map to place modules and generate routes.

Important behavior:

- fixed modules are placed on the map;
- the number of fixed module instances is selected before placement;
- rovers are mobile actors and are not manually placed like static modules;
- resource-route tools and rover fleets are inferred from active rover ports;
- module equations define resource output, processing time, storage, and event energy;
- SysML power interfaces constrain which consumers are supplied;
- route distances are passed to the DES sliders;
- module positions, orientations, site information, and route waypoints are sent to the DES workflow through the `urban_planning` input.

Confirm the placement before running DES.

### Step 5 - DES Simulation

Adjust the DES parameters, then click `Run DES Simulation`.

This triggers:

```text
.github/workflows/run_des.yml
```

The workflow:

- reads active nodes from the interface or the active scenario graph;
- runs the historical ISRU engine for the ISRU preset;
- compiles Step 4 instances, routes, and equations into generic SimPy processes for a new scenario;
- writes `outputs/scenarios/<Scenario_Name>/des_results.json`;
- updates `clean_database/json/<Scenario_Name>/<Scenario_Name>.json` with urban planning data;
- regenerates `clean_database/usd/scenes/scene.usda`;
- regenerates `clean_database/scenes/waypoints.usda`;
- rebuilds `extensions/lsp1.pipeline/data/manifest.json`;
- commits the generated files back to the selected branch.

If the DES fails, for example because of a power failure, the workflow stops and the latest successful Omniverse manifest may not be updated.

## 5. Install The Omniverse Extension For The First Time

Clone the repository locally:

```bash
git clone https://github.com/abrunier3/S24-ArchitectingLunarBases.git
cd S24-ArchitectingLunarBases
git checkout cleanup-branch
```

For another branch, replace `cleanup-branch` with the branch used by the browser interface.

Open Omniverse, then:

1. Open the Extension Manager.
2. Add this repository's extension search path:

```text
/path/to/S24-ArchitectingLunarBases/extensions
```

3. Search for `LSP1 Pipeline`.
4. Enable the extension.

When the extension loads, a window named `LSP1 Pipeline` should appear.

If it does not appear:

- refresh the Extension Manager;
- disable and re-enable the extension;
- restart Omniverse;
- verify that the search path points to the parent `extensions` folder, not only to `extensions/lsp1.pipeline`.

## 6. Use Omniverse For Visualization

Before opening the visualization, make sure the DES workflow has completed successfully and pushed the generated files.

In the `LSP1 Pipeline` window:

1. Click `Pull GitHub Omniverse`.
2. Wait until the status reports a successful pull.
3. Click `Load DES Playback`.
4. The extension loads:

```text
clean_database/usd/scenes/scene.usda
clean_database/scenes/waypoints.usda
clean_database/scenes/Lunar_surface_v4.usdc
outputs/scenarios/<Scenario_Name>/des_results.json
extensions/lsp1.pipeline/data/manifest.json
```

5. Click `Play` to start the rover playback.
6. Use `Pause` and `Reset` as needed.
7. Use `Show Routes` to display route segments colored by slope severity.

The extension also applies terrain projection data from the manifest:

- terrain placement and scale;
- module ground altitude and local orientation;
- route altitude sampling;
- rover yaw and pitch along the route;
- slope warning and caution counts.

## 7. Generated Files

The following files are generated but intentionally kept because the interface and Omniverse consume them:

```text
outputs/scenarios/<Scenario_Name>/graph.json
outputs/scenarios/<Scenario_Name>/des_results.json
outputs/cad_previews/
clean_database/usd/scenes/scene.usda
clean_database/scenes/waypoints.usda
extensions/lsp1.pipeline/data/manifest.json
```

Do not delete these files during normal use.

## 8. Troubleshooting

### The Interface Runs The Wrong Branch

Check `GH_REF` in `ScenarioIndex.html`.

If it points to the wrong branch, workflows will dispatch to the wrong branch and generated outputs will not match what Omniverse pulls.

### Omniverse Loads Old Results

Check that:

- the DES workflow completed successfully;
- the generated files were committed and pushed;
- the extension pull button pulled the same branch used by the browser interface;
- local changes are not blocking `git pull`.

### The Extension Cannot Load The Scene

Check that these files exist locally:

```text
clean_database/usd/scenes/scene.usda
clean_database/scenes/waypoints.usda
outputs/scenarios/<Scenario_Name>/des_results.json
extensions/lsp1.pipeline/data/manifest.json
```

Also check the Omniverse console for the exact missing file path.

### Routes Do Not Appear

Click `Show Routes`.

If nothing appears, check that `extensions/lsp1.pipeline/data/manifest.json` contains route data and that `clean_database/scenes/waypoints.usda` exists.

### The DES Fails With A Power Error

This means the simulated mission consumed more energy than the active power system could provide. Adjust the DES parameters, such as rover count, haul distance, travel time, processing rate, or power-related architecture choices, then rerun the DES simulation.

### CAD Metadata Looks Wrong

If CAD metadata is detected directly from the uploaded/converted CAD file, it is treated as the source of truth. Manual fields are only fallback values when the CAD file does not provide the metadata.

If scale looks wrong, verify:

- `metersPerUnit`;
- CAD bounding box dimensions;
- SysML module dimensions;
- whether the uploaded USD already contains authored transforms.

## 9. Recommended End-To-End Test

For a clean validation run:

1. Open the browser interface.
2. Run Graph.
3. Confirm the active modules.
4. Upload or verify CAD previews if needed.
5. Place modules in Urban Planning.
6. Confirm placements.
7. Run DES Simulation.
8. Wait for the GitHub Action to complete and push generated files.
9. Open Omniverse.
10. Enable or reload the `LSP1 Pipeline` extension.
11. Pull GitHub from the extension.
12. Load DES Playback.
13. Play the scenario.
14. Toggle Show Routes and verify route colors.

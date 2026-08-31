# ECLIPSE Pipeline User Guide

This guide describes the current ECLIPSE workflow: build an ISRU mission in the browser, run the discrete-event simulation (DES), compare completed scenarios, and replay the result in NVIDIA Omniverse.

## 1. Overview

The workflow has four connected parts:

1. Select or create a scenario and define its mission architecture.
2. Configure placement, rover routes, SysML interfaces, and equations in the four scenario phases.
3. Configure and run the DES, then inspect its results and compare completed scenarios.
4. Load the generated scenario in Omniverse for animated playback, cameras, and live mission telemetry.

The browser interface is available at:

```text
https://abrunier3.github.io/S24-ArchitectingLunarBases/ScenarioIndex.html
```

The interface and Omniverse must use the same Git branch. The current cleanup/testing branch is `cleanup-branch`.

## 2. Before You Start

You need:

- write access to the repository;
- a GitHub Personal Access Token when the browser asks for one; it is kept only for the browser session;
- a local repository checkout and Omniverse Kit or USD Composer to use the Omniverse playback extension;
- Git available to Omniverse if you use the extension's `Pull GitHub Omniverse` button.

Choose a scenario from the mission entry screen:

- `ISRU Scenario` starts from the reference ISRU architecture;
- a saved scenario restores its model and configuration;
- `Build New Scenario` starts from an empty logic model.

New ISRU scenarios start with the reference ISRU CAD assignments. They remain scenario-specific: changing or uploading a CAD in one scenario does not overwrite the CAD selected by another scenario.

## 3. Build the Mission Scenario

Run the graph when prompted after selecting a scenario. The browser loads the active SysML model, its parts, ports, attributes, equations, and available interfaces.

The mission editor is organized into four phases.

### Phase 1: Asset Instancing and Placement

Set the required count for each static module, then place every instance on the terrain map.

- Fixed assets, such as the ISRU plant, excavation unit, depot, power system, habitat, and landing zone, must be placed.
- Rovers are mobile actors. They are assigned to routes rather than placed as fixed modules.
- Use the placement view to inspect terrain constraints and choose viable locations.

### Phase 2: Route Generation

Create the terrain paths that rovers will travel during the DES.

1. Select either `Regolith rover route` or `LOX rover route`.
2. Set the number of rovers in that fleet.
3. Select the origin, any intermediate stops, and the destination in traversal order.
4. Choose the rover assigned to the route and create it.

Terrain routes are operational routes. They determine route distance, terrain slope, rover travel time, and transport energy. The resource-flow arrows shown in the SysML view are only a visual representation of the model's logical flows; they are not additional terrain routes.

A fleet can contain fewer rovers than routes. In that case, the DES uses the available rovers as a shared fleet and a rover becomes available again after completing its route cycle.

Use `Ignore power constraints` in this phase only when you deliberately want an energy-unconstrained simulation. When it is enabled, the DES treats energy as unlimited and ignores power interfaces, demand, supply, and battery failures.

### Phase 3: SysML Interfaces and Equations

This phase displays the active interfaces, rover routes, and equations under their appropriate modules.

- Double-click a module, or use the module equation list, to inspect and edit its equations.
- The equations define the simulated resource, timing, and process behavior. An edited equation is used by the next DES run.
- The graph view is a logical operations diagram. It shows power, LOX, and regolith flows; it is not a terrain map.
- If validation says `No SysML interface available from the active graph`, the active graph does not expose a usable SysML interface for the current scenario. This is separate from visible map links or terrain routes.

For the ISRU reference scenario, system/process constants originate from the SysML model and mission operating settings are configured in the DES panel. The reference scenario remains a safe starting point, but its exposed equations and simulation parameters can be modified for the scenario.

### Phase 4: Scenario Validation

Review the placed instances, terrain routes, SysML interfaces, equations, and power mode before confirming the scenario.

Validation prevents a DES submission when the active architecture is incomplete. Correct the reported missing placement, route, interface, or equation before running the DES. Confirming a scenario does not replace it with a hidden backup scenario: the DES always runs the configuration currently shown in the editor.

## 4. CAD Model Submission

Use the CAD section to associate a model with the selected module instance type.

### Upload, reuse, and storage

For the selected module, you can:

- drag and drop a USD, USDA, USDC, USDZ, STEP, STP, STL, or OBJ file, or click the upload area to choose it;
- select `Upload & Publish selected CAD` to import it into the active scenario;
- choose `Load a CAD from a scenario or the CAD library...` to reuse any published CAD;
- select a CAD from the grouped scenario list or the shared `clean_database/cad_models` library, then click `Load`.

Published CAD is stored under:

```text
clean_database/cad_models/<Scenario_Name>/<Module_Name>/
```

The CAD picker lists only scenarios and assets that actually contain a CAD file. The shared library remains available and is never removed merely because a scenario changes its own selection.

`Save & Publish All` publishes all pending CAD changes. It is useful after uploading several models. A source-front selection is saved immediately; it does not require a separate `Save & Publish All` action before moving to the next phase.

### CAD axes and Omniverse orientation

The preview has two distinct concepts:

- **Source up** is used only for raw CAD inputs such as STEP, STP, STL, and OBJ. Select the source up axis only when the imported source needs to be rebuilt into USD. The interface rebuilds the USD and reports `USD rebuilt as ... Ready for Omniverse` when it completes.
- **Source front** selects the direction the vehicle or asset faces after it is placed in Omniverse. Choose `+X`, `-X`, `+Y`, `-Y`, `+Z`, or `-Z`, except for a direction parallel to the up axis.

For native USD files, the USD stage's up axis is detected automatically by the pipeline. The blue up-axis choice is intentionally not shown for those files. Choose only the source front direction. The front choice is saved to the scenario asset and applied as placement yaw in the generated Omniverse scene.

After changing a raw CAD up axis, wait for the rebuilt-preview status before continuing. After changing a front axis, wait for the saved status. `Run DES` also waits for any pending front-axis saves before dispatching the workflow.

## 5. Configure and Run the DES

After confirming the scenario, configure the DES parameters and select `Run DES Simulation`.

The configuration is organized by operating concern. Important settings include:

- rover transport energy coefficient, payload, flat-terrain speed, and slope speed reduction;
- process throughput, conversion, storage, and dispatch settings;
- power generation, stationary battery capacity, initial stationary battery charge, and module power profiles;
- the `Regolith dispatch check interval`, which is how often the DES checks whether ISRU transport should dispatch a regolith shipment. It is not simply a check for an empty storage bin.

The configured rover speed is the nominal speed on flat ground. The simulation calculates a slower effective speed on sloped terrain:

```text
effective speed = flat speed / (1 + slope penalty x route slope in degrees)
```

The stationary solar battery is different from a rover battery. It stores surplus power generated by the solar power system and supplies the mission during generation deficits. `Initial battery charge [SolarPowerSystem]` is the energy already stored in that stationary battery at mission start; it cannot exceed the configured capacity.

For power-constrained runs, rover and process energy demands are included in the mission power balance. A power failure means the required energy could not be supplied by generation plus available stationary storage. For an energy-unconstrained run, the DES deliberately ignores these constraints.

The workflow writes the DES result, updated scenario data, USD scene, terrain waypoints, and Omniverse manifest. If the DES reports an error, correct the scenario or simulation settings and run it again.

## 6. Inspect Results and Compare Scenarios

The DES page shows the latest scenario's final values and mission time histories. The primary resource for the ISRU reference scenario is LOX.

The `Saved Scenario Comparison` panel compares completed simulations:

1. Select two to four completed scenarios with their checkboxes.
2. Select one of the checked scenarios as `Baseline`.
3. Choose `Final MoEs` or `Time histories`.

`Final MoEs` displays the key outcome values and their percentage change from the selected baseline, including LOX produced and delivered, regolith received, and energy consumed. `Time histories` overlays every selected scenario on the same graph so their trajectories can be compared directly. The selection, baseline, and active view are preserved while you switch between the two views.

## 7. Omniverse Playback

Install the extension once:

1. Clone the repository and check out the same branch used by the browser interface.
2. In Omniverse, open Extension Manager and add the repository's `extensions` directory as an extension search path.
3. Enable `LSP1 Pipeline`.

After a successful DES run:

1. Open the `LSP1 Mission Playback` window.
2. Select the scenario.
3. Click `Pull GitHub Omniverse` to obtain the latest outputs.
4. Start playback with `Play`.

The playback controls support `Pause`, `Reset`, one-hour backward/forward steps, adjustable playback rate, and a mission-position slider. The slider can scrub to an exact moment and supports moving backward in the mission timeline.

The mission dashboard updates during playback with key results such as LOX produced and delivered, LOX at plants, regolith received, power balance, and stationary solar battery state.

Use the camera controls to switch between:

- `Overview`: the full terrain map, with modules and moving rovers visible;
- `Follow Active`: follows the rover currently active in the simulated operation;
- `Rover Chase`: follows the selected rover from behind.

Choose the rover camera target in the extension. The selected-rover telemetry shows its speed, local slope, battery, and payload. `Show Routes` toggles the operational terrain routes and their slope diagnostics.

## 8. Generated Outputs

The following generated files are consumed by the interface or Omniverse and should be retained:

```text
outputs/scenarios/<Scenario_Name>/graph.json
outputs/scenarios/<Scenario_Name>/des_results.json
outputs/cad_previews/<Scenario_Name>/
clean_database/cad_models/<Scenario_Name>/
outputs/scenarios/<Scenario_Name>/omniverse/scene.usda
outputs/scenarios/<Scenario_Name>/omniverse/waypoints.usda
outputs/scenarios/<Scenario_Name>/omniverse/manifest.json
```

Do not delete these files as part of normal scenario use. The CAD library at `clean_database/cad_models/` also contains reusable reference assets outside a scenario folder.

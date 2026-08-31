# ECLIPSE Pipeline User Guide

This guide follows the browser interface from top to bottom. Complete the steps in this order to build, run, inspect, and visualize a mission scenario.

The browser interface is available at:

```text
https://abrunier3.github.io/S24-ArchitectingLunarBases/ScenarioIndex.html
```

You need repository write access and a GitHub Personal Access Token. The interface asks for the token when it needs to run or publish a workflow and keeps it only for the current browser session.

## 1. Choose a Mission Scenario

At the top of the page, open **Mission Scenario** and choose one option:

1. **ISRU Scenario**: starts from the validated ISRU reference model.
2. **Saved Scenarios**: restores an existing configuration and its current settings.
3. **Build New Scenario**: starts from an empty logic model.

Enter a name for a new scenario. The name identifies its SysML model, configuration, CAD assignments, DES results, and Omniverse package.

For a new ISRU scenario, the base ISRU CAD models are already assigned. CAD remains scoped to the scenario: uploading or selecting a model in one scenario does not change another scenario's CAD selection.

## 2. Build Requirements

The **1. Build Requirements** section is the entry point for defining the high-level requirements and interfaces in MSOSA. Use it before activating the mission network when requirements work is needed. The mission can only use the systems, ports, and attributes available in its SysML model.

## 3. Activate the Mission Network

In **2. Mission Network Activation**:

1. Click **Run Graph**.
2. Wait for the graph to load.
3. Turn the required modules on or off in **Activate Systems**.
4. Check the **Mission Operations Graph** to confirm the expected power, LOX, and regolith flows.

The graph is a logical SysML view, not a terrain route map. It determines which systems, ports, interfaces, and equations are available in the downstream mission builder and DES.

### Ignore power constraints

Use the **Ignore power constraints** checkbox only when you intentionally want an energy-unconstrained run. After enabling it and running the DES, the simulation treats energy as unlimited and ignores power supply, demand, power interfaces, battery depletion, and power failures.

Leave it disabled for a power-constrained simulation. In that mode, power generation and the stationary solar battery must cover the rover and process energy demand.

## 4. Submit CAD Models

In **3. Model Submission**, select a module from the left-hand list. For each module, choose one of these paths:

1. Drag and drop a USD, USDA, USDC, USDZ, STEP, STP, STL, or OBJ file into the upload area, or click the area to browse.
2. Click **Upload & Publish selected CAD**.

Or reuse a model that already exists:

1. Open **Load a CAD from a scenario or the CAD library...**.
2. Choose a model from a scenario group or from the shared CAD library.
3. Click **Load**.

The CAD picker shows only scenarios and assets that actually contain a CAD file. The shared CAD library at `clean_database/cad_models/` is also available. Use **Save & Publish All** after uploading several models; it publishes every pending CAD change.

### Set CAD orientation

Use the preview panel to configure the source axes before visualization.

- For **STEP, STP, STL, and OBJ** files, select the correct **Source up** axis if the raw source needs reorientation. The interface converts the file again and reports `USD rebuilt as ... Ready for Omniverse` when finished. Wait for that confirmation.
- For **USD, USDA, USDC, and USDZ** files, the pipeline automatically detects the USD up axis. No blue up-axis control is shown. Select only the **Source front** direction.

The source front indicates the direction the model faces in Omniverse. Choose `+X`, `-X`, `+Y`, `-Y`, `+Z`, or `-Z`; a direction parallel to the source up axis is unavailable. The front choice saves immediately and the DES waits for any pending save before it starts. You do not need to press **Save & Publish All** solely after changing the front direction.

## 5. Select the Site

In **4. Urban Planning - Site Selection & Mission Scenario Builder**, first use **Step 4.1 - Site Selection**:

1. Select a site pin on the map.
2. Review its terrain and illumination information.
3. Select the site for the scenario.

Then open **Step 4.2 - Mission Scenario Builder**.

## 6. Build the Terrain Mission

Step 4.2 contains four tabs. Work through them from left to right.

### Phase 1: Asset Instancing and Placement

1. Set the number of instances for each fixed module.
2. Select an instance in the left panel.
3. Place it on the map.
4. Repeat until every required fixed module is placed.

ISRU plants, excavation units, the propellant depot, power systems, habitats, and landing zones are fixed modules. Rovers are mobile actors and are assigned to routes instead of being placed on the map.

### Phase 2: Route Generation

Create the terrain paths that each rover uses during the simulation:

1. Choose **Regolith rover route** or **LOX rover route**.
2. Set the fleet count for that rover type.
3. Select origin, optional intermediate stops, and destination in traversal order.
4. Choose the rover assigned to the route.
5. Click **Create rover route**.

These are the actual operational terrain routes. Their geometry determines distance, measured slope, travel time, and transport energy in the DES and in Omniverse.

The LOX, regolith, and power arrows visible in the logic view are only resource-flow visuals. They do not create extra terrain paths. A fleet can contain fewer rovers than terrain routes: the DES then uses the available rovers as a shared fleet and reuses a rover after it completes its route cycle.

### Phase 3: SysML Interfaces and Equations

This tab shows active rover routes, SysML interfaces, and module equations.

- Double-click a placed module, or use the module equation list, to inspect or edit equations.
- An edited equation is used by the next DES run.
- Use the route lists to review the rover routes created in Phase 2.

If validation reports **No SysML interface available from the active graph**, the active SysML graph does not expose a usable interface for the scenario. It does not mean that a terrain route or a visible map link is missing.

### Phase 4: Scenario Validation

Review the active modules, placements, routes, interfaces, equations, and power mode. Fix every error reported by validation, then click **Confirm Scenario**.

Confirming does not switch to a hidden backup scenario. The next DES run uses the scenario you configured in the interface.

## 7. Configure and Run the DES

In **5. Mission Tradespace Selection (DES)**, configure the mission operating parameters, then click **Run DES Simulation**.

Important controls include:

- rover payload, transport-energy coefficient, flat-terrain speed, and slope speed reduction;
- ISRU throughput, conversion, storage, and dispatch behavior;
- generation power, stationary battery capacity, initial battery charge, and module power consumption;
- **Regolith dispatch check interval**, which is how often the DES checks whether regolith transport should dispatch a shipment. It is not only a check for an empty storage bin.

The configured rover speed is the speed on flat terrain. The DES slows it down for sloped terrain:

```text
effective speed = flat speed / (1 + slope penalty x route slope in degrees)
```

The solar battery belongs to the stationary solar power system. It stores surplus generated energy and supplies the mission when generation is insufficient. **Initial battery charge [SolarPowerSystem]** is the amount stored in that stationary battery at the beginning of the mission; it cannot exceed its capacity.

For a normal power-constrained run, a power failure means generation plus stationary battery storage could not meet the energy required by the mission. Correct the architecture or the DES parameters and run it again.

## 8. Read Results and Compare Completed Scenarios

After the DES completes, the page displays the scenario's metrics and mission time histories. For the reference ISRU scenario, the primary resource is LOX.

Use **Saved Scenario Comparison** to compare two to four completed scenarios:

1. Select the scenarios with the checkboxes.
2. Select one checked scenario as **Baseline**.
3. Click **Final MoEs** to compare final values and percentage changes relative to the baseline.
4. Click **Time histories** to see the selected scenarios overlaid on the same graphs.

The comparison focuses on mission outcomes such as LOX produced and delivered, regolith received, and energy consumed.

## 9. Replay the Scenario in Omniverse

Install the `LSP1 Pipeline` extension once by adding this repository's `extensions` folder to Omniverse Extension Manager and enabling the extension. The local repository branch must match the one used by the browser interface.

After a successful DES run:

1. Open **LSP1 Mission Playback** in Omniverse.
2. Click **Pull GitHub Omniverse**.
3. Select the scenario from the scenario list.
4. Click **Play**.

Use **Pause**, **Reset**, **Back 1 hr**, **Forward 1 hr**, the playback-rate slider, and the **Mission position** slider to control the simulation. The mission-position slider can move backward or jump to an exact moment.

The dashboard updates during playback with LOX, regolith, power, and stationary battery results. The camera controls provide:

- **Overview** for the full map with highlighted modules and moving rovers;
- **Follow Active** for the rover currently operating in the DES;
- **Rover Chase** for a behind-the-rover view of the selected camera target.

Select a rover in **Rover camera target** to see its live speed, local slope, battery, and payload. Use **Show Routes** to display operational terrain routes and their slope diagnostics.

## 10. Generated Scenario Data

Each successful run creates and updates scenario-specific data. Do not delete these files during normal use:

```text
outputs/scenarios/<Scenario_Name>/graph.json
outputs/scenarios/<Scenario_Name>/des_results.json
outputs/scenarios/<Scenario_Name>/omniverse/scene.usda
outputs/scenarios/<Scenario_Name>/omniverse/waypoints.usda
outputs/scenarios/<Scenario_Name>/omniverse/manifest.json
outputs/cad_previews/<Scenario_Name>/
clean_database/cad_models/<Scenario_Name>/
```

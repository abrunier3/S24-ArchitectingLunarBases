# ECLIPSE Pipeline Demonstration Script

**Target duration:** 22 to 24 minutes  
**Narrative:** start from an ISRU architecture, turn it into an operational mission scenario, simulate it, compare results, and replay it in Omniverse.

This is a spoken script. **On screen** tells you what to do in the interface; **Behind the scenes** explains what the pipeline is doing.

## Preparation Before the Demonstration

Complete these checks before presenting:

- Open `ScenarioIndex.html` in a browser already authenticated with the GitHub token.
- Prepare one ISRU demonstration scenario with its graph loaded, CAD visible, site selected, modules placed, and routes created.
- Keep a second completed ISRU scenario available for the comparison view.
- Open GitHub Actions in a second tab on the same branch used by the interface.
- Open Omniverse with the `LSP1 Pipeline` extension enabled and the demonstration scenario available in its scenario list.
- Keep one browser tab on the DES comparison section and one window on Omniverse, so the audience never has to wait for a GitHub Action to finish.

During the presentation, trigger the actions to show that the pipeline is real. Then use the already-completed scenarios to show results, comparison, and Omniverse immediately.

---

## 0:00-1:30 | Introduction

**On screen:** Show the landing page, then scroll to **Mission Scenario**.

**Say:**

> I am going to show the complete ECLIPSE pipeline. The goal is to move from a lunar mission architecture, expressed in SysML and configured by a user, to a discrete-event simulation, and finally to a 3D visualization in Omniverse.
>
> The interface is organized as a design journey. We choose or create a scenario, activate the systems that compose it, associate CAD models, place assets and routes on terrain, configure the simulation, then analyze and visualize the result.
>
> The case I will use is an ISRU mission. We excavate regolith, transport it to an ISRU plant, produce LOX, and deliver that LOX to a propellant depot.

**Behind the scenes:**

> All data remains tied to one scenario identifier. That identifier links the SysML model, configuration, selected CAD, DES results, and Omniverse package.

## 1:30-3:00 | Choose a Starting Point

**On screen:** Show the three cards: **ISRU Scenario**, **Saved Scenarios**, and **Build New Scenario**. Choose the ISRU scenario or load the prepared demonstration scenario.

**Say:**

> The user has three ways to start. The first is the ISRU reference scenario: it loads a validated architecture with modules, ports, equations, and simulation assumptions. The second restores a saved scenario. The third starts from an empty logic model, for a fully new mission architecture.
>
> For this demonstration I will start from the ISRU scenario. It is important to understand that this is not a fixed simulation. It is a starting point that the user can change: for example, the number of plants, routes, equations, power parameters, or CAD models.

**Behind the scenes:**

> A new ISRU scenario copies the reference configuration. Its CAD assignments are also initialized from the reference, but they become scenario-specific. Changing a rover CAD in this scenario does not overwrite the rover used by another scenario.

## 3:00-4:00 | Requirements and SysML Model

**On screen:** Scroll to **1. Build Requirements**. Point to the MSOSA button without opening it for long.

**Say:**

> This first section connects high-level requirements and interfaces to the architecture. Those elements are defined in the MBSE environment and represented in SysML. The web interface does not replace the system model; it makes that model usable for mission configuration and simulation.
>
> The key point is that the modules, attributes, ports, and interfaces shown later in the workflow are not invented by the interface. They come from the active SysML model.

## 4:00-6:30 | Activate the Mission Network and Build the Graph

**On screen:** Go to **2. Mission Network Activation**. Show active modules, the **Ignore power constraints** toggle, and click **Run Graph**. Briefly show the GitHub Actions tab, then return to the prepared graph.

**Say:**

> Step 2 turns the SysML model into an operational mission graph. Here, I choose which systems are active: for example excavation, the ISRU plant, rovers, the depot, and the solar power system.
>
> I now click `Run Graph`. The graph on the right shows logical relations: red for power, blue for LOX, and yellow for regolith. This is not yet a terrain route map. It is a graph of SysML flows and interfaces.

**Behind the scenes:**

> This click triggers a GitHub Action. It parses the scenario SysML file, produces JSON for parts and assets, computes connectivity, and writes a scenario-specific `graph.json`. The browser then reloads that graph to display the modules and connections.

**Say:**

> This is also where we can enable `Ignore power constraints`. If selected, the scenario intentionally runs with unlimited energy: the DES ignores power sources, demand, interfaces, battery depletion, and power failures. That is useful when studying only logistics. For a realistic run, I keep it unchecked so power constrains the mission.

## 6:30-9:30 | Assign CAD Models and Orientation

**On screen:** Go to **3. Model Submission**. Select a rover, show the preview, show the library menu, and show the front-axis controls. Do not upload a file live unless needed; show an existing CAD and the drag-and-drop area.

**Say:**

> Step 3 manages CAD models. For every module, the user can upload a USD, STEP, STL, or OBJ file directly, or reuse a CAD that was published by another scenario or added to the shared library.
>
> The important design choice is that CAD belongs to a scenario. We can therefore test a new rover design in a trade study without changing the reference scenario or any other scenario.

**On screen:** Open **Load a CAD from a scenario or the CAD library...** and show the grouped choices. Close it afterwards.

**Say:**

> This picker is organized in two parts: scenarios that contain CAD, and the shared CAD library. It does not show misleading choices: an asset without CAD in a scenario is simply not listed.

**On screen:** Show **Source front**. If a STEP file is available, show **Source up**; otherwise explain it without changing values.

**Say:**

> Orientation is the other important topic. For a native USD file, the pipeline detects the vertical axis from the file itself. The user therefore only selects the source front direction, for example `+X` or `+Y`, which determines how the vehicle faces in Omniverse.
>
> For raw files such as STEP or STL, the user can also correct the source up axis. The pipeline then reconverts the CAD into USD and regenerates the preview. The status confirms when the USD is ready for Omniverse.

**Behind the scenes:**

> Uploading or reconverting CAD triggers a second GitHub Action. It converts CAD to USD and GLB, extracts metadata, and creates a web preview. Published files are stored in the scenario folder, while the selected front axis is saved in the asset metadata.

## 9:30-11:00 | Select the Mission Site

**On screen:** Go to **4. Urban Planning**, open **Step 4.1 - Site Selection**, click a site pin, and select the site.

**Say:**

> We now move from the logical model to the physical context. In the first urban-planning step, I select the lunar site. The interface provides terrain and illumination information to help choose a location compatible with the mission.
>
> This choice becomes part of the scenario. It affects module positions, route length, and the slopes that rovers will have to cross.

## 11:00-15:30 | Build the Terrain Mission

**On screen:** Open **Step 4.2 - Mission Scenario Builder**. Move through the four tabs from left to right. Use the prepared scenario rather than placing every asset live.

### 11:00-12:15 | Phase 1: Asset Instancing and Placement

**Say:**

> In Phase 1, I set the number of instances and place fixed assets: excavation, the ISRU plant, the depot, solar power, habitat, and landing zone. Each instance receives a position on the map.
>
> Rovers are different. They are mobile actors, so they are not placed at a fixed point. They are assigned to routes in the next phase.

### 12:15-13:45 | Phase 2: Rover Route Generation

**On screen:** Switch to **Phase 2 - Route Generation**. Show one regolith route and one LOX route, their rover counts, and the route list.

**Say:**

> This phase creates the real operational terrain routes. For regolith, we go from excavation to the ISRU plant. For LOX, we go from the ISRU plant to the propellant depot. Intermediate stops can also be added.
>
> A route is not only for animation. Its distance and slope profile are sent to the DES. They affect travel time, effective speed, and transport energy.

> The rover number is a fleet size, not necessarily the number of routes. If there are fewer rovers than routes, the DES uses a shared fleet. A rover becomes available again after it completes its route cycle.

### 13:45-14:45 | Phase 3: SysML Interfaces and Equations

**On screen:** Switch to **Phase 3 - SysML Interfaces & Equations**. Show routes in the left panel, then open one module equation.

**Say:**

> This phase makes active SysML interfaces and equations visible under their appropriate modules. LOX, regolith, and power lines are logical resource flows. They are not additional terrain routes; the physical routes were defined in the previous phase.

> The user can open and edit an equation. That modification becomes part of the next simulation. For example, an equation can define production throughput, processing time, or energy consumption.

### 14:45-15:30 | Phase 4: Scenario Validation

**On screen:** Switch to **Phase 4 - Scenario Validation**, show the counters, and click **Confirm Scenario** if it is not already confirmed.

**Say:**

> Finally, validation checks whether the scenario can run: modules are placed, routes are coherent, interfaces are available, equations are present, and the power mode is known. If the interface reports that no SysML interface is available, it means the active graph does not provide the required interface. It is not a missing line on the map.

> Once confirmed, this exact configuration is sent to the DES. There is no hidden backup scenario replacing it in the background.

## 15:30-18:30 | Configure and Run the DES

**On screen:** Go to **5. Mission Tradespace Selection (DES)**. Show transport controls, then power and battery controls. Change a non-critical value, such as flat-terrain speed, and click **Run DES Simulation**. Show the submission status, then open already-computed results.

**Say:**

> The DES converts the architecture into behavior over time. I can configure transport parameters, capacities, process rates, storage, generation power, demand profiles, and stationary battery settings.

> Take rover speed as an example. The value configured here is speed on flat terrain. The actual speed is reduced when the route becomes steeper, so a route changes both the geometry and the mission schedule.

> We can also configure the regolith dispatch check interval. This is not simply an "empty storage" condition. It defines how frequently the simulation checks whether ISRU transport should dispatch a new regolith shipment.

**On screen:** Point to **Generation power**, **Battery capacity**, and **Initial battery charge**.

**Say:**

> The solar battery here belongs to the stationary power system. It stores surplus generation and covers power deficits. Initial battery charge is the energy already stored at mission start. It is separate from a rover's own battery.

**Behind the scenes:**

> When I click `Run DES Simulation`, the browser first saves any pending CAD orientation selection. It then sends the scenario configuration, routes, placements, equations, and slider values to GitHub Actions. The pipeline runs the discrete-event engine, writes the results, and builds the Omniverse package: USD scene, waypoints, and manifest.

**Say:**

> In a power-constrained run, a power failure means that generation plus available stationary battery could not satisfy mission demand. This is a useful result: it tells us that the architecture or operating parameters must change. For the rest of the demonstration, I will open an execution that has already completed.

## 18:30-20:30 | Read Results and Compare Scenarios

**On screen:** Show the completed scenario metrics and time histories, then **Saved Scenario Comparison**. Select two scenarios, choose a baseline, click **Final MoEs**, then **Time histories**.

**Say:**

> The results provide final values and time histories. In this ISRU mission, LOX is the primary resource. We can track production, the amount delivered to the depot, regolith received, and energy consumed.

> Comparison does not force the user to inspect one scenario at a time. I select two to four completed scenarios, then choose one as the baseline. Percentage changes are calculated against that baseline.

> In `Final MoEs`, we compare the key outcome values directly. In `Time histories`, the selected scenarios are overlaid on the same graph. This is useful not only to see which scenario ends with the best result, but also when and why their trajectories begin to diverge.

## 20:30-23:30 | Replay the Mission in Omniverse

**On screen:** Switch to Omniverse. Open **LSP1 Mission Playback**, select the scenario, click **Pull GitHub Omniverse** if needed, and click **Play**. Show cameras, the time slider, and telemetry.

**Say:**

> The final step is the 3D visualization. The Omniverse extension loads the package produced by the DES for the selected scenario: terrain, scene, waypoints, actors, and time-dependent simulation results.

> I can play, pause, move backward or forward by one hour, change playback rate, and jump to an exact instant with the mission-position slider. The visualization is not an independent animation. It replays the simulation state.

**On screen:** Select **Overview**.

**Say:**

> Overview gives the full terrain map, with fixed modules and moving rovers visible together.

**On screen:** Select a rover, then show **Rover Chase** and **Follow Active**. Point to telemetry.

**Say:**

> I can select a rover as the camera target. Rover Chase follows it from behind, while Follow Active follows the actor that is currently performing an operation in the DES. The telemetry displays the selected rover's speed, local slope, battery, and payload.

> Finally, `Show Routes` displays the actual operational terrain routes and their slope diagnostics. This closes the loop between a route chosen in the interface, its effect in the DES, and its 3D representation.

## 23:30-24:30 | Conclusion

**On screen:** Return to an Omniverse overview or the scenario comparison.

**Say:**

> To summarize, ECLIPSE connects three levels that are often separate: the SysML system model, operational mission configuration, and simulation with 3D visualization.
>
> The user remains in control of assets, CAD, routes, equations, and simulation parameters. In return, the pipeline provides comparable quantitative results and a spatial and temporal view of the mission in Omniverse.

> The key idea is traceability: the scenario configured in the browser is the scenario that is simulated and visualized.

---

## Shorter 20-Minute Version

If you need to fit the demonstration into 20 minutes, reduce the CAD and site sections to one minute each. Keep the graph activation, route/equation configuration, DES, comparison, and Omniverse sections. Do not wait for a GitHub Action live: show the dispatch, then switch to a scenario that has already completed.

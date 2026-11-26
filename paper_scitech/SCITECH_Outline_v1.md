# ECLIPSE SciTech paper outline

Integrated scenario definition simulation and visualization

Version 1 | 18 November 2026

The paper presents the complete ECLIPSE environment for collaborative lunar base architecting. Its central contribution is a shared scenario definition that connects specialist contributions, architectural choices, operational assumptions, quantitative results, and spatial inspection. The original ecosystem and the AE 8900 developments belong in one technical account of the delivered system.

Retain the seven main sections of the ECLIPSE paper. Expand the behavior engine, CAD integration, scenario persistence, and visualization within that structure. Describe collaboration through contributions at connected engineering steps and through versioned artifacts. Present automation, flexibility, and coherence as properties supported by specific demonstrations.

## Abstract

- Establish the engineering problem: interdependent lunar infrastructure must be designed by specialists using heterogeneous models and tools.
- Introduce ECLIPSE and its connected workflow from system definition and requirements to site planning, operational simulation, verification, and visualization.
- Explain the principal capabilities: configurable scenario architecture and equations; an initial generic behavior framework; CAD conversion with metadata write-back; saved scenario comparison; and scenario-specific Omniverse playback.
- Summarize the demonstrations and include numerical findings only after the current simulation campaign has been completed and checked.
- End with the demonstrated scope. Distinguish the configurable ISRU application from the initial extension to other resource chains.

## I Introduction

### A Background

- Introduce sustained lunar infrastructure as a system of interdependent habitats, power, communications, processing facilities, storage, and transport assets.
- Explain why these systems involve different technical specialties and organizations. Connect their operational dependencies to the need to integrate their contributions.
- Use the lunar spaceport as the concrete design problem. Establish the coupled effects of placement, terrain, resource access, logistics, and power.
- Keep lunar program context brief and supported by current primary sources. Replace broad judgments about Apollo-era engineering with a precise description of the present integration problem.

### B Motivation

- Paragraph 1: begin from the collaboration need established in Background. Explain the resulting exchange of heterogeneous data, competing model versions, and alternative system configurations. Treat controlled information sharing as a need; describe its implemented support later.
- Paragraph 2: establish that mission objectives change system types, quantities, connections, operating laws, and terrain layouts. Then derive the need for a modular, configurable, extensible workflow that preserves its assumptions between iterations.
- Paragraph 3: motivate explicit visualization of the simulated mission through time. Explain what spatial placement, rover movement, resource histories, and synchronized telemetry help stakeholders inspect alongside numerical measures of effectiveness.
- Paragraph 4: introduce model-based digital engineering as a relevant approach to connecting these activities. Leave the assessment of published methods and their demonstrated benefits to Section II.

<!-- page -->

## II Problem formulation

### A Literature review

Organize the review by engineering approach. Within each group, compare the problem addressed, representation used, demonstrated strengths, integration boundary, and implications for the present work. Synthesize relationships between studies rather than allocating one descriptive paragraph to each reference.

**Group 1 Lunar system architecture and multidisciplinary trade studies.** Review system-of-systems studies and parametric or MBSE-linked sizing methods. Candidate starting points in the supplied bibliography include the Cislunar Architecture Study and the ISRU and power-system studies by Boyer, Ramkumar, and Mehta. Assess how they connect architectural decisions to performance, what they demonstrate about trade exploration, and which operational or integration questions remain outside their reported scope.

**Group 2 Operational modeling and scenario construction.** Review lunar logistics and surface-operations environments, followed by configurable or composable simulation approaches. The tabletop study and MORPH, DELOS, and PIONEER are starting points whose actual reports must be inspected. Compare event logic, resource contention, scenario input languages, user responsibility, and the effort required to express a different resource chain. SimPy documentation explains the implementation framework; it cannot establish novelty relative to other simulation environments.

**Group 3 Digital engineering integration and collaboration.** Review authoritative models, digital threads, model exchange, provenance, and collaboration across specialist tools. Separate standards and strategy documents from evaluated implementations. Compare the data contracts, versioning, and change propagation actually demonstrated. Distinguish asynchronous artifact contributions from simultaneous editing of a shared application state.

**Group 4 Spatial planning and simulation visualization.** Review GIS-informed infrastructure planning, simulation-linked 3D environments, and the role of scene interoperability. Compare coordinate consistency, terrain provenance, geometry association, time synchronization, and scenario regeneration. Use OpenUSD and Omniverse documentation to substantiate technical capabilities; assess engineering benefits through application evidence. An operationally synchronized physical counterpart is a different claim from a design-stage simulation playback.

**Cross-cutting comparison criteria.** Examine architecture traceability, configurable operational behavior, geometric and metadata interoperability, terrain and time consistency, scenario preservation, and contributor workflow. For each candidate study, distinguish an explicitly demonstrated capability from one not described in the inspected source. Absence from a publication is not proof that a capability does not exist.

**Review output.** Build a compact comparison matrix and a synthesis paragraph explaining how the approaches complement one another. Use that synthesis to derive the specific integration problem addressed by ECLIPSE. Audit the supplied references for accurate titles, identifiers, dates, and relevance; expand the review beyond the existing Georgia Tech examples where the evidence warrants it.

### B Research gap

- Formulate a bounded integration gap: preserving a consistent, inspectable scenario definition across architecture, spatial planning, configurable operations, heterogeneous geometry, and quantitative and visual assessment.
- Separate limitations documented in prior publications from limitations observed in the original ECLIPSE prototype. A prototype limitation alone does not establish a field-wide research gap.
- Scope the novelty claim to the combination and implementation demonstrated in this paper. Finalize its wording after the comparative literature assessment.

<!-- page -->

### C Objectives and research questions

**Objective.** Develop and demonstrate an integrated digital engineering environment in which specialists contribute to a shared lunar mission definition, configure supported operational scenarios, preserve their assumptions and outputs, and evaluate alternatives quantitatively and spatially.

**RQ1 Scenario configurability and extensibility.** How can a common architecture representation support user-visible mission configuration and executable operational behavior across the ISRU reference case and additional resource-chain scenarios?

**RQ2 Interoperability and traceability across contributions.** How can system models, spatial data, CAD assets, operational assumptions, and results be connected while preserving scenario identity, data authority, and contribution provenance?

**RQ3 Coherent mission evaluation.** How can quantitative simulation outputs be connected to spatial placement, terrain, rover motion, and recorded-time telemetry so that stakeholders can inspect and compare the same mission scenario?

### D Contributions and evaluation strategy

- **C1 Integrated ecosystem architecture:** a functional decomposition and digital thread connecting requirements and system definition, selection, GIS planning, operational simulation, verification, CAD, visualization, and contributor workflows.
- **C2 Configurable behavior modeling:** a transparent ISRU configuration with visible equations and parameters, plus an initial role-based description and compiler for additional supported resource chains.
- **C3 Engineering geometry integration:** supported CAD formats standardized into visualization assets, with separate source and visualization metadata and controlled enrichment of the authoritative SysML model.
- **C4 Preserved and inspectable scenarios:** named scenario configurations, result comparison against a selected baseline, and scenario-specific Omniverse packages with terrain-aware placement and synchronized playback telemetry.

Link RQ1 to Section IV.D and the ISRU and generic demonstrations. Link RQ2 to artifact provenance, CAD write-back, and saved scenario identity. Link RQ3 to the quantitative comparison and Omniverse consistency demonstrations. These contributions explain the complete system; they do not claim that each constituent technology is new.

### Editorial rules for the merged paper

- Present the final tool directly. Retain a short historical comparison only when it clarifies a measured capability or a design rationale.
- Describe requirements as guiding architecture and evaluation. Do not imply automatic synthesis of arbitrary mission architectures or a global optimization process unless such a process is demonstrated.
- Use collaboration to describe connected specialist contributions and the implemented versioned workflow. Claims about access control, intellectual-property protection, conflict prevention, and simultaneous editing require separate evidence.
- Describe visualization as complementary to quantitative analysis. Do not claim universal stakeholder comprehension or improved decision quality without an evaluation of those outcomes.

<!-- page -->

## III Architecture

### A Engineering needs and architectural requirements

- Derive requirements for interoperable data exchange, scenario configurability, extensibility, traceability, spatial and temporal consistency, and contributions from different specialties.
- Define the scope of each requirement and an observable acceptance criterion. For example, a saved scenario must retain the configuration and identify the outputs used for its playback.
- Distinguish architectural objectives from capabilities already demonstrated by the prototype. In particular, collaboration support does not automatically imply concurrent application sessions.

### B Functional decomposition

For each block, give its purpose, rationale, required inputs, outputs, and relationship to the other blocks. Keep algorithms, libraries, detailed equations, filenames, and user-interface controls in Section IV.

1. **Authoritative Source of Truth:** defines systems, reference properties, interfaces, requirements, and stable identifiers. Supports downstream traceability and controlled updates.
2. **Module Selection and Scenario Configuration:** identifies participating system types and instances and preserves their architectural connections for a specific mission.
3. **Urban Planning:** evaluates candidate sites, positions infrastructure, and defines operational routes within an explicit spatial reference.
4. **Behavior Engine:** interprets the supported operational description, resource relationships, equations, and power assumptions to generate mission histories and final metrics.
5. **Requirements Verification Loop:** associates simulated attributes with evaluable requirement constraints and returns verification evidence to the architecture workflow.
6. **CAD Submission:** associates stakeholder geometry with system identifiers and preserves engineering provenance while producing usable visualization assets.
7. **Visualization:** combines the selected scenario's geometry, terrain, routes, and recorded behavior for spatial and temporal inspection.
8. **Collaboration:** connects contributions made at different specialist steps through versioned models, artifacts, and shared exchange contracts.

### C Scenario lifecycle and data authority

- Describe the lifecycle from reference model to selected instances, spatial layout, operational configuration, execution, saved outputs, comparison, and playback.
- Define authority by information type: modeled dimensions and reference properties; scenario-specific overrides and routes; submitted CAD provenance; generated results; visualization derivatives.
- Explain that a scenario binds these artifacts together. Saved configuration and output isolation support revisiting alternatives; versioned dependencies are also needed for stronger long-term reproducibility.
- Separate logical resource interfaces from physical transport paths. A resource-flow arrow does not by itself define a terrain route or a separate transporter.
- Show the requirement-feedback path and the CAD-metadata enrichment path as distinct connections to the authoritative model.

**Main figure:** one updated ecosystem diagram showing the eight blocks, specialist entry points, the scenario lifecycle, and both feedback paths. Avoid a second diagram that repeats the same decomposition with implementation filenames.

<!-- page -->

## IV Implementation

### A Authoritative model and model exchange

- Describe SysML v2 modeling in MSOSA, system identifiers, typed resource and power ports, dimensions, and reference attributes.
- Explain the implemented export and parsing path into the JSON representations consumed by downstream tools. State which properties and relationships are preserved and checked.
- Distinguish a requirement's satisfy relationship from execution of a verification expression. Specify the actual evaluation path in Section IV.E.
- Explain where scenario-specific values override model defaults and how their provenance is retained.

### B Scenario initialization and module selection

- Introduce the ISRU preset, saved scenario loading, and new generic scenario workflow. Explain what is prepopulated by the preset and what the user must define.
- Describe architecture parsing, the directed system graph, port and connection checks, activation of a subset, and preservation of instance identity.
- Explain module multiplicity before placement and propagation of active systems to CAD, planning, and simulation.
- Keep detailed role inference and equation execution in Section IV.D. This subsection establishes the system graph they consume.

### C GIS planning and operational routes

- Retain the original regional site-assessment method and its criteria, normalization, weighting, data provenance, and planning resolution.
- Explain the local map frame, module placement and orientation, terrain guidance, and route construction. Distinguish regional site suitability from local route feasibility.
- Describe the actual routing objective and constraints implemented in the chosen paper version. Use qualified language for route optimality.
- Explain instance-level route endpoints, waypoints, optional stops, transporter assignments, route lengths, and available slope metrics.
- State how those outputs feed the DES and visualization. Distinguish a route-level travel approximation from detailed vehicle dynamics over every waypoint.

**Figures:** a compact system-connectivity example; one site and local-layout figure if it adds information beyond the final architecture diagram. Move large interface walkthroughs to supplementary material when they compete with technical evidence.

**Source integration:** reuse the ECLIPSE material on SysML, activation, GIS, and placement, then update the scenario entry points, multiplicity, and operational-route contract from the 8900 work and later repository discussions.

<!-- page -->

### D Configurable and extensible behavior engine

Give this subsection substantial space. Its contribution has two separate levels: a transparent and configurable ISRU model, and a generic framework for scenarios expressible through the supported operational roles.

**1 User-visible operational definition.** Explain how selected instances, resource and power interfaces, transporter assignments, routes, equations, and numerical assumptions become the executable scenario. Expose the causal connection between a user decision and a simulated outcome.

**2 Configurable ISRU implementation.** Describe multiple regolith and LOX rovers, multiple plants, per-plant input inventories, dispatch logic, pickup thresholds, loading assumptions, and outbound and empty return travel. Identify which operations remain simplified. Make explicit that the detailed process and energy equations are inspectable and editable, reference coefficients come from the scenario's SysML/assets, and simulation settings or supported overrides are exposed through configuration.

**3 Equation and parameter provenance.** Explain the detailed production and energy chains, including intermediate quantities. Separate technological assumptions, physical constants, scenario overrides, and execution settings. Document the active precedence rules and fallback behavior. A default value in a configurable field is different from a hidden assumption that a user cannot change.

**4 Generic role interpretation.** Describe Source, Processor, Storage, Consumer, Transporter, and PowerGenerator. Treat Passive as a supported classification where relevant, rather than implying an additional independent physics model. Explain inference from directed resource and power interfaces and explicit route assignment, user overrides, and ambiguous topologies. Distinguish the normal UI classification path from backend compatibility fallbacks.

**5 Behavior compilation.** Show how the selected roles, inventories, routes, equations, and power configuration become SimPy processes. Use a Processor example to connect an input delivery, inventory, transformation, processing delay, and output availability. Explain that new scenarios can be assembled within this vocabulary without a dedicated mission-specific controller.

**6 Equation contracts and validation.** Describe the restricted expression parser, intermediate variables, recognized variables, required outputs, and binding of outputs to resource, time, storage, or energy effects. Explain checks for missing equations, incompatible connections, absent transporters, invalid routes, and unknown variables. Validation checks executable consistency; it does not establish physical accuracy.

**7 Power and travel models.** Explain configured generation, stationary battery capacity and initial charge, demand modes, event energy, management interval, and inclusion of plant processing and storage demand in the system balance. Explain flat-terrain speed and the implemented route-slope adjustment. State the role of the explicit energy-unconstrained mode and distinguish it from power-feasible operation. Rover charging is not an implemented closed operational cycle.

**Figures and table:** one operational configuration figure; one role-to-SimPy behavior diagram; a compact role and equation-contract table. Include a numerical-settings capture only if readable and informative. Put actual case-study coefficient values and their sources in Section V.A.

<!-- page -->

### E Requirements verification

- Specify the demonstrated chain from time-indexed DES values to identified model attributes and executable requirement constraints.
- Explain the evaluated sampling times, pass/fail semantics, reporting, and model update process. Distinguish discrete sampled checks from continuous-time guarantees.
- Retain the team-developed verification contribution, supported by a current execution example and its report. Clearly identify which feedback steps are automatic and which require an engineering decision.

### F CAD conversion and authoritative metadata

- Describe supported STEP/STP, STL, OBJ, and USD-family input paths; the OpenCascade/pythonOCC, trimesh, and USD readers; generated USD assets; and browser previews.
- Explain source-CAD metadata separately from generated visualization metadata. Record provenance, units, geometry bounds, materials where available, and reliability of derived properties.
- Explain up-axis handling and the user-selected front reference. For native USD, respect the stage's orientation metadata; for converted formats, describe the applicable user choices. Apply front direction consistently to static placement orientation and moving actors.
- Preserve SysML dimensions as authoritative. Describe the actual geometry fitting policy, resulting length scale, and consistent transformation of area, volume, and center information before metadata write-back.
- Describe scenario-specific CAD storage, selection from the repository library, and resolved geometry references. Explain how distinct model choices remain associated with distinct modules and scenarios.
- Qualify volume and center calculations by geometric closure and material/density assumptions. Derived geometric properties are not a certified mass model.

### G Scenario packages and Omniverse playback

- Describe generation of the scene, waypoint layer, results, recorded log, terrain reference, actor definitions, and scenario manifest.
- Explain how the Omniverse extension selects and reads the package. Describe recorded-time synchronization, seeking, rate control, reset, route visibility, and camera targeting.
- Explain the common metric frame, terrain triangle sampling, interpolation, footprint-based plane fitting, pitch/roll, and vertical clearance adjustment.
- Describe route densification and terrain projection, slope diagnostics, rover orientation, and distance-based interpolation. Grounding does not flatten the terrain or create foundations.
- State the distinction between alignment of a prepared mesh and automatic retrieval of the exact geographic terrain patch. Identify remaining ISRU-oriented playback and telemetry compatibility logic.

### H Persistence automation and contributor workflow

- Explain which inputs, CAD references, assumptions, results, and visualization artifacts are saved with each named scenario; how saved configurations are reloaded; and how completed outputs remain distinguishable.
- Describe GitHub Pages, explicit workflow dispatches, GitHub Actions, versioned artifacts, and local Omniverse synchronization as actually implemented. Avoid claiming that every commit executes every pipeline stage.
- Explain scenario selection for comparison, the selected baseline, available final metrics and percentage changes, and overlaid histories.
- Relate each specialist contribution to the engineering artifacts it produces. Distinguish this asynchronous workflow from transactional multi-user application services.

**Figures:** one dual-metadata CAD diagram, with orientation and write-back examples only where needed; one manifest and terrain-integration diagram. Keep result dashboards for Section V.

<!-- page -->

## V Demonstration and results

### A Cases assumptions and evaluation protocol

- Define the current Lunar Spaceport-1 ISRU baseline from its saved configuration, rather than reconstructing it from prose in the old paper.
- Give active types and instance counts, site, coordinates and route lengths, duration, processing and conversion assumptions, inventory capacities, transport parameters, power demand and generation, battery initial conditions, and energy-constraint mode.
- Provide an assumptions table with each important coefficient's value, units, source or rationale, scope, and configured location. Include process coefficients, dispatch intervals, and the route-slope speed model.
- Identify software revision, scenario and run identifiers, terrain source and preparation, and output files used for the figures. Distinguish total simulation duration from individual plant operating time.
- Define a small controlled comparison campaign. Recommended cases: baseline; changed rover fleet; changed processing capacity; and changed power supply. Add a changed-route case if needed to substantiate the terrain-to-operations connection. Hold other assumptions fixed and explain exceptions.
- Include an analytical or independently calculated check of a simple resource and travel case, an energy-accounting check, and a documented insufficient-power case. These proposed checks are evidence to produce, not results already obtained.

### B Site assessment and complete workflow execution

- Retain the regional GIS ranking if its original method, inputs, and weights remain applicable. Report the selected site's rank under those criteria rather than calling it universally optimal.
- Show the actual local layout and routes used by the current DES and Omniverse package.
- Demonstrate that one identified scenario passes through system activation, placement, simulation, verification where executable, saved outputs, and visualization.
- Trace a changed input through the affected downstream artifacts. Demonstrate contribution continuity without inferring a measured improvement in collaboration efficiency.

### C ISRU outcomes and scenario comparison

- Report LOX produced, LOX delivered, retained inventories, regolith delivered and processed, plant activity, rover trips and distances, energy demand and generation, and battery state where modeled and logged.
- Separate total production from delivery fraction and inventory carryover. Delivery fraction over a finite horizon is not a thermodynamic or transport efficiency.
- Show time histories of the quantities needed to explain resource or power bottlenecks. Interpret changes in terms of the configured parameters and scheduling assumptions.
- Compare completed scenarios on common axes and state the selected baseline. Do not imply statistical significance for deterministic case comparisons.
- Replace the old numerical table with current outputs. The historical 111.23 kg LOX result and full-battery interpretation cannot be carried into the new abstract without regeneration and verification under the current model.

**Evidence:** case and assumptions table; updated GIS/layout figure; baseline and variant result table; aligned production, delivery, energy, and battery histories. Include only available and meaningful signals.

<!-- page -->

### D Initial generalization beyond ISRU

- Reproduce compact cargo-relay, ice-processing, and water-transfer cases using the generic engine and the same supported role contracts.
- For each case, report the system graph, resource types, roles, essential equations, routes, mode, and an observable outcome with units.
- Explain which behaviors are reused and whether a new controller was required. Keep the examples distinguishable so that different labels alone do not stand in for different operational capabilities.
- State the tested boundary: these resource chains demonstrate extensibility within a constrained vocabulary, not coverage of every lunar mission or validated process physics.

### E CAD and playback consistency

- Demonstrate conversion and metadata propagation on representative supported input formats. Report the original format, resolved orientation, applied scale, resulting geometry reference, and SysML metadata update.
- Show that two scenario-specific CAD selections remain distinct when saved and loaded. Check scenario identity across the selected configuration, results, manifest, geometry, and playback.
- Present terrain-grounded placement and projected operational routes. Use available slope and projection diagnostics to report consistency and limitations of the supplied terrain asset.
- Show an Omniverse frame with telemetry at a stated recorded simulation time and compare selected displayed values with the corresponding log entries.
- Describe the visual information stakeholders can inspect. Reserve claims about improved comprehension or decision performance for a separate evaluated study.

### F Verification and capability coverage

- Include an executable requirement example with its expression, traced attribute, sampled values, pass/fail output, and the engineering action taken if a violation occurs.
- Summarize the contribution-to-evidence mapping. Distinguish completed demonstrations, evidence still to generate, and capabilities outside the delivered scope.
- Separate implementation verification, physical-model validation, mission requirement verification, and usability evaluation. A successful end-to-end run establishes only the properties it actually checks.

**Results figures:** a readable comparison of actual completed runs; a small table or diagram of the three generic cases; a CAD write-back example; and Omniverse playback with synchronized telemetry. Avoid repeating configuration screenshots from Section IV.

**Evidence priorities:** regenerate the ISRU results first, preserve their assumptions, reproduce the generic examples, and collect the current verification output. Screenshots of entry menus alone do not establish scenario comparison or successful simulation.

<!-- page -->

## VI Discussion

### A Answers to the research questions

- **RQ1:** interpret configurability, module multiplicity, equation binding, and generic-case reuse. Distinguish configuration changes from extensions of the behavior library.
- **RQ2:** explain how model authority, source metadata, scenario overrides, saved outputs, and CAD and manifest associations preserve context across specialist contributions. Scope traceability to retained artifacts and dependencies.
- **RQ3:** explain the value of linking numerical histories to placement, routes, rover motion, and recorded-time telemetry. State when these representations correspond.

### B Limitations and interpretation

- Generic behavior uses constrained roles and predominantly mass-based resources. Coupled reactants, richer inventories, queues, failures, and stochastic operations remain outside the demonstrated scope.
- Power is a simplified balance. Energy-unconstrained runs establish no power feasibility; complete rover charging and electrical-network design are not implemented.
- DES travel uses simplified route metrics. Omniverse movement does not establish validated vehicle dynamics.
- Prepared-mesh grounding requires appropriate geographic source data and does not prove constructability. CAD properties depend on units, closure, scale, and density assumptions.
- GitHub supports asynchronous contributions. Simultaneous editing, access-control guarantees, conflict prevention, and quantified collaboration benefits require separate evidence.
- State physical-validation limits and remaining scenario-specific comparison and telemetry logic.

## VII Conclusions and future work

### A Conclusions

Answer the engineering objective through the completed demonstrations: the integrated contributor workflow, configurable operations, CAD/model consistency, and preserved quantitative and visual evaluation. Include only regenerated numerical findings and novelty claims supported by the literature assessment.

### B Future work

- Extend and verify behavior vocabulary, units, resource synchronization, power and mobility fidelity, and charging. Expand resource-independent comparison, telemetry, and dependency versioning.
- Automate geographic terrain preparation and enrich the existing CAD library with curated, traceable engineering components.
- Develop services for authenticated concurrent contributions and evaluate collaboration and decision support with representative users.

Do not list existing saved scenarios, baseline comparison, multiformat CAD, terrain sampling, or synchronized playback telemetry as future features. Future work should name the additional maturity or scope required.

<!-- page -->

## Integration map and source record

### Placement of the main 8900 capabilities

| Capability | Implementation | Evidence |
| --- | --- | --- |
| Visible ISRU architecture assumptions and equations | IV D items 1 to 3 | V A and V C |
| Role inference overrides and generic compiler | IV D items 4 to 6 | V D |
| Multiple rovers plants inventories and return trips | IV D item 2 | V C |
| Configurable power and route-level travel | IV C and IV D item 7 | V A and V C |
| CAD formats orientation scaling and dual metadata | IV F | V E |
| Scenario-specific CAD and reusable library assets | IV F and IV H | V E |
| Named scenarios reload and baseline comparison | IV B and IV H | V B and V C |
| Manifest packages and recorded-time telemetry | IV G | V E |
| Terrain sampling grounding and route projection | IV G | V B and V E |
| Original SysML GIS and requirement verification | IV A IV C and IV E | V B and V F |

### Architecture and implementation boundary

Architecture specifies the purpose, relationships, authority rules, and information that must cross each boundary. Implementation explains the chosen representations, tools, algorithms, equations, controls, and execution mechanisms. Results show the artifacts and measured behavior obtained from declared cases. Discussion interprets those findings and their limits.

Keep one explanation of each mechanism. For example, the architecture requires a traceable scenario package; implementation defines the manifest and package generation; results demonstrate loading the matching package; discussion assesses the resulting traceability and remaining dependencies.

### Source record

- **ECLIPSE paper:** ECLIPSE_PAPER.pdf, supplied SciTech copy, 19 PDF pages. Primary source for the original ecosystem, eight-block architecture, GIS method, and team-developed verification workflow. Its old results and broad claims require the updates identified above.
- **8900 paper:** Final-Paper_Brunier_Arthur.pdf, 23 PDF pages, including three front-matter pages. Technical Approach is on PDF pages 7 to 15; Results on pages 16 to 20; Discussion and conclusions on pages 19 to 22. Use PDF page positions rather than the report's printed page numbers when locating material.
- **Original outline:** Detailed Outline2.docx. Retain its useful overall organization; resolve conflicts in favor of the supplied paper and the later implemented capabilities.
- **Repository discussions:** Étudier intégration Omniverse, 359 retrieved turns; Expliquer la généralisation DES, 111 retrieved turns; Rédiger l’abstract du projet, including the final-tool and specialist-collaboration narrative decisions. The TRC discussion provides submission context rather than technical evidence.
- **Repository evidence:** scenario runner and configuration, generic compiler and equation evaluator, active ISRU engine, CAD conversion and SysML updater, scene and manifest generation, web interface, user guide, and GitHub workflows. The historic DES diagnosis describes the former implementation and must not override the current sources.
- **Review guidance:** advisor comments supplied with the request and three annotated photographs. They motivate the literature synthesis, architecture/implementation separation, revised motivation, and replacement of historical results.

The literature comparison and simulation campaign described here are the next evidence-producing stages. This outline does not report them as completed studies.

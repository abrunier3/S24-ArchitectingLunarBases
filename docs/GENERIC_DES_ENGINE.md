# Generic DES Scenario Engine

## Engine Selection

The DES workflow supports two explicit execution modes:

- `engine.mode = "isru"` runs the validated historical ISRU controllers.
- `engine.mode = "generic"` compiles the Step 4 scenario description into SimPy processes.

The ISRU preset selects the first mode. `Build New Scenario` selects the second mode.

## Scenario Contract

The generic compiler consumes `scenario_builder` from the structured scenario configuration. It uses:

- placed module instances and their SysML asset types;
- instance-level resource routes, rover assignments, stops, and distances;
- SysML power interfaces;
- module and rover equations;
- per-module power models;
- simulation duration and rover operating coefficients.

Rover resource types are inferred from active rover ports ending in `In` and `Out`. A future `WaterRover` with `WaterIn` and `WaterOut` therefore creates a Water route tool without an ISRU-specific code change.

## Generated SimPy Behavior

The UI infers a module behavior from resource-flow direction and passes the
selected class to the compiler:

- **Source:** has an outgoing resource route and produces when transport requests material.
- **Processor:** has incoming and outgoing resource flows with different resource types; it evaluates its transformation equations, waits for `ProcessingTime`, and makes its outputs available.
- **Storage:** is the conservative default for a same-resource relay or a resource-terminal module and retains deliveries in a dedicated `simpy.Container`.
- **Transporter:** is identified by an explicit resource-route assignment (`rover_type` / `rover_id`) or by the class selected in Step 2; it repeatedly acquires available cargo, travels to the destination, unloads, and performs an empty return trip.
- **Consumer:** is inferred for a power-only sink or selected explicitly in Step 2 when a resource-terminal module consumes rather than stores its input.
- **Generator:** has an outgoing power flow.

Automatic class detection does not inspect module names, attribute names, or
equation-variable names. The Step 2 class selector resolves the two topological
ambiguities: same-resource `Storage` versus `Transporter`, and terminal
`Storage` versus `Consumer`. The selected value is authoritative for the DES.

Each module instance owns its own inventory and processing process. Multiple instances therefore operate independently and in parallel.

## Equation Contract

The supported transformation outputs are:

```text
<Resource>Out = f(<Resource>In, attributes, SimulationTime)
<Resource>Stored = f(<Resource>Stored, <Resource>In, attributes)
ProcessingTime = f(<Resource>In, attributes)
TravelTime = f(Distance, CargoMass, RoverCapacity, attributes)
EnergyConsumed = f(resource variables, time, attributes)
PowerIn = f(SimulationTime, inventory, attributes)
PowerOut = f(SimulationTime, attributes)
EnergyGenerated = f(SimulationTime, attributes)
```

Equations are parsed with a restricted Python AST evaluator. Arbitrary Python execution and `eval()` are not used. Supported arithmetic includes `+`, `-`, `*`, `/`, powers, and the functions `abs`, `min`, `max`, `round`, and `sqrt`.

Intermediate variables are allowed when a later equation consumes them. A terminal output that has no effect on resources, time, storage, or power is rejected.

## Scheduling Rules

- A source operation begins when an assigned rover requests cargo.
- A processor operation begins when a delivery reaches its input inventory.
- A storage update occurs when cargo is unloaded.
- A rover departs when its assigned source has cargo available; routes assigned to one rover are served in round-robin order.
- Outbound travel uses the loaded cargo mass. Return travel is evaluated separately with zero cargo mass.
- Continuous power is integrated at `power.management_dt_hr`; event energy from production and transport is added to the same system balance.

## Preflight Validation

The workflow rejects a generic scenario when:

- a route references an unknown endpoint or stop;
- a route has no transporter, a non-positive distance, or conflicting units;
- a required resource output, processing-time law, or travel-time law is missing;
- an equation contains unsupported syntax, an unknown variable, or an output with no DES effect;
- a power-consuming module has no incoming power interface;
- a power profile is invalid.

## Standard Results

The engine writes the same two files consumed by the existing pipeline:

```text
lunar_spaceport_results.json
lunar_spaceport_log.json
```

Generic results contain module inventories, processing cycles, rover trips, route-level deliveries, loaded and return distance, energy demand and generation, unserved energy, event history, and terminal-resource delivery MoEs. The Step 5 dashboard detects `Engine = "GenericScenario"` and renders resource-independent metrics.

## Current Boundaries

- Resource quantities use mass-flow semantics and default to kilograms when no route unit is provided.
- A processor cycle is triggered by one delivered input resource. Coupled multi-reactant batch synchronization requires an additional input-stoichiometry contract.
- The current power manager balances the connected scenario as one electrical bus; cable capacity and independent microgrids are not yet modeled.
- Route stops affect path geometry and travel distance; they are not loading or unloading events unless represented as separate resource routes.
- Logical conditions, failures, maintenance, and probabilistic distributions are not yet part of the equation grammar.

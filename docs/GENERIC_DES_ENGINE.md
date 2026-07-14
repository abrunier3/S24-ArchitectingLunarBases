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

The compiler infers a module behavior from its routes:

- **Source:** has an outgoing resource route and produces when transport requests material.
- **Processor:** receives a resource, evaluates its transformation equations, waits for `ProcessingTime`, and makes its outputs available.
- **Storage:** retains deliveries in a dedicated `simpy.Container`; a same-resource pass-through module remains a storage module unless it defines `ProcessingTime`.
- **Transporter:** repeatedly acquires available cargo, travels to the destination, unloads, and performs an empty return trip.
- **Consumer:** has no resource transformation but may have a continuous, profile-based, or equation-based power demand.
- **Generator:** is identified by a power-system type or a `PowerOut` equation.

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

# DES Diagnosis Report

## Scope

This report describes the current Discrete Event Simulation (DES) scenario used by the ECLIPSE pipeline, the event logic implemented in the active model, and the main assumptions/limitations.

The active DES model used by the workflow is:

- `S24/DES_pipeline_version/ISRU_DES_Model_V5_2_PV.py`

The GitHub Actions workflow that calls it is:

- `.github/workflows/run_des.yml`

Older DES files such as `ISRU_DES_Model_V3.py`, `ISRU_DES_Model_V4_PV.py`, `ISRU_DES_Model_V5_PV.py`, and `ISRU_DES_Model_V5_1_PV.py` are historical versions and should not be treated as the active scenario unless the workflow is changed.

## High-Level Scenario

The DES models an ISRU-based lunar logistics scenario over a fixed 60-hour simulation window.

The core scenario is:

1. Regolith rovers repeatedly haul regolith to one or more ISRU plants.
2. ISRU plants process regolith batches into LOX.
3. Once enough LOX accumulates at an ISRU plant, a single LOX rover transports it to the landing/launch zone.
4. Optional infrastructure modules consume power: habitation, communication, landing/launch zone, and rover charging station.
5. If a solar power system is active, a power manager checks hourly whether generation plus battery storage can satisfy modeled demand.

The irreducible required DES core is:

- `ISRUPlant`
- `RegolithRover`

Other nodes are optional and gated by the active SysML nodes sent from the UI.

## Inputs

### From the UI / GitHub workflow

The UI sends active system nodes and DES slider values to the workflow. The main numerical inputs are:

- `Num_Regolith_Rovers`
- `Num_ISRU_Plants`
- `Regolith_Haul_Distance`
- `LOX_Haul_Distance`
- `Rover_Energy_Consumption`
- `Rover_Travel_Time`
- `ISRU_Plant_Processing_Rate`
- `LOX_Transport_Threshold`

The workflow also receives `urban_planning`, which contains module positions and route waypoints. This data is used to update the SysML JSON and downstream visualization paths. The DES itself still consumes scalar haul distances, not full waypoint geometry.

### From SysML/JSON assets

Runtime DES attributes are read through `ImportUtility.data_from_json(...)`, which maps legacy DES filenames to:

- `clean_database/json/ECLIPSE_Project/assets/ISRUPlant.json`
- `clean_database/json/ECLIPSE_Project/assets/Rover.json`
- `clean_database/json/ECLIPSE_Project/assets/SolarPowerSystem.json`
- `clean_database/json/ECLIPSE_Project/assets/HabitationModule.json`
- `clean_database/json/ECLIPSE_Project/assets/LaunchLandingZone.json`
- `clean_database/json/ECLIPSE_Project/assets/CommunicationModule.json`

The workflow also patches `ISRUPlant.json` before the run when needed: if `excavationEnergyCoeff` is missing from the ISRU plant asset, it copies the value from `ISRUExcavation.json`.

## Active Node Logic

The workflow does not pass raw SysML node names directly into the DES model. It first infers DES engine nodes from each active SysML part name, attributes, and ports.

Valid DES engine nodes are:

- `HabitationModule`
- `ISRUPlant`
- `LaunchLandingZone`
- `LOXRover`
- `RegolithRover`
- `SolarPowerSystem`
- `CommunicationModule`

Important consequence:

- `PropellantDepot` is not an independent DES entity in the active model.
- `ISRUExcavation` is not an independent DES entity either; its data is partly used for compatibility through `excavationEnergyCoeff`.
- Physical route geometry is mainly used by the SysML/USD/Omniverse pipeline, while DES uses scalar distance inputs.

## Event Logic

### 1. Regolith Rover Loop

Each regolith rover runs the same infinite process:

1. Load `4000 kg` of regolith.
2. Travel the configured `Regolith_Haul_Distance`.
3. Unload.
4. Put `4000 kg` into the shared regolith buffer.
5. Repeat.

The hardcoded regolith batch size is:

- `roverBatch = 4000 kg`

The travel time is:

```text
travel_time_hr = distance_km * Rover_Travel_Time
```

The rover energy consumption is:

```text
energy_kWh = distance_km * Rover_Energy_Consumption * current_load_kg
```

Assumption:

- The distance input is treated as the total modeled distance for one delivery cycle.
- Loading/unloading time is not modeled.
- Return-to-source behavior is not explicitly modeled as a separate empty trip.

### 2. Regolith Buffer

All regolith rovers feed one shared SimPy container:

```text
capacity = 20,000 kg * Num_Regolith_Rovers
```

ISRU plants pull `4000 kg` batches from this shared buffer.

Assumption:

- Regolith inventory is continuous at the buffer level.
- There is no explicit queueing/loading equipment model between rover and plant.

### 3. ISRU Plant Processing

Each ISRU plant runs an infinite controller:

1. Wait until `4000 kg` of regolith is available.
2. Process that batch.
3. Generate LOX and add it to the plant's internal LOX storage.
4. Repeat.

Processing duration:

```text
processing_time_hr = regolith_mass_kg / ISRU_Plant_Processing_Rate
```

LOX production uses the model equation:

```text
extracted_LOX_fraction = (0.51 * 0.47 * 31.999 * regHeadGrade) / (2 * 151.71)
generated_LOX = extracted_LOX_fraction * regolith_mass
```

With the current default `regHeadGrade = 0.1`, a `4000 kg` regolith batch produces approximately:

```text
10.11 kg LOX
```

ISRU processing energy includes:

- excavation energy
- regolith transport energy
- beneficiation energy
- reactor energy
- electrolysis energy
- liquefaction energy

Assumptions:

- Each ISRU plant can process one batch at a time.
- Multiple ISRU plants process in parallel if enough regolith is available.
- Each plant has its own LOX storage variable.
- Regolith/LOX chemistry and energy equations come from the cited ISRU reference model.

### 4. LOX Storage Energy at ISRU Plant

Each plant has a separate hourly LOX storage energy process:

```text
storage_energy_kWh = 0.31 * plant.LOXStored * dt
```

This is added directly to:

```text
plant.totalEnergyConsumed
```

Important limitation:

- This plant storage/processing energy is tracked in the ISRU plant result, but it is not currently exposed to the `PowerManager` as an hourly `getCurrentPowerDemand(...)`.
- Therefore, solar power/battery feasibility does not fully account for ISRU plant process energy demand.

### 5. LOX Rover Delivery Logic

The LOX rover process is spawned only when both are active:

- `LOXRover`
- `LaunchLandingZone`

Each ISRU plant has its own LOX delivery controller. Every hour, each controller checks:

```text
if plant.LOXStored >= LOX_Transport_Threshold
```

When the threshold is reached:

1. The plant enters a first-come-first-served queue for a shared LOX rover resource.
2. Only one LOX rover exists.
3. While waiting, the plant continues accumulating LOX.
4. When the rover becomes available, the plant transfers all currently stored LOX.
5. Plant LOX storage is reset to zero.
6. Rover travels `LOX_Haul_Distance`.
7. LOX is delivered to the landing/launch zone.

Assumptions:

- There is a single LOX rover shared by all ISRU plants.
- The queue is FCFS through a SimPy `Resource(capacity=1)`.
- Loading/unloading time is not modeled.
- If the LOX rover or landing zone is inactive, no LOX transport occurs and LOX remains at the plant.

### 6. Landing / Launch Zone

The landing/launch zone receives LOX deliveries and stores them up to:

```text
loxCapacity = 50,000 kg
```

Its modeled power demand is:

```text
demand_kWh = (chillingPowerPerKgLOX * loxStored + utilitiesPowerRate) * dt
```

Current asset defaults:

- `utilitiesPowerRate = 3 kW`
- `chillingPowerPerKgLox = 0.31 kW/kg LOX`
- scheduled spike: `50 kWh` at `t = 25 hr`

Assumption:

- No launch event consumes LOX in the active scenario.

### 7. Habitat and Communication Module

If active and if the solar system exists, these modules are registered with the power manager.

Habitat defaults:

- `constantPowerRate = 5 kW`
- scheduled spike: `20 kWh` at `t = 10 hr`

Communication module defaults:

- `constantPowerRate = 2 kW`
- scheduled spike: `10 kWh` at `t = 15 hr`

Assumption:

- Power spikes are one-time energy additions during the hourly power-management timestep.

### 8. Solar Power System and Power Manager

If `SolarPowerSystem` is active, a `PowerManager` runs every hour.

Solar defaults:

- `powerOutput = 100 kW`
- `batteryCapacity = 500 kWh`
- `batteryCharge = 500 kWh`
- degradation factors currently default to `1.0`

At each hourly timestep:

1. Solar generates:

```text
energyGenerated = currentPowerOutput * dt
```

2. The power manager sums demand from registered consumers that implement:

```text
getCurrentPowerDemand(dt)
```

3. If generation exceeds demand, the battery charges.
4. If demand exceeds generation, the battery discharges.
5. If the battery cannot cover the deficit, the simulation raises a `POWER FAILURE`.

Important limitation:

- `ISRUPlant` objects are registered with the power manager, but `ISRUPlant` does not implement `getCurrentPowerDemand(dt)`.
- As a result, ISRU process energy is not included in the solar/battery feasibility check.
- Power feasibility currently includes habitat, communication module, landing zone, and charging station demand when active.

### 9. Rover Battery and Charging

Rovers start from the battery values in `Rover.json`:

- `batteryCapacity = 100 kWh`
- `batteryCharge = 100 kWh`
- `maxCapacity = 5000 kg`

The active model creates a rover charging station when `LOXRover` is active:

- `chargingPowerRate = 20 kW`
- `efficiencyFactor = 0.85`

However:

- No process currently calls `chargingStation.chargeRover(...)`.
- Therefore, rovers do not recharge automatically during the active DES scenario.

Assumption/limitation:

- Rover battery failure is possible if repeated trips consume more energy than the initial battery.
- Charging station metrics may remain zero unless charging logic is explicitly added.

## Hardcoded Values

The current DES still contains several hardcoded assumptions:

- Simulation duration: `60 hr`
- Regolith batch size: `4000 kg`
- Regolith buffer capacity: `20,000 kg * Num_Regolith_Rovers`
- LOX delivery polling interval: `1 hr`
- LOX storage energy coefficient at plant: `0.31`
- Habitat power spike: `20 kWh` at `10 hr`
- Communication power spike: `10 kWh` at `15 hr`
- Landing zone power spike: `50 kWh` at `25 hr`
- Charging station power: `20 kW`
- Charging station efficiency: `0.85`
- One shared LOX rover resource for all ISRU plants

The following are configurable through workflow/UI inputs:

- number of regolith rovers
- number of ISRU plants
- regolith haul distance
- LOX haul distance
- rover energy consumption
- rover travel time
- ISRU processing rate
- LOX transport threshold

The following come from SysML/JSON assets:

- rover capacity and battery defaults
- solar generation and battery defaults
- module power rates
- landing zone LOX capacity and chilling coefficient
- ISRU physical/chemical/energy coefficients

## Outputs

The DES writes:

- `lunar_spaceport_results.json`
- `lunar_spaceport_log.json`

The workflow wraps them into:

- `outputs/des_results.json`

The result file includes:

- active nodes
- input slider values
- ISRU plant metrics
- rover distance/energy/battery state
- landing zone LOX storage
- solar/battery metrics
- power manager demand/generation time series
- time-series log data

## What the DES Does Not Currently Model

The active DES does not currently model:

- full waypoint-by-waypoint rover motion
- terrain slope effects on rover speed or energy
- explicit loading/unloading durations
- explicit empty return trips
- rover charging behavior during operations
- launch events consuming LOX
- propellant depot as a separate dynamic entity
- ISRU process energy as a demand on the solar/battery power manager
- lunar day/night cycles or time-varying solar availability
- stochastic failures, maintenance, or random processing delays

These effects may be represented visually downstream or partially encoded through input distances, but they are not solved dynamically inside the current DES engine.

## Current Diagnosis Summary

The current DES is best understood as a deterministic logistics-and-production model for a lunar ISRU scenario:

- Regolith logistics are continuous and batch-based.
- ISRU production is batch-based and can run in parallel across multiple plants.
- LOX transport is threshold-triggered and constrained by one shared LOX rover.
- Power management is hourly and can fail the scenario when modeled demand exceeds solar generation plus battery reserve.
- Urban planning routes influence the pipeline and visualization, but the DES itself still uses scalar haul distances.

The main technical caveat is that ISRU plant energy is tracked as an output but is not currently coupled back into the power manager's demand calculation. This means the power feasibility check is incomplete until ISRU plants expose a `getCurrentPowerDemand(dt)` method or the power manager is extended to account for process energy events.

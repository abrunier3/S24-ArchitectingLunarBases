# Generic DES Test Scenarios

The repository contains three small non-ISRU scenarios. Each scenario uses the
same repository-safe identifier for both authoritative files:

```text
clean_database/sysml/<Scenario_Name>.sysml
clean_database/scenarios/<Scenario_Name>.json
```

After the files are pushed, open **Mission Scenario > Saved Scenarios**, load an
example, run the SysML graph, inspect or move the modules in Step 4, and run the
DES in Step 5. The configurations already contain routes and equations, so they
can also be used unchanged as regression cases.

## Water_Transfer_Test

```text
WaterExtractor --(WaterRover / Water)--> WaterTank
SolarPowerSystem -----------------------> WaterExtractor, WaterTank
```

- The extractor is a source. A rover request triggers one production cycle.
- `WaterOut` is limited by `productionRate`.
- The rover capacity limits the mass moved during each trip.
- The rover performs a loaded outbound trip and an empty return trip.
- The tank is a terminal additive stock.

This is the smallest example for checking a new resource name, a dynamic rover
tool, route travel time, storage, and the power balance.

## Ice_Processing_Test

```text
IceExtractor --(IceRover / Ice)--> WaterProcessor
WaterProcessor --(WaterRover / Water)--> WaterTank
SolarPowerSystem -----------------------> powered modules
```

- `IceExtractor` produces ice on demand.
- `WaterProcessor` converts the delivered ice using
  `WaterOut = IceIn * conversionEfficiency`.
- `ProcessingTime = IceIn / processingRate` delays each processor cycle.
- A second rover fleet moves the produced water to the final tank.

This example checks two resource types, two rover types, a processor, and the
propagation of processing energy into the power model.

## Cargo_Relay_Test

```text
CargoSource --(CargoRover)--> ForwardDepot --(CargoRover)--> HabitatConsumer
```

- The source releases cargo in bounded batches.
- The same rover fleet serves both route legs.
- `ForwardDepot` receives and later releases the same resource. It is inferred
  as a storage relay, not as a processor.
- The habitat is the terminal cargo inventory.
- No generator is included, so rover energy appears as unserved energy. This is
  intentional and makes the power consequence visible in the results.

This example checks a multi-leg logistics chain and a reusable intermediate
stock without an ISRU-specific controller.

## Naming and persistence

The **Start building your mission now** button opens the Mission Scenario
selector. Creating an ISRU or new scenario asks for its name immediately. The UI
normalizes that name to letters, numbers, and underscores, then creates both the
SysML file and configuration JSON on the active GitHub branch. A pre-existing
SysML file with the same name can also be paired with a new configuration.

The Graph and DES workflows receive the selected scenario identifier. Their
scenario-specific outputs are stored under:

```text
outputs/scenarios/<Scenario_Name>/graph.json
outputs/scenarios/<Scenario_Name>/des_results.json
```

`outputs/graph.json` and `outputs/des_results.json` remain compatibility copies
of the latest run.

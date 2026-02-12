package 'Lunar Rover' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    part LunarRover {

        // ---------------------------------------------------------------------
        // Simulation binding
        // ---------------------------------------------------------------------
        attribute simId    = "regolith_rover_1";
        attribute simClass = "LunarRover";

        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part LunarRover_dims {
            attribute length = 3.2; // meters
            attribute width  = 2.0; // meters
            attribute height = 1.8; // meters

            attribute metersPerUnit = 1;
            attribute upAxis = "Z";

            attribute X = 20; // meters
            attribute Y = 5;  // meters
            attribute Z = 0;  // meters
        }

        attribute geometry    = "assets/geom/LunarRover_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";

        // ---------------------------------------------------------------------
        // Core operational parameters (match Python __init__)
        // ---------------------------------------------------------------------
        attribute name            = "Regolith Cargo Rover";
        attribute roverType       = "cargo";   // "crew" or "cargo"
        attribute maxCapacity     = 5000;      // kg
        attribute energyPerKmPerKg = 3.4e-4;   // kWh/(km*kg)
        attribute batteryCapacity = 100;       // kWh
        attribute hoursPerKm      = 5;         // hr/km

        // ---------------------------------------------------------------------
        // State variables (match Python internal state at t=0)
        // NOTE: your Python starts batteryCharge=batteryCapacity; keep for traceability
        // ---------------------------------------------------------------------
        attribute currentLoad        = 0;    // kg
        attribute batteryCharge      = 100;  // kWh (starts full)
        attribute totalDistanceTraveled = 0; // km
        attribute totalEnergyConsumed   = 0; // kWh
    }
}

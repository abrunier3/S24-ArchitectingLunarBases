package 'Landing Launch Zone' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    part LandingLaunchZone {

        // ---------------------------------------------------------------------
        // Simulation binding
        // ---------------------------------------------------------------------
        attribute simId    = "lz_alpha";
        attribute simClass = "LandingLaunchZone";

        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part LandingLaunchZone_dims {
            attribute length = 18; // meters
            attribute width  = 14; // meters
            attribute height = 6;  // meters

            attribute metersPerUnit = 1;
            attribute upAxis = "Z";

            attribute X = 80; // meters
            attribute Y = 10; // meters
            attribute Z = 0;  // meters
        }

        attribute geometry    = "assets/geom/LandingLaunchZone_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";

        // ---------------------------------------------------------------------
        // Core operational parameters (match Python __init__)
        // ---------------------------------------------------------------------
        attribute name               = "LZ-Alpha";
        attribute loxCapacity        = 50000; // kg
        attribute utilitiesPowerRate = 3;     // kW

        // ---------------------------------------------------------------------
        // State variables (match Python internal state)
        // ---------------------------------------------------------------------
        attribute loxStored = 0;            // kg
        attribute totalEnergyConsumed = 0;  // kWh

        // ---------------------------------------------------------------------
        // Power model coefficients (match getCurrentPowerDemand)
        // basePower = loxChillCoeff * loxStored + utilitiesPowerRate
        // ---------------------------------------------------------------------
        attribute loxChillCoeff = 0.31; // kW/kg  (since basePower is kW and loxStored is kg)

        // ---------------------------------------------------------------------
        // Optional spike schedule (export-friendly)
        // Your code stores spikes as (time, energy) tuples.
        // ---------------------------------------------------------------------
        attribute spikeScheduleJSON =
            "[{\"time_hr\":25,\"energy_kWh\":50}]";
    }
}

  package 'LaunchLandingZone' {


    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;


    part LaunchLandingZone {
        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part LaunchLandingZone_dims {
            attribute length = 50; // meters
            attribute width = 50; // meters
            attribute height = 10; // meters


            attribute metersPerUnit = 1;
            attribute upAxis = "Z";


            attribute X = 0; // meters
            attribute Y = 0; // meters
            attribute Z = 0; // meters
        }

        // ---------------------------------------------------------------------
        // Core operational parameters (mapped from Python class attributes)
        // ---------------------------------------------------------------------
        attribute loxCapacity = 50000; // kg
        attribute loxStored = 0; // kg
        attribute utilitiesPowerRate = 3; // kW/hr
        attribute totalEnergyConsumed = 0; // kWh
        attribute chillingPowerPerKgLox = 0.31; // kWh/kg

        attribute LaunchLandingZone_volume = (LaunchLandingZone_dims.length * LaunchLandingZone_dims.width * LaunchLandingZone_dims.height)*LaunchLandingZone_dims.metersPerUnit^3 * 1000; // liters


        attribute geometry = "assets/geom/LaunchLandingZone_geom.usda";
        attribute material = "assets/mtl/steel.usda"; // Structural steel
        }


}
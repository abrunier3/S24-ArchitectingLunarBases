  package 'Rover' {


    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;


    part Rover {
        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part Rover_dims {
            attribute length = 5; // meters
            attribute width = 3; // meters
            attribute height = 3; // meters


            attribute metersPerUnit = 1;
            attribute upAxis = "Z";


            attribute X = 0; // meters
            attribute Y = 0; // meters
            attribute Z = 0; // meters
        }

        // ---------------------------------------------------------------------
        // Core operational parameters (mapped from Python class attributes)
        // ---------------------------------------------------------------------
        attribute batteryCapacity = 100; // kWh
        attribute maxCapacity = 5000; // kg
        attribute energyPerKmPerKg = 0.00034; // kWh/km/kg
        attribute batteryCharge = 100; // kWh
        attribute totalDistanceTraveled = 0; // km
        attribute totalEnergyConsumed = 0; // kWh
        attribute hoursPerKm = 5; // hours/km

        attribute Rover_volume = (Rover_dims.length * Rover_dims.width * Rover_dims.height)*Rover_dims.metersPerUnit^3 * 1000; // liters


        attribute geometry = "assets/geom/Rover_geom.usda";
        attribute material = "assets/mtl/steel.usda"; // Structural steel
        }


}
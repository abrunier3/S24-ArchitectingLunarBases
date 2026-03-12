  package 'Habitation Module' {


    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;


    part HabitationModule {
        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part HabitationModule_dims {
            attribute length = 20; // meters
            attribute width = 10; // meters
            attribute height = 8; // meters


            attribute metersPerUnit = 1;
            attribute upAxis = "Z";


            attribute X = 0; // meters
            attribute Y = 0; // meters
            attribute Z = 0; // meters
        }

        // ---------------------------------------------------------------------
        // Core operational parameters (mapped from Python class attributes)
        // ---------------------------------------------------------------------
        attribute constantPowerRate = 5; // kW/hr 


        // State variables
        attribute totalEnergyConsumed = 0; // kWh

        attribute HabitationModule_volume = (HabitationModule_dims.length * HabitationModule_dims.width * HabitationModule_dims.height)*HabitationModule_dims.metersPerUnit^3 * 1000; // liters


        attribute geometry = "assets/geom/HabitationModule_geom.usda";
        attribute material = "assets/mtl/steel.usda"; // Structural steel
        }


}
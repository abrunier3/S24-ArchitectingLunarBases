  package 'Communication Module' {


    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;


    part CommunicationModule {
        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part CommunicationModule_dims {
            attribute length = 20; // meters
            attribute width = 30; // meters
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
        attribute constantPowerRate = 2; // kW/hr 


        // State variables
        attribute totalEnergyConsumed = 0; // kWh

        attribute CommunicationModule_volume = (CommunicationModule_dims.length * CommunicationModule_dims.width * CommunicationModule_dims.height)*CommunicationModule_dims.metersPerUnit^3 * 1000; // liters


        attribute geometry = "assets/geom/CommunicationModule_geom.usda";
        attribute material = "assets/mtl/steel.usda"; // Structural steel
        }


}
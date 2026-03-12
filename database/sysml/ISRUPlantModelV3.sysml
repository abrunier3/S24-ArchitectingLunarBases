  package 'ISRU Plant' {


    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;


    part ISRUPlant {
        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part ISRUPlant_dims {
            attribute length = 20; // meters
            attribute width = 15; // meters
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
        attribute processingRate = 1600; // kg/hr of regolith processed
        attribute regHeadGrade = 0.1; // wt% ilmenite in regolith feed
        attribute lunarGravity = 1.62; // m/s^2


        // State variables
        attribute LOXStored = 0; // kg
        attribute totalEnergyConsumed = 0; // kWh


        attribute ISRUPlant_volume = (ISRUPlant_dims.length * ISRUPlant_dims.width * ISRUPlant_dims.height)*ISRUPlant_dims.metersPerUnit^3 * 1000; // liters


        attribute geometry = "assets/geom/ISRUPlant_geom.usda";
        attribute material = "assets/mtl/steel.usda"; // Structural steel


        // ---------------------------------------------------------------------
        // Subsystems corresponding to process steps in the DES model
        // ---------------------------------------------------------------------

        attribute excavationEnergyCoeff = 6.5e-6; // kWh/kg
        attribute transportEnergyCoeff = 3.6e-4; // kWh/(kg*km)
        attribute liftHeight = 1; // meters
        attribute gangueTransportDist = 1; // km
        attribute reactorEnergyCoeff = 0.385; // kWh/kg beneficiated regolith
        attribute electrolysisEnergyCoeff = 8.26; // kWh/kg H2O
        attribute liquefactionEnergyCoeff = 1.17; // kWh/kg O2
        }


}
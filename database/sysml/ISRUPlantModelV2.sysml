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
        // Simulation binding (for SysML -> JSON -> DES instantiation)
        // ---------------------------------------------------------------------
        attribute simId    = "isru_plant_1";
        attribute simClass = "ISRUPlant";

        // ---------------------------------------------------------------------
        // Physical layout and geometry (visual / USD)
        // ---------------------------------------------------------------------
        part ISRUPlant_dims {
            attribute length = 20; // meters
            attribute width  = 15; // meters
            attribute height = 8;  // meters

            attribute metersPerUnit = 1;
            attribute upAxis = "Z";

            attribute X = 0; // meters
            attribute Y = 0; // meters
            attribute Z = 0; // meters
        }

        attribute ISRUPlant_volume =
            (ISRUPlant_dims.length * ISRUPlant_dims.width * ISRUPlant_dims.height)
            * ISRUPlant_dims.metersPerUnit^3 * 1000; // liters

        attribute geometry    = "assets/geom/ISRUPlant_geom.usda";

        // Use only materials that exist in your library for now
        attribute materialRef = "Aluminum_2219_T87";

        // ---------------------------------------------------------------------
        // Core operational parameters (match Python __init__)
        // ---------------------------------------------------------------------
        attribute processingRate = 1600; // kg/hr
        attribute regHeadGrade   = 0.1;  // fraction used by DES

        // Gravity used in the DES code
        attribute lunarGravity = 1.62; // m/s^2

        // ---------------------------------------------------------------------
        // State variables (match Python internal state)
        // ---------------------------------------------------------------------
        attribute LOXStored = 0;           // kg
        attribute totalEnergyConsumed = 0; // kWh

        // ---------------------------------------------------------------------
        // Coefficients used in DES equations (documented here)
        // ---------------------------------------------------------------------
        attribute excavationEnergyCoeff      = 6.5e-6; // kWh/kg
        attribute transportEnergyCoeff       = 3.6e-4; // kWh/(kg*km)
        attribute beneficiationLiftHeight    = 1;      // m
        attribute gangueTransportDist        = 1;      // km
        attribute reactorEnergyCoeff         = 0.385;  // kWh/kg beneficiated regolith
        attribute electrolysisEnergyCoeff    = 8.26;   // kWh/kg H2O
        attribute liquefactionEnergyCoeff    = 1.17;   // kWh/kg O2

        // Extraction expression constants (optional)
        attribute extractionCoeff_a = 0.51;
        attribute extractionCoeff_b = 0.47;
        attribute molarMassO2       = 31.999;
        attribute molarMassIlm      = 151.71;
    }
}

  package 'SolarPowerSystem' {


    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;


    part SolarPowerSystem {
        // ---------------------------------------------------------------------
        // Physical layout and geometry
        // ---------------------------------------------------------------------
        part SolarPowerSystem_dims {
            attribute length = 25; // meters
            attribute width = 25; // meters
            attribute height = 4; // meters


            attribute metersPerUnit = 1;
            attribute upAxis = "Z";


            attribute X = 0; // meters
            attribute Y = 0; // meters
            attribute Z = 0; // meters
        }

        // ---------------------------------------------------------------------
        // Core operational parameters (mapped from Python class attributes)
        // ---------------------------------------------------------------------
        attribute powerOutput = 100; // kW
        attribute powerDegradationFactor = 1;
        attribute batteryCapacity = 500; // kWh
        attribute batteryDegradationFactor = 1;
        attribute batteryCharge = 500; // kWh
        attribute totalEnergyGenerated = 0; // kWh
        attribute totalEnergyFromBattery = 0; // kWh

        attribute SolarPowerSystem_volume = (SolarPowerSystem_dims.length * SolarPowerSystem_dims.width * SolarPowerSystem_dims.height)*SolarPowerSystem_dims.metersPerUnit^3 * 1000; // liters


        attribute geometry = "assets/geom/SolarPowerSystem_geom.usda";
        attribute material = "assets/mtl/steel.usda"; // Structural steel
        }


}
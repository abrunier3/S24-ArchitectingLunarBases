package 'Oxygen Tank' {

    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    // -------------------------------------------------------------------------
    // Oxygen Tank
    // -------------------------------------------------------------------------

    part O2Tank {
        part O2Tank_dims {
            attribute length = 1.5; // meters
            attribute width = 1.2; // meters
            attribute height = 1.3; // meters

            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
        }

        attribute volume = (O2Tank_dims.length * O2Tank_dims.width * O2Tank_dims.height) * O2Tank_dims.metersPerUnit^3 * 1000; // liters
        attribute usableO2Capacity = volume * 0.85; // liters
        attribute dryMass = 400; // kg
        attribute operatingPressure = 250; // kPa
        attribute maxPressure = 400; // kPa
        attribute wallThickness = 0.01; // meters

        attribute geometry = "assets/geom/O2Tank_geom.usda";
        attribute material = "assets/mtl/aluminum.usda"; // Aluminum alloy 2219-T87
    }

    requirement TankCapacityReq {
        id = "O2TANK-001";
        text = "The oxygen storage tank shall provide a minimum internal geometric volume of 2.3 m³ to accommodate the required liquid oxygen capacity and ullage.";
    }

    requirement UsableLOXCapacityReq {
        id = "O2TANK-002";
        text = "The oxygen storage tank shall provide a minimum usable LOX capacity of 85 percent of the total volume of the tank at beginning of life conditions.";
    }

    requirement TankMassReq {
        id = "O2TANK-003";
        text = "The dry mass of the oxygen storage tank shall not exceed 400 kg.";
    }

    requirement OperatingPressureReq {
        id = "O2TANK-004";
        text = "The oxygen storage tank shall be designed to operate at a nominal pressure of 250 kPa.";
    }

    requirement MaxPressureReq {
        id = "O2TANK-005";
        text = "The oxygen storage tank shall be designed to withstand a maximum pressure of 400 kPa without structural failure.";
    }

    requirement WallThicknessReq {
        id = "O2TANK-006";
        text = "The wall thickness of the oxygen storage tank shall be a minimum of 0.01 meters to ensure structural integrity under operating conditions.";
    }

    requirement MaterialReq {
        id = "O2TANK-007";
        text = "The oxygen storage tank shall be constructed from aluminum alloy 2219-T87 or an approved equivalent cryogenic-grade aluminum alloy.";
    }

    requirement DimensionReq {
        id = "O2TANK-008";
        text = "The oxygen storage tank dimensions shall be approximately 1.5 meters in length, 1.2 meters in width, and 1.3 meters in height to fit within the designated habitat module space.";
    }

    satisfy TankCapacityReq        by O2Tank;
    satisfy UsableLOXCapacityReq   by O2Tank;
    satisfy TankMassReq            by O2Tank;
    satisfy OperatingPressureReq   by O2Tank;
    satisfy MaxPressureReq         by O2Tank;
    satisfy WallThicknessReq       by O2Tank;
    satisfy MaterialReq            by O2Tank;
    satisfy DimensionReq           by O2Tank;
}
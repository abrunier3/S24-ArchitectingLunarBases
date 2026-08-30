package Water_Transfer_Test {
    private import SysML::*;

    part WaterTransferMission {
        part WaterExtractor {
            part WaterExtractor_dims {
                attribute length = 8;
                attribute width = 6;
                attribute height = 4;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute productionRate = 20;
            port WaterExtractor_WaterPortOut {
                out item WaterOut;
            }
            port WaterExtractor_PowerPortIn {
                in item PowerIn;
            }
        }

        part WaterRover {
            part WaterRover_dims {
                attribute length = 4;
                attribute width = 2.5;
                attribute height = 2;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute maxCapacity = 10;
            attribute hoursPerKm = 0.5;
            attribute energyPerKmPerKg = 0.01;
            port WaterRover_WaterPortInOut {
                in item WaterIn;
                out item WaterOut;
            }
        }

        part WaterTank {
            part WaterTank_dims {
                attribute length = 5;
                attribute width = 5;
                attribute height = 5;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute storageCapacity = 500;
            port WaterTank_WaterPortIn {
                in item WaterIn;
            }
            port WaterTank_PowerPortIn {
                in item PowerIn;
            }
        }

        part SolarPowerSystem {
            part SolarPowerSystem_dims {
                attribute length = 12;
                attribute width = 10;
                attribute height = 2;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute powerOutput = 50;
            attribute batteryCapacity = 100;
            attribute batteryCharge = 100;
            port Solar_WaterExtractorPowerOut {
                out item PowerOut;
            }
            port Solar_WaterTankPowerOut {
                out item PowerOut;
            }
        }
    }

    interface def WaterMovement {
        end source;
        end target;
    }
    interface def PowerMovement {
        end source;
        end target;
    }

    interface ExtractorToWaterRover : WaterMovement connect WaterTransferMission.WaterExtractor.WaterExtractor_WaterPortOut to WaterTransferMission.WaterRover.WaterRover_WaterPortInOut;
    interface WaterRoverToTank : WaterMovement connect WaterTransferMission.WaterRover.WaterRover_WaterPortInOut to WaterTransferMission.WaterTank.WaterTank_WaterPortIn;
    interface SolarToExtractor : PowerMovement connect WaterTransferMission.SolarPowerSystem.Solar_WaterExtractorPowerOut to WaterTransferMission.WaterExtractor.WaterExtractor_PowerPortIn;
    interface SolarToTank : PowerMovement connect WaterTransferMission.SolarPowerSystem.Solar_WaterTankPowerOut to WaterTransferMission.WaterTank.WaterTank_PowerPortIn;
}

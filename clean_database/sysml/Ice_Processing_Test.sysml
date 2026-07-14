package Ice_Processing_Test {
    private import SysML::*;

    part IceProcessingMission {
        part IceExtractor {
            part IceExtractor_dims {
                attribute length = 8;
                attribute width = 6;
                attribute height = 4;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute extractionRate = 15;
            port IceExtractor_IcePortOut {
                out item IceOut;
            }
            port IceExtractor_PowerPortIn {
                in item PowerIn;
            }
        }

        part IceRover {
            part IceRover_dims {
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
            port IceRover_IcePortInOut {
                in item IceIn;
                out item IceOut;
            }
        }

        part WaterProcessor {
            part WaterProcessor_dims {
                attribute length = 10;
                attribute width = 8;
                attribute height = 5;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute conversionEfficiency = 0.8;
            attribute processingRate = 10;
            port WaterProcessor_IcePortIn {
                in item IceIn;
            }
            port WaterProcessor_WaterPortOut {
                out item WaterOut;
            }
            port WaterProcessor_PowerPortIn {
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
            attribute powerOutput = 100;
            attribute batteryCapacity = 200;
            attribute batteryCharge = 200;
            port Solar_ExtractorPowerOut {
                out item PowerOut;
            }
            port Solar_ProcessorPowerOut {
                out item PowerOut;
            }
            port Solar_TankPowerOut {
                out item PowerOut;
            }
        }
    }

    interface def IceMovement { end source; end target; }
    interface def WaterMovement { end source; end target; }
    interface def PowerMovement { end source; end target; }

    interface ExtractorToIceRover : IceMovement connect IceProcessingMission.IceExtractor.IceExtractor_IcePortOut to IceProcessingMission.IceRover.IceRover_IcePortInOut;
    interface IceRoverToProcessor : IceMovement connect IceProcessingMission.IceRover.IceRover_IcePortInOut to IceProcessingMission.WaterProcessor.WaterProcessor_IcePortIn;
    interface ProcessorToWaterRover : WaterMovement connect IceProcessingMission.WaterProcessor.WaterProcessor_WaterPortOut to IceProcessingMission.WaterRover.WaterRover_WaterPortInOut;
    interface WaterRoverToTank : WaterMovement connect IceProcessingMission.WaterRover.WaterRover_WaterPortInOut to IceProcessingMission.WaterTank.WaterTank_WaterPortIn;
    interface SolarToExtractor : PowerMovement connect IceProcessingMission.SolarPowerSystem.Solar_ExtractorPowerOut to IceProcessingMission.IceExtractor.IceExtractor_PowerPortIn;
    interface SolarToProcessor : PowerMovement connect IceProcessingMission.SolarPowerSystem.Solar_ProcessorPowerOut to IceProcessingMission.WaterProcessor.WaterProcessor_PowerPortIn;
    interface SolarToTank : PowerMovement connect IceProcessingMission.SolarPowerSystem.Solar_TankPowerOut to IceProcessingMission.WaterTank.WaterTank_PowerPortIn;
}

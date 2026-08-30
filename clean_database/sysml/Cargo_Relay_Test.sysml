package Cargo_Relay_Test {
    private import SysML::*;

    part CargoRelayMission {
        part CargoSource {
            part CargoSource_dims {
                attribute length = 6;
                attribute width = 6;
                attribute height = 4;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute supplyRate = 12;
            port CargoSource_CargoPortOut {
                out item CargoOut;
            }
        }

        part CargoRover {
            part CargoRover_dims {
                attribute length = 4;
                attribute width = 2.5;
                attribute height = 2;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute maxCapacity = 8;
            attribute hoursPerKm = 0.75;
            attribute energyPerKmPerKg = 0.008;
            port CargoRover_CargoPortInOut {
                in item CargoIn;
                out item CargoOut;
            }
        }

        part ForwardDepot {
            part ForwardDepot_dims {
                attribute length = 5;
                attribute width = 5;
                attribute height = 3;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            attribute storageCapacity = 100;
            port ForwardDepot_CargoPortInOut {
                in item CargoIn;
                out item CargoOut;
            }
        }

        part HabitatConsumer {
            part HabitatConsumer_dims {
                attribute length = 10;
                attribute width = 8;
                attribute height = 5;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute X = 0;
                attribute Y = 0;
                attribute Z = 0;
            }
            port Habitat_CargoPortIn {
                in item CargoIn;
            }
        }
    }

    interface def CargoMovement { end source; end target; }

    interface SourceToRover : CargoMovement connect CargoRelayMission.CargoSource.CargoSource_CargoPortOut to CargoRelayMission.CargoRover.CargoRover_CargoPortInOut;
    interface RoverToForwardDepot : CargoMovement connect CargoRelayMission.CargoRover.CargoRover_CargoPortInOut to CargoRelayMission.ForwardDepot.ForwardDepot_CargoPortInOut;
    interface ForwardDepotToHabitat : CargoMovement connect CargoRelayMission.ForwardDepot.ForwardDepot_CargoPortInOut to CargoRelayMission.HabitatConsumer.Habitat_CargoPortIn;
}

package ECLIPSE_LSP1 {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    part HabitationModule {
        part HabitationModule_dims {
            attribute length = 20;
            attribute width = 10;
            attribute height = 8;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
        }
        attribute constantPowerRate = 5;
        attribute totalEnergyConsumed = 0;
        attribute HabitationModule_volume = HabitationModule_dims.length * HabitationModule_dims.width * HabitationModule_dims.height *
                                                   HabitationModule_dims.metersPerUnit ^ 3 * 1000;

        attribute geometry = "assets/geom/HabitationModule_geom.usda";
        attribute material = "assets/mtl/steel.usda";
        port Habitation_PowerPortIn {
            in item PowerIn;
        }
    }
    part ISRUPlant {
        part ISRUPlant_dims {
            attribute length = 20;
            attribute width = 15;
            attribute height = 8;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
        }
        attribute processingRate = 1600;
        attribute regHeadGrade = 0.1;
        attribute lunarGravity = 1.62;
        attribute LOXStored = 0;
        attribute totalEnergyConsumed = 0;
        attribute ISRUPlant_volume = ISRUPlant_dims.length * ISRUPlant_dims.width * ISRUPlant_dims.height * ISRUPlant_dims.metersPerUnit ^ 3 * 1000;
        attribute geometry = "assets/geom/ISRUPlant_geom.usda";
        attribute material = "assets/mtl/steel.usda";
        attribute excavationEnergyCoeff = 6.5E-6;
        attribute transportEnergyCoeff = 3.6E-4;
        attribute liftHeight = 1;
        attribute gangueTransportDist = 1;
        attribute reactorEnergyCoeff = 0.385;
        attribute electrolysisEnergyCoeff = 8.26;
        attribute liquefactionEnergyCoeff = 1.17;
        port ISRU_LOXPortOut {
            out item LOXOut;
        }
        port ISRU_PowerPortIn {
            in item PowerIn;
        }
    }
    part LaunchLandingZone {
        part LaunchLandingZone_dims {
            attribute length = 50;
            attribute width = 50;
            attribute height = 10;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
        }
        attribute loxCapacity = 50000;
        attribute loxStored = 0;
        attribute utilitiesPowerRate = 3;
        attribute totalEnergyConsumed = 0;
        attribute chillingPowerPerKgLox = 0.31;
        attribute LaunchLandingZone_volume = LaunchLandingZone_dims.length * LaunchLandingZone_dims.width * LaunchLandingZone_dims.height *
                                                    LaunchLandingZone_dims.metersPerUnit ^ 3 * 1000;

        attribute geometry = "assets/geom/LaunchLandingZone_geom.usda";
        attribute material = "assets/mtl/steel.usda";
        port LaunchZone_PowerPortIn {
            in item PowerIn;
        }
    }
    part Propellant_Depot {
        part Propellant_Depot_dims {
            attribute length = 4;
            attribute width = 4;
            attribute height = 2.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute X = 0;
            attribute Y = 5;
            attribute Z = 0;
            attribute rX_deg = 0;
            attribute rY_deg = 0;
            attribute rZ_deg = 0;
        }
        attribute Propellant_Depot_volume = Propellant_Depot_dims.length * Propellant_Depot_dims.width * Propellant_Depot_dims.height *
                                                  Propellant_Depot_dims.metersPerUnit ^ 3 * 1000;

        attribute geometry = "assets/geom/Propellant_Depot_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
        port Propellant_LOXPortIn {
            in item LOXIn;
        }
        port Propellant_PowerPortIn {
            in item PowerIn;
        }
    }
    part Rover {
        part Rover_dims {
            attribute length = 5;
            attribute width = 3;
            attribute height = 3;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
        }
        attribute batteryCapacity = 100;
        attribute maxCapacity = 5000;
        attribute energyPerKmPerKg = 3.4E-4;
        attribute batteryCharge = 100;
        attribute totalDistanceTraveled = 0;
        attribute totalEnergyConsumed = 0;
        attribute hoursPerKm = 5;
        attribute Rover_volume = Rover_dims.length * Rover_dims.width * Rover_dims.height * Rover_dims.metersPerUnit ^ 3 * 1000;
        attribute geometry = "assets/geom/Rover_geom.usda";
        attribute material = "assets/mtl/steel.usda";
        port Rover_LOXPortInOut {
            out item LOXOut;
            in item LOXIn;
        }
        port Rover_PowerPortIn {
            in item PowerIn;
        }
    }
    part SolarPowerSystem {
        part SolarPowerSystem_dims {
            attribute length = 25;
            attribute width = 25;
            attribute height = 4;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
        }
        attribute powerOutput = 100;
        attribute powerDegradationFactor = 1;
        attribute batteryCapacity = 500;
        attribute batteryDegradationFactor = 1;
        attribute batteryCharge = 500;
        attribute totalEnergyGenerated = 0;
        attribute totalEnergyFromBattery = 0;
        attribute SolarPowerSystem_volume = SolarPowerSystem_dims.length * SolarPowerSystem_dims.width * SolarPowerSystem_dims.height *
                                                   SolarPowerSystem_dims.metersPerUnit ^ 3 * 1000;

        attribute geometry = "assets/geom/SolarPowerSystem_geom.usda";
        attribute material = "assets/mtl/steel.usda";
        port Power_PowerPortOutToRover {
            out item PowerOut;
        }
        port Power_PowerPortOutToPropellantDepot {
            out item PowerOut;
        }
        port Power_PowerPortOutToISRUPlant {
            out item PowerOut;
        }
        port Power_PowerPortOutToHabitationModule {
            out item PowerOut;
        }
        port Power_PowerPortOutToLaunchLandingZone {
            out item PowerOut;
        }
    }
    interface def LOXMovement {
        end suppliedBy;
        end consumedBy;
    }
    interface def RegolithMovement {
        end suppliedBy;
        end consumedBy;
    }
    interface def PowerMovement {
        end suppliedBy;
        end consumedBy;
    }

    interface ISRUPlantToRover : LOXMovement connect ISRUPlant.ISRU_LOXPortOut to Rover.Rover_LOXPortInOut;
    interface RoverToPropellantDepot : LOXMovement connect Rover.Rover_LOXPortInOut to Propellant_Depot.Propellant_LOXPortIn;
    interface PowerGenToPropellant : PowerMovement connect SolarPowerSystem.Power_PowerPortOutToPropellantDepot to Propellant_Depot.Propellant_PowerPortIn;
    interface PowerGenToISRUPlant : PowerMovement connect SolarPowerSystem.Power_PowerPortOutToISRUPlant to ISRUPlant.ISRU_PowerPortIn;
    interface PowerGenToHabMod : PowerMovement connect SolarPowerSystem.Power_PowerPortOutToHabitationModule to HabitationModule.Habitation_PowerPortIn;
    interface PowerGenToLaunch : PowerMovement connect SolarPowerSystem.Power_PowerPortOutToLaunchLandingZone to LaunchLandingZone.LaunchZone_PowerPortIn;
    interface PowerGenToRover : PowerMovement connect SolarPowerSystem.Power_PowerPortOutToRover to Rover.Rover_PowerPortIn;
    view ECLIPSE_LSP1 : DS_Views::SymbolicViews::iv;
}
package MissionRequirements {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    requirement <M_LSP1_001> 'Mission Duration' {
        doc /* Lunar Spaceport-1 architecture shall support a lunar surface mission of 10 days duration. */
        attribute missionDurationActual : TimeValue;
        attribute missionDurationRequired : TimeValue;
        require constraint {
            missionDurationActual >= missionDurationRequired
        }
    }
    verification def MissionDurationTest {
        private import VerificationCases::*;
        objective missionDurationVerificationObjective {
            verify 'Mission Duration';
        }
        return verdict : VerdictKind;
    }
    requirement <M_LSP1_002> 'ISRU Production Rate' {
        doc /* Lunar Spaceport-1 architecture shall support in-situ resource utilization capable of generating 1000 kg of LOX. */
        attribute loxProducedActual : MassValue;
        attribute loxProducedRequired : MassValue;
        require constraint {
            loxProducedActual >= loxProducedRequired
        }
    }
    verification def ISRUProductionTest {
        private import VerificationCases::*;
        objective loxProductionVerificationObjective {
            verify 'ISRU Production Rate';
        }
        return verdict : VerdictKind;
    }
    requirement <M_LSP1_003> 'LOX Delivery Rate' {
        doc /* Lunar Spaceport-1 architecture shall provide 1000 kg of LOX to the propellant depot. */
        attribute loxDeliveredActual : MassValue;
        attribute loxDeliveredRequired : MassValue;
        require constraint {
            loxDeliveredActual >= loxDeliveredRequired
        }
    }
    verification def LOXDeliveryTest {
        private import VerificationCases::*;
        objective loxDeliveryVerificationObjective {
            verify 'LOX Delivery Rate';
        }
        return verdict : VerdictKind;
    }
    requirement <M_LSP1_004> 'Landing Site Location' {
        doc /* Lunar Spaceport-1 architecture shall support a landing at <89.796°S, 54.9375°E>. */
        attribute landingLatitudeActual : Real;
        attribute landingLongitudeActual : Real;
        attribute landingLatitudeRequired : Real;
        attribute landingLongitudeRequired : Real;
        require constraint {
            landingLatitudeActual == landingLatitudeRequired and landingLongitudeActual == landingLongitudeRequired
        }
    }
    view MissionRequirementsTable : DS_Views::TabularViews::rt {
        expose MissionRequirements::**;
    }
}
package SubsystemRequirements {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    requirement <LSP_1> 'ISRU Plant' {
        doc 
        /* Lunar Spaceport-1 architecture shall have an ISRU processing plant to convert lunar regolith and extracted volatiles into usable propellants and consumables.*/
    }
    requirement <LSP_2> 'Regolith Rover' {
        doc 
        /* Lunar Spaceport-1 architecture shall have a regolith rover to transport excavated regolith from the ISRU excavation site to the ISRU processing plant.*/
    }
    requirement <LSP_3> 'LOX Rover' {
        doc 
        /* Lunar Spaceport-1 architecture shall have a LOX rover to transport produced liquid oxygen from theISRU processing plant to the propellant depot or landing and launch site.*/
    }
    requirement <LSP_4> 'Propellant Depot' {
        doc 
        /* Lunar Spaceport-1 architecture shall have a propellant depot to store produced propellants for use by visiting spacecraft.*/
    }
    requirement <LSP_5> 'ISRU Excavation' {
        doc 
        /* Lunar Spaceport-1 architecture shall have an ISRU excavation site to extract regolith or volatile-bearing material for processing.*/
    }
    requirement <LSP_6> 'Power Generation' {
        doc 
        /* Lunar Spaceport-1 architecture shall have a solar power generation system to provide electrical power to surface infrastructure and operations.*/
    }
    requirement <LSP_7> 'Launch and Landing Site' {
        doc 
        /* Lunar Spaceport-1 architecture shall have a landing and launch site to support spacecraft landing, refueling, and launch operations.*/
    }
    requirement <LSP_8> 'Habitation Module' {
        doc 
        /* Lunar Spaceport-1 architecture shall have a habitation module to support crew living and operational activities during lunar surface missions.*/
    }
    view SubsystemRequirementsTable : DS_Views::TabularViews::rt {
        expose SubsystemRequirements::**;
    }
}
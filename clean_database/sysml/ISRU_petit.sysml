package ECLIPSE_LSP1 {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    private import MissionRequirements::*;
    private import SubsystemRequirements::*;
    part LSP1 {
        part LSP1_dims {
            attribute length = 1000;
            attribute width = 1000;
            attribute height = 500;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
        }
        attribute missionDuration = 9;
        satisfy requirement missionDurationTest :> 'Mission Duration';
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
            satisfy requirement habitatPowerTest :> LSP1_8::LSP1_8_1;
            satisfy requirement habitatEnergyTest :> LSP1_8::LSP1_8_2;

            // BEGIN AUTO CAD METADATA: HabitationModule
            attribute cadAreaScaleFactor = 403.580063574;
            attribute cadCenterOfMassXM = 0.685675050283;
            attribute cadCenterOfMassYM = 3.28553946567;
            attribute cadCenterOfMassZM = 0.954978730281;
            attribute cadLengthScaleFactor = 20.0893022172;
            attribute cadMetadataScaleFactor = 20.0893022172;
            attribute cadSourceCenterOfMassXM = -0.0450327138669;
            attribute cadSourceCenterOfMassYM = 0.37874091546;
            attribute cadSourceCenterOfMassZM = 0.0373024441854;
            attribute cadSourceFrontAxis = "+X";
            attribute cadSourceSurfaceAreaM2 = 1.60374852394;
            attribute cadSourceUpAxis = "Z";
            attribute cadSurfaceAreaM2 = 647.240931246;
            attribute cadVolumeAvailable = false;
            attribute cadVolumeScaleFactor = 8107.64186597;
            attribute cadVolumeStatus = "mesh_not_watertight";
            // END AUTO CAD METADATA: HabitationModule

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
            attribute conversionEfficiency = 0.002527902017;
            attribute regHeadGrade = 0.1;
            attribute lunarGravity = 1.62;
            attribute LOXStored = 0;
            attribute totalEnergyConsumed = 0;
            attribute ISRUPlant_volume = ISRUPlant_dims.length * ISRUPlant_dims.width * ISRUPlant_dims.height * ISRUPlant_dims.metersPerUnit ^ 3 * 1000;
            attribute geometry = "assets/geom/ISRUPlant_geom.usda";
            attribute material = "assets/mtl/steel.usda";
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
            satisfy requirement isruProductionRateTest :> 'ISRU Production Rate';
            satisfy requirement isruProcessingRateTest :> LSP1_1::LSP1_1_1;
            satisfy requirement loxProductionTest :> LSP1_1::LSP1_1_3;
            satisfy requirement energyConsumptionTest :> LSP1_1::LSP1_1_4;
            port ISRU_RegolithPortIn {
                in item RegolithIn;
            }

            // BEGIN AUTO CAD METADATA: ISRUPlant
            attribute cadAreaScaleFactor = 19.6450829907;
            attribute cadCenterOfMassXM = 0.00773617730256;
            attribute cadCenterOfMassYM = 0.258932262227;
            attribute cadCenterOfMassZM = 1.49095969563;
            attribute cadLengthScaleFactor = 4.43227740453;
            attribute cadMetadataScaleFactor = 4.43227740453;
            attribute cadSourceCenterOfMassXM = 0.310870675744;
            attribute cadSourceCenterOfMassYM = 0.185093954844;
            attribute cadSourceCenterOfMassZM = 0.224178281065;
            attribute cadSourceFrontAxis = "+X";
            attribute cadSourceSurfaceAreaM2 = 21.3006266858;
            attribute cadSourceUpAxis = "Z";
            attribute cadSurfaceAreaM2 = 418.452578998;
            attribute cadVolumeAvailable = false;
            attribute cadVolumeScaleFactor = 87.07245745;
            attribute cadVolumeStatus = "mesh_not_watertight";
            // END AUTO CAD METADATA: ISRUPlant

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
            satisfy requirement launchZonePowerTest :> LSP1_7::LSP1_7_1;

            // BEGIN AUTO CAD METADATA: LaunchLandingZone
            attribute cadAreaScaleFactor = 57.7273618468;
            attribute cadCenterOfMassXM = 0.609205335822;
            attribute cadCenterOfMassYM = 0.844316722688;
            attribute cadCenterOfMassZM = 1.5671814238;
            attribute cadLengthScaleFactor = 7.59785244966;
            attribute cadMetadataScaleFactor = 7.59785244966;
            attribute cadSourceCenterOfMassXM = 0.080181253829;
            attribute cadSourceCenterOfMassYM = 1.06048016453;
            attribute cadSourceCenterOfMassZM = 0.205796549158;
            attribute cadSourceSurfaceAreaM2 = 32.7543266808;
            attribute cadSurfaceAreaM2 = 1890.82086835;
            attribute cadVolumeAvailable = false;
            attribute cadVolumeScaleFactor = 438.60397762;
            attribute cadVolumeStatus = "mesh_not_watertight";
            // END AUTO CAD METADATA: LaunchLandingZone

        }
        part PropellantDepot {
            part PropellantDepot_dims {
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
            attribute PropellantDepot_volume = PropellantDepot_dims.length * PropellantDepot_dims.width * PropellantDepot_dims.height *
                                                     PropellantDepot_dims.metersPerUnit ^ 3 * 1000;

            attribute geometry = "assets/geom/Propellant_Depot_geom.usda";
            attribute materialRef = "Aluminum_2219_T87";
            port Propellant_LOXPortIn {
                in item LOXIn;
            }
            port Propellant_PowerPortIn {
                in item PowerIn;
            }

            // BEGIN AUTO CAD METADATA: PropellantDepot
            attribute cadAreaScaleFactor = 59.1437042219;
            attribute cadCenterOfMassXM = 0.0441818826344;
            attribute cadCenterOfMassYM = 0.098826606475;
            attribute cadCenterOfMassZM = 0.783243752505;
            attribute cadLengthScaleFactor = 7.69049440686;
            attribute cadMetadataScaleFactor = 7.69049440686;
            attribute cadSourceCenterOfMassXM = -14.2430094959;
            attribute cadSourceCenterOfMassYM = -0.799236554259;
            attribute cadSourceCenterOfMassZM = -811.985589339;
            attribute cadSourceSurfaceAreaM2 = 0.438406535711;
            attribute cadSurfaceAreaM2 = 25.928986477;
            attribute cadVolumeAvailable = false;
            attribute cadVolumeScaleFactor = 454.844326519;
            attribute cadVolumeStatus = "mesh_not_watertight";
            // END AUTO CAD METADATA: PropellantDepot

        }
        part LOXRover {
            part LOXRover_dims {
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
            attribute LOXRover_volume = LOXRover_dims.length * LOXRover_dims.width * LOXRover_dims.height * LOXRover_dims.metersPerUnit ^ 3 * 1000;
            attribute geometry = "assets/geom/Rover_geom.usda";
            attribute material = "assets/mtl/steel.usda";
            port LOXRover_LOXPortInOut {
                out item LOXOut;
                in item LOXIn;
            }
            satisfy requirement loxRoverCapacityTest :> LSP1_3::LSP1_3_1;
            satisfy requirement loxRoverBatteryTest :> LSP1_3::LSP1_3_2;
            satisfy requirement loxRoverEnergyTest :> LSP1_3::LSP1_3_3;

            // BEGIN AUTO CAD METADATA: LOXRover
            attribute cadAreaScaleFactor = 3.84467526874;
            attribute cadCenterOfMassXM = -3.42837077193e-17;
            attribute cadCenterOfMassYM = 0.490551239096;
            attribute cadCenterOfMassZM = 1.5;
            attribute cadFormat = "STEP";
            attribute cadLengthScaleFactor = 1.96078435039;
            attribute cadMetadataScaleFactor = 1.96078435039;
            attribute cadSourceCenterOfMassXM = -1.74846906099e-17;
            attribute cadSourceCenterOfMassYM = 1.22520585723;
            attribute cadSourceCenterOfMassZM = 3.78834963215e-17;
            attribute cadSourceFile = "Viper Rover.STEP";
            attribute cadSourceFrontAxis = "+X";
            attribute cadSourceSurfaceAreaM2 = 19.714776743;
            attribute cadSourceUpAxis = "Z";
            attribute cadSourceVolumeM3 = 3.92712415182;
            attribute cadSurfaceAreaM2 = 75.7969145727;
            attribute cadVolumeAvailable = true;
            attribute cadVolumeM3 = 29.6049360512;
            attribute cadVolumeScaleFactor = 7.53857909928;
            attribute cadVolumeStatus = "available";
            // END AUTO CAD METADATA: LOXRover

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
            port Power_PowerPortOutToISRUExcavation {
                out item PowerOut;
            }
            satisfy requirement solarPowerOutputTest :> LSP1_6::LSP1_6_1;
            satisfy requirement solarBatteryCapacityTest :> LSP1_6::LSP1_6_2;
            satisfy requirement solarEnergyGenerationTest :> LSP1_6::LSP1_6_3;

            // BEGIN AUTO CAD METADATA: SolarPowerSystem
            attribute cadAreaScaleFactor = 177.777781645;
            attribute cadCenterOfMassXM = 0.454395652488;
            attribute cadCenterOfMassYM = 0.248785183066;
            attribute cadCenterOfMassZM = 0.754174470046;
            attribute cadLengthScaleFactor = 13.3333334783;
            attribute cadMetadataScaleFactor = 13.3333334783;
            attribute cadSourceCenterOfMassXM = 0.00790950754972;
            attribute cadSourceCenterOfMassYM = 0.0194416118803;
            attribute cadSourceCenterOfMassZM = 0.0565630057093;
            attribute cadSourceSurfaceAreaM2 = 1.37934411445;
            attribute cadSurfaceAreaM2 = 245.216736791;
            attribute cadVolumeAvailable = false;
            attribute cadVolumeScaleFactor = 2370.37044771;
            attribute cadVolumeStatus = "mesh_not_watertight";
            // END AUTO CAD METADATA: SolarPowerSystem

        }
        part RegolithRover {
            part RegolithRover_dims {
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
            attribute RegolithRover_volume = RegolithRover_dims.length * RegolithRover_dims.width * RegolithRover_dims.height *
                                                    RegolithRover_dims.metersPerUnit ^ 3 * 1000;

            attribute geometry = "assets/geom/Rover_geom.usda";
            attribute material = "assets/mtl/steel.usda";
            port RegolithRover_RegolithPortInOut {
                out item RegolithOut;
                in item RegolithIn;
            }
            satisfy requirement regolithRoverCapacityTest :> LSP1_2::LSP1_2_1;
            satisfy requirement regolithRoverEnergyTest :> LSP1_2::LSP1_2_3;
            satisfy requirement regolithRoverBatteryTest :> LSP1_2::LSP1_2_4;
            satisfy requirement regolithRoverRangeTest :> LSP1_2::LSP1_2_5;

            // BEGIN AUTO CAD METADATA: RegolithRover
            attribute cadAreaScaleFactor = 3.84467526874;
            attribute cadCenterOfMassXM = -3.42837077193e-17;
            attribute cadCenterOfMassYM = 0.490551239096;
            attribute cadCenterOfMassZM = 1.5;
            attribute cadFormat = "STEP";
            attribute cadLengthScaleFactor = 1.96078435039;
            attribute cadMetadataScaleFactor = 1.96078435039;
            attribute cadSourceCenterOfMassXM = -1.74846906099e-17;
            attribute cadSourceCenterOfMassYM = 1.22520585723;
            attribute cadSourceCenterOfMassZM = 3.78834963215e-17;
            attribute cadSourceFile = "Viper Rover.STEP";
            attribute cadSourceFrontAxis = "+X";
            attribute cadSourceSurfaceAreaM2 = 19.714776743;
            attribute cadSourceUpAxis = "Z";
            attribute cadSourceVolumeM3 = 3.92712415182;
            attribute cadSurfaceAreaM2 = 75.7969145727;
            attribute cadVolumeAvailable = true;
            attribute cadVolumeM3 = 29.6049360512;
            attribute cadVolumeScaleFactor = 7.53857909928;
            attribute cadVolumeStatus = "available";
            // END AUTO CAD METADATA: RegolithRover

        }
        part ISRUExcavation {
            part ISRUExcavation_dims {
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
            attribute ISRUExcavation_volume = ISRUExcavation_dims.length * ISRUExcavation_dims.width * ISRUExcavation_dims.height *
                                                     ISRUExcavation_dims.metersPerUnit ^ 3 * 1000;
            attribute excavationEnergyCoeff = 6.5E-6;
            attribute geometry = "assets/geom/ISRUExcavation_geom.usda";
            attribute materialRef = "Aluminum_2219_T87";
            port Excavation_PowerPortIn {
                in item PowerIn;
            }
            port Excavation_RegolithPortOut {
                out item RegolithOut;
            }
            satisfy requirement excavationEnergyCoeffTest :> LSP1_5::LSP1_5_2;

            // BEGIN AUTO CAD METADATA: ISRUExcavation
            attribute cadAreaScaleFactor = 0.374614236272;
            attribute cadCenterOfMassXM = -0.131913291676;
            attribute cadCenterOfMassYM = -0.0892818044328;
            attribute cadCenterOfMassZM = 0.12265806199;
            attribute cadLengthScaleFactor = 0.612057379885;
            attribute cadMetadataScaleFactor = 0.612057379885;
            attribute cadSourceCenterOfMassXM = 0.251615315939;
            attribute cadSourceCenterOfMassYM = 0.20146750712;
            attribute cadSourceCenterOfMassZM = 0.0135780763968;
            attribute cadSourceSurfaceAreaM2 = 25.663819114;
            attribute cadSurfaceAreaM2 = 9.61403199719;
            attribute cadVolumeAvailable = false;
            attribute cadVolumeScaleFactor = 0.22928540792;
            attribute cadVolumeStatus = "mesh_not_watertight";
            // END AUTO CAD METADATA: ISRUExcavation

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
    interface ISRUPlantToRover : LOXMovement connect LSP1.LOXRover.LOXRover_LOXPortInOut to LSP1.ISRUPlant.ISRU_LOXPortOut;
    interface RoverToPropellantDepot : LOXMovement connect LSP1.LOXRover.LOXRover_LOXPortInOut to LSP1.PropellantDepot.Propellant_LOXPortIn;
    interface PowerGenToPropellant : PowerMovement
            connect LSP1.SolarPowerSystem.Power_PowerPortOutToPropellantDepot
            to LSP1.PropellantDepot.Propellant_PowerPortIn;

    interface PowerGenToISRUPlant : PowerMovement connect LSP1.SolarPowerSystem.Power_PowerPortOutToISRUPlant to LSP1.ISRUPlant.ISRU_PowerPortIn;
    interface PowerGenToHabMod : PowerMovement connect LSP1.SolarPowerSystem.Power_PowerPortOutToHabitationModule to LSP1.HabitationModule.Habitation_PowerPortIn;
    interface PowerGenToLaunch : PowerMovement
            connect LSP1.SolarPowerSystem.Power_PowerPortOutToLaunchLandingZone
            to LSP1.LaunchLandingZone.LaunchZone_PowerPortIn;

    verification ISRUProductionTest {
        private import VerificationCases::*;
        private import MissionRequirements::*;
        subject target :> LSP1.ISRUPlant = LSP1.ISRUPlant;
        objective loxProductionObj {
            verify 'ISRU Production Rate' {
                subject a = target;
            }
        }
        return verdict : VerdictKind = PassIf(loxProductionObj());
    }
    verification MissionDurationTest {
        private import VerificationCases::*;
        private import MissionRequirements::*;
        subject target :> LSP1 = LSP1;
        objective missionDurationObj {
            verify 'Mission Duration' {
                subject a = target;
            }
        }
        return verdict : VerdictKind = PassIf(missionDurationObj());
    }
    verification ISRUProcessingRateTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.ISRUPlant = LSP1.ISRUPlant;

        objective processingRateObj {
            verify LSP1_1::LSP1_1_1 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(processingRateObj());
    }

    verification ISRU_LOXProductionTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.ISRUPlant = LSP1.ISRUPlant;

        objective loxStoredObj {
            verify LSP1_1::LSP1_1_3 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(loxStoredObj());
    }

    verification ISRU_EnergyConsumptionTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.ISRUPlant = LSP1.ISRUPlant;

        objective energyObj {
            verify LSP1_1::LSP1_1_4 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(energyObj());
    }


    verification RegolithRoverCapacityTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.RegolithRover = LSP1.RegolithRover;

        objective capacityObj {
            verify LSP1_2::LSP1_2_1 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(capacityObj());
    }

    verification RegolithRoverEnergyTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.RegolithRover = LSP1.RegolithRover;

        objective energyObj {
            verify LSP1_2::LSP1_2_3 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(energyObj());
    }

    verification RegolithRoverBatteryTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.RegolithRover = LSP1.RegolithRover;

        objective batteryObj {
            verify LSP1_2::LSP1_2_4 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(batteryObj());
    }

    verification RegolithRoverRangeTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.RegolithRover = LSP1.RegolithRover;

        objective rangeObj {
            verify LSP1_2::LSP1_2_5 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(rangeObj());
    }


    verification LOXRoverCapacityTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.LOXRover = LSP1.LOXRover;

        objective capacityObj {
            verify LSP1_3::LSP1_3_1 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(capacityObj());
    }

    verification LOXRoverBatteryTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.LOXRover = LSP1.LOXRover;

        objective batteryObj {
            verify LSP1_3::LSP1_3_2 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(batteryObj());
    }

    verification LOXRoverEnergyTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.LOXRover = LSP1.LOXRover;

        objective energyObj {
            verify LSP1_3::LSP1_3_3 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(energyObj());
    }


    verification ISRUExcavationEnergyCoeffTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.ISRUPlant = LSP1.ISRUPlant;

        objective excavationCoeffObj {
            verify LSP1_5::LSP1_5_2 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(excavationCoeffObj());
    }


    verification SolarPowerOutputTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.SolarPowerSystem = LSP1.SolarPowerSystem;

        objective powerObj {
            verify LSP1_6::LSP1_6_1 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(powerObj());
    }

    verification SolarBatteryCapacityTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.SolarPowerSystem = LSP1.SolarPowerSystem;

        objective batteryObj {
            verify LSP1_6::LSP1_6_2 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(batteryObj());
    }

    verification SolarEnergyGenerationTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.SolarPowerSystem = LSP1.SolarPowerSystem;

        objective energyObj {
            verify LSP1_6::LSP1_6_3 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(energyObj());
    }


    verification LaunchZonePowerTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.LaunchLandingZone = LSP1.LaunchLandingZone;

        objective powerObj {
            verify LSP1_7::LSP1_7_1 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(powerObj());
    }


    verification HabitatPowerTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.HabitationModule = LSP1.HabitationModule;

        objective powerObj {
            verify LSP1_8::LSP1_8_1 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(powerObj());
    }

    verification HabitatEnergyTest {
        private import VerificationCases::*;
        private import SubsystemRequirements::*;
        subject target :> LSP1.HabitationModule = LSP1.HabitationModule;

        objective energyObj {
            verify LSP1_8::LSP1_8_2 {
                subject a = target;
            }
        }

        return verdict : VerdictKind = PassIf(energyObj());
    }
    view ECLIPSE_LSP1_Interfaces : DS_Views::SymbolicViews::iv;
    view ECLIPSE_LSP1_General : DS_Views::SymbolicViews::gv;
    interface connect LSP1::SolarPowerSystem.Power_PowerPortOutToISRUExcavation to LSP1::ISRUExcavation.Excavation_PowerPortIn;
    interface ISRUExcavationToRegolithRover : RegolithMovement
            connect LSP1::ISRUExcavation.Excavation_RegolithPortOut
            to LSP1::RegolithRover.RegolithRover_RegolithPortInOut;

    interface RegolithRoverToISRUPlant : RegolithMovement connect LSP1::RegolithRover.RegolithRover_RegolithPortInOut to LSP1::ISRUPlant.ISRU_RegolithPortIn;
    interface PowerGenToISRUExcavation : PowerMovement
            connect LSP1::SolarPowerSystem.Power_PowerPortOutToISRUExcavation
            to LSP1::ISRUExcavation.Excavation_PowerPortIn;
}
package MissionRequirements {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    private import ECLIPSE_LSP1::*;
    requirement <M_LSP1_001> 'Mission Duration' {
        doc /* Lunar Spaceport-1 architecture shall support a lunar surface mission of 10 days duration. */
        subject lsp1 :> LSP1;
        require constraint {
            lsp1.missionDuration >= 10
        }
    }
     requirement <M_LSP1_002> 'ISRU Production Rate' {
        doc /* Lunar Spaceport-1 architecture shall support in-situ resource utilization capable of generating 1000 kg of LOX per hour. */
        subject isruPlant :> LSP1.ISRUPlant;
        require constraint {
            isruPlant.processingRate >= 1000
        }
    }
    requirement <M_LSP1_003> 'LOX Delivery Rate' {
        doc /* Lunar Spaceport-1 architecture shall provide 1000 kg of LOX to the propellant depot per hour. */
        attribute loxDeliveredActual : MassValue;
        attribute loxDeliveredRequired : MassValue;
        require constraint {
            loxDeliveredActual >= loxDeliveredRequired
        }
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
    private import ECLIPSE_LSP1::*;
    requirement <LSP1_1> 'ISRU Plant' {
        doc /* Lunar Spaceport-1 architecture shall have an ISRU processing plant to convert lunar regolith and extracted volatiles into usable propellants and consumables.*/

        requirement <LSP1_1_1> 'Minimum Processing Rate' {
            doc /* The ISRU processing plant shall maintain a regolith processing rate greater than or equal to 1600 kg/hr.*/
            subject isruPlant :> LSP1.ISRUPlant;
            require constraint {
                isruPlant.processingRate >= 1600
            }
        }
        requirement <LSP1_1_2> 'Minimum Regolith Intake' {
            doc /* The ISRU processing plant shall receive at least 4000 kg of regolith during a mission simulation.*/
            // No direct attribute → needs simulation variable
        }
        requirement <LSP1_1_3> 'Minimum LOX Production' {
            doc /* The ISRU processing plant shall produce at least 10 kg of liquid oxygen during a mission simulation.*/
            subject isruPlant :> LSP1.ISRUPlant;
            require constraint {
                isruPlant.LOXStored >= 10
            }
        }
        requirement <LSP1_1_4> 'Maximum Plant Energy Consumption' {
            doc /* The ISRU processing plant shall not consume more than 300 kWh of energy during a single regolith processing cycle.*/
            subject isruPlant :> LSP1.ISRUPlant;
            require constraint {
                isruPlant.totalEnergyConsumed <= 300
            }
        }
        requirement <LSP1_1_5> 'Minimum Plant Processing Uptime' {
            doc /* The ISRU processing plant shall maintain at least 2 hours of processing uptime during a mission simulation.*/
            // No uptime attribute → simulation-derived
        }
    }
    requirement <LSP1_2> 'Regolith Rover' {
        doc /* Lunar Spaceport-1 architecture shall have a regolith rover to transport excavated regolith from the ISRU excavation site to the ISRU processing plant.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_2_1> 'Minimum Cargo Capacity' {
            doc /* The regolith rover shall support a cargo capacity greater than or equal to 5000 kg.*/
            require constraint {
                lsp1.RegolithRover.maxCapacity >= 5000
            }
        }
        requirement <LSP1_2_2> 'Minimum Regolith Delivery Load' {
            doc /* The regolith rover shall transport at least 4000 kg of regolith per delivery mission.*/
            // No direct attribute
        }
        requirement <LSP1_2_3> 'Maximum Rover Energy Consumption' {
            doc /* The regolith rover shall not consume more than 5 kWh of energy per transport mission.*/
            require constraint {
                lsp1.RegolithRover.totalEnergyConsumed <= 5
            }
        }
        requirement <LSP1_2_4> 'Minimum Rover Battery Capacity' {
            doc /* The regolith rover shall maintain a battery capacity greater than or equal to 100 kWh.*/
            require constraint {
                lsp1.RegolithRover.batteryCapacity >= 100
            }
        }
        requirement <LSP1_2_5> 'Minimum Rover Range Capability' {
            doc /* The regolith rover shall travel at least 2 km during a mission simulation.*/
            require constraint {
                lsp1.RegolithRover.totalDistanceTraveled >= 2
            }
        }
    }

    requirement <LSP1_3> 'LOX Rover' {
        doc /* Lunar Spaceport-1 architecture shall have a LOX rover to transport produced liquid oxygen from the ISRU processing plant to the propellant depot or landing and launch site.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_3_1> 'Minimum LOX Rover Cargo Capacity' {
            doc /* The LOX rover shall support a cargo capacity greater than or equal to 5000 kg.*/
            require constraint {
                lsp1.LOXRover.maxCapacity >= 5000
            }
        }
        requirement <LSP1_3_2> 'Minimum Rover Battery Capacity' {
            doc /* The LOX rover shall maintain a battery capacity greater than or equal to 100 kWh.*/
            require constraint {
                lsp1.LOXRover.batteryCapacity >= 100
            }
        }
        requirement <LSP1_3_3> 'Maximum Rover Energy Consumption' {
            doc /* The LOX rover shall not consume more than 5 kWh of energy per transport mission.*/
            require constraint {
                lsp1.LOXRover.totalEnergyConsumed <= 5
            }
        }
    }

    requirement <LSP1_4> 'Propellant Depot' {
        doc /* Lunar Spaceport-1 architecture shall have a propellant depot to store produced propellants for use by visiting spacecraft.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_4_1> 'Minimum LOX Storage Capacity' {
            doc /* The propellant depot shall maintain liquid oxygen storage capacity greater than or equal to 50000 kg.*/
            // No explicit capacity attribute in part → missing
        }
        requirement <LSP1_4_2> 'Minimum LOX Inventory Capability' {
            doc /* The propellant depot shall store at least 10 kg of delivered liquid oxygen during a mission simulation.*/
            // No LOXStored attribute in PropellantDepot
        }
    }

    requirement <LSP1_5> 'ISRU Excavation' {
        doc /* Lunar Spaceport-1 architecture shall have an ISRU excavation site to extract regolith or volatile-bearing material for processing.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_5_1> 'Minimum Excavation Delivery Mass' {
            doc /* The excavation system shall deliver at least 4000 kg of regolith to the ISRU plant during a mission simulation.*/
            // No attribute
        }
        requirement <LSP1_5_2> 'Maximum Excavation Energy Coefficient' {
            doc /* The excavation system shall maintain an excavation energy coefficient less than or equal to 6.5e-06 kWh per kg.*/
            require constraint {
                lsp1.ISRUExcavation.excavationEnergyCoeff <= 6.5E-6
            }
        }
    }

    requirement <LSP1_6> 'Power Generation' {
        doc /* Lunar Spaceport-1 architecture shall have a solar power generation system to provide electrical power to surface infrastructure and operations.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_6_1> 'Minimum Solar Power Output' {
            doc /* The solar power generation system shall produce electrical power greater than or equal to 100 kW during operations.*/
            require constraint {
                lsp1.SolarPowerSystem.powerOutput >= 100
            }
        }
        requirement <LSP1_6_2> 'Minimum Battery Storage Capacity' {
            doc /* The solar power system shall maintain battery storage capacity greater than or equal to 500 kWh.*/
            require constraint {
                lsp1.SolarPowerSystem.batteryCapacity >= 500
            }
        }
        requirement <LSP1_6_3> 'Minimum Energy Generation' {
            doc /* The solar power system shall generate at least 500 kWh of electrical energy during a mission simulation.*/
            require constraint {
                lsp1.SolarPowerSystem.totalEnergyGenerated >= 500
            }
        }
    }

    requirement <LSP1_7> 'Launch and Landing Site' {
        doc /* Lunar Spaceport-1 architecture shall have a landing and launch site to support spacecraft landing, refueling, and launch operations.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_7_1> 'Maximum Utility Power Consumption' {
            doc /* The landing and launch site shall maintain utility power consumption less than or equal to 3 kW during operations.*/
            require constraint {
                lsp1.LaunchLandingZone.utilitiesPowerRate <= 3
            }
        }
    }

    requirement <LSP1_8> 'Habitation Module' {
        doc /* Lunar Spaceport-1 architecture shall have a habitation module to support crew living and operational activities during lunar surface missions.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_8_1> 'Maximum Habitat Continuous Power' {
            doc /* The habitation module shall maintain continuous electrical power consumption less than or equal to 5 kW.*/
            require constraint {
                lsp1.HabitationModule.constantPowerRate <= 5
            }
        }
        requirement <LSP1_8_2> 'Maximum Habitat Energy Consumption' {
            doc /* The habitation module shall not consume more than 50 kWh of energy during a 10 hour mission period.*/
            require constraint {
                lsp1.HabitationModule.totalEnergyConsumed <= 50
            }
        }
    }

    requirement <LSP1_9> 'Communications Module' {
        doc /* Lunar Spaceport-1 architecture shall have a communications system to support lunar surface communications and telemetry.*/
        subject lsp1 :> LSP1;

        requirement <LSP1_9_1> 'Maximum Communications Power Consumption' {
            doc /* The communications module shall maintain continuous electrical power consumption less than or equal to 2 kW.*/
            // No communications module in model
        }
        requirement <LSP1_9_2> 'Maximum Communications Energy Consumption' {
            doc /* The communications module shall not consume more than 20 kWh of energy during a 10 hour mission period.*/
            // No communications module in model
        }
    }
    view SubsystemRequirementsTable : DS_Views::TabularViews::rt {
        expose SubsystemRequirements::**;
    }
}

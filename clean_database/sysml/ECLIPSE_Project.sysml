package ECLIPSE_LSP1 {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    part HabitationModule {
        part HabitationModule_dims {
            attribute length = 6;
            attribute width = 3;
            attribute height = 2.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute X = 30;
            attribute Y = 0;
            attribute Z = 0;
            attribute rX_deg = 0;
            attribute rY_deg = 0;
            attribute rZ_deg = 0;
        }
        attribute HabitationModule_volume = HabitationModule_dims.length * HabitationModule_dims.width * HabitationModule_dims.height *
                                                  HabitationModule_dims.metersPerUnit ^ 3 * 1000;

        attribute materialRef = "Titanium_Ti6Al4V";
        metadata def material_used;
    }
    part ISRU_PLANT {
        part ISRU_PLANT_dims {
            attribute length = 5;
            attribute width = 4;
            attribute height = 2;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute X = 10;
            attribute Y = 0;
            attribute Z = 0;
            attribute rX_deg = 0;
            attribute rY_deg = 0;
            attribute rZ_deg = 0;
        }
        attribute ISRU_PLANT_volume = ISRU_PLANT_dims.length * ISRU_PLANT_dims.width * ISRU_PLANT_dims.height * ISRU_PLANT_dims.metersPerUnit ^ 3 * 1000;
        attribute geometry = "assets/geom/ISRU_PLANT_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
        port ISRU_LOXPortOut {
            out item LOXOut;
        }
    }
    part landing_site {
        part landing_site_dims {
            attribute length = 1;
            attribute width = 1;
            attribute height = 0.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute X = 0;
            attribute Y = 0;
            attribute Z = 0;
            attribute rX_deg = 0;
            attribute rY_deg = 0;
            attribute rZ_deg = 0;
        }
        attribute landing_site_volume = landing_site_dims.length * landing_site_dims.width * landing_site_dims.height * landing_site_dims.metersPerUnit ^ 3 * 1000;
        attribute geometry = "assets/geom/landing_site_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
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
    }
    part Rover {
        part Rover_dims {
            attribute length = 4;
            attribute width = 2;
            attribute height = 1.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute X = 9;
            attribute Y = 0;
            attribute Z = 0;
            attribute rX_deg = 0;
            attribute rY_deg = 0;
            attribute rZ_deg = 0;
        }
        attribute Rover_volume = Rover_dims.length * Rover_dims.width * Rover_dims.height * Rover_dims.metersPerUnit ^ 3 * 1000;
        attribute geometry = "assets/geom/Rover_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
        port RoverFleet_LOXPortInOut {
            out item LOXOut;
            in item LOXIn;
        }
    }
    interface def LOXMovement {
        end suppliedBy;
        end consumedBy;
    }
    interface ISRUPlantToRover : LOXMovement connect Rover.RoverFleet_LOXPortInOut to ISRU_PLANT.ISRU_LOXPortOut;
    interface RoverToPropellantDepot : LOXMovement connect Rover.RoverFleet_LOXPortInOut to Propellant_Depot.Propellant_LOXPortIn;
    view ECLIPSE_LSP1 : DS_Views::SymbolicViews::gv;
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
package 'Vehicle Requirements' {
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;
    requirement LSP_2 {
        doc 
        /* The spaceport shall support safe, controlled extraction, processing,
         * storage, and distribution of lunar resources. */
    }
    requirement LSP_2_1 :> LSP_2 {
        doc /* The spaceport shall support extraction of lunar resources. */
    }
    requirement LSP_2_1_1 :> LSP_2_1 {
        doc 
        /* The spaceport shall support mechanized excavation and collection
         * of lunar regolith sufficient to supply continuous ISRU operations. */
    }
    requirement LSP_2_1_1_1 :> LSP_2_1_1 {
        doc 
        /* The excavation system shall support regolith collection sufficient
         * to enable ≥ 1 kg O2/hr production at the ISRU extraction system. */
        attribute o2ProductionSupported : MassFlowRateValue;
        attribute o2ProductionRequired : MassFlowRateValue;
        require constraint {
            o2ProductionSupported >= o2ProductionRequired
        }
    }
    requirement LSP_2_1_2 :> LSP_2_1 {
        doc 
        /* The spaceport shall support excavation throughput matched to
         * downstream ISRU mass-flow demand. */
    }
    requirement LSP_2_1_2_1 :> LSP_2_1_2 {
        doc /* The spaceport shall support simultaneous operation of ≥ 5 excavators. */
        attribute excavatorsActual : Integer;
        attribute excavatorsRequired : Integer;
        require constraint {
            excavatorsActual >= excavatorsRequired
        }
    }
    requirement LSP_2_1_3 :> LSP_2_1 {
        doc /* The spaceport shall support mobile excavation operations. */
    }
    requirement LSP_2_1_3_1 :> LSP_2_1_3 {
        doc /* The spaceport shall support excavation power demand of at least 1 kW per excavator. */
        attribute powerAvailable : PowerValue;
        attribute powerRequired : PowerValue;
        require constraint {
            powerAvailable >= powerRequired
        }
    }
    requirement LSP_2_1_4 :> LSP_2_1 {
        doc 
        /* The spaceport shall support electrical energy provision, storage,
         * and recharge for sustained excavation operations. */
    }
    requirement LSP_2_2 :> LSP_2 {
        doc /* The spaceport shall process extracted materials into usable products. */
    }
    requirement LSP_2_2_1 :> LSP_2_2 {
        doc /* The spaceport shall support chemical or electrochemical conversion of regolith. */
    }
    requirement LSP_2_2_1_1 :> LSP_2_2_1 {
        doc /* The ISRU subsystem shall produce ≥ 1 kg O2/hr under nominal conditions. */
        attribute o2Produced : MassFlowRateValue;
        attribute o2Required : MassFlowRateValue;
        require constraint {
            o2Produced >= o2Required
        }
    }
    requirement LSP_2_2_1_1_1 :> LSP_2_2_1_1 {
        doc /* ISRU excavation operations shall be compatible with local regolith properties. */
    }
    requirement LSP_2_2_1_1_2 :> LSP_2_2_1_1 {
        doc /* ISRU excavation system placement shall account for spatial variability of regolith properties. */
    }
    requirement LSP_2_2_2 :> LSP_2_2 {
        doc /* The spaceport shall support multiple ISRU extraction pathways. */
    }
    requirement LSP_2_2_2_1 :> LSP_2_2_2 {
        doc /* Hydrogen-reduction extraction shall be supported at 13 kW thermal per 1 kg O2/hr. */
        attribute thermalPowerProvided : PowerValue;
        attribute thermalPowerRequired : PowerValue;
        require constraint {
            thermalPowerProvided >= thermalPowerRequired
        }
    }
    requirement LSP_2_2_2_2 :> LSP_2_2_2 {
        doc /* Carbothermal extraction shall be supported at 28.6 kW thermal per 1 kg O2/hr. */
        attribute thermalPowerProvided : PowerValue;
        attribute thermalPowerRequired : PowerValue;
        require constraint {
            thermalPowerProvided >= thermalPowerRequired
        }
    }
    requirement LSP_2_2_2_3 :> LSP_2_2_2 {
        doc /* Molten-regolith electrolysis shall be supported at 30.1 kW electrical per 1 kg O2/hr. */
        attribute electricalPowerProvided : PowerValue;
        attribute electricalPowerRequired : PowerValue;
        require constraint {
            electricalPowerProvided >= electricalPowerRequired
        }
    }
    requirement LSP_2_2_3 :> LSP_2_2 {
        doc /* The spaceport shall support electrolysis of produced water. */
    }
    requirement LSP_2_2_4 :> LSP_2_2 {
        doc /* The spaceport shall support scaling of extraction output based on available power and regolith supply. */
    }
    requirement LSP_2_3 :> LSP_2 {
        doc /* The spaceport shall safely store processed resources in lunar environmental conditions. */
    }
    requirement LSP_2_3_1 :> LSP_2_3 {
        doc /* The spaceport shall support cryogenic storage of oxygen products. */
    }
    requirement LSP_2_3_1_1 :> LSP_2_3_1 {
        doc /* Liquid oxygen shall be stored at 90 K using active cryogenic cooling. */
        attribute temperatureActual : TemperatureValue;
        attribute temperatureRequired : TemperatureValue;
        require constraint {
            temperatureActual <= temperatureRequired
        }
    }
    requirement LSP_2_3_2 :> LSP_2_3 {
        doc /* The spaceport shall support cryogenic storage of hydrogen when produced. */
    }
    requirement LSP_2_3_2_1 :> LSP_2_3_2 {
        doc /* Liquid hydrogen shall be stored at 20 K using multi-stage cryogenic cooling. */
        attribute temperatureActual : TemperatureValue;
        attribute temperatureRequired : TemperatureValue;
        require constraint {
            temperatureActual <= temperatureRequired
        }
    }
    requirement LSP_2_3_3 :> LSP_2_3 {
        doc /* The spaceport shall support active thermal control and boil-off mitigation. */
    }
    requirement LSP_2_4 :> LSP_2 {
        doc /* The spaceport shall maintain safe separation between ISRU operations and crewed zones. */
    }
    requirement LSP_2_4_1 :> LSP_2_4 {
        doc /* The ISRU subsystem shall limit propagation of dust or debris toward crewed zones. */
    }
    requirement LSP_2_4_1_1 :> LSP_2_4_1 {
        doc /* Airborne dust concentration at crewed zone boundary shall be ≤ 0.1 mg/m3. */
        attribute dustActual : MassConcentrationValue;
        attribute dustLimit : MassConcentrationValue;
        require constraint {
            dustActual <= dustLimit
        }
    }
    requirement LSP_2_4_2 :> LSP_2_4 {
        doc /* The ISRU subsystem shall implement keep-out zones. */
    }
    requirement LSP_2_4_2_1 :> LSP_2_4_2 {
        doc /* An exclusion zone with minimum radius of 100 meters shall be established. */
        attribute radiusActual : LengthValue;
        attribute radiusRequired : LengthValue;
        require constraint {
            radiusActual >= radiusRequired
        }
    }
    requirement LSP_2_4_3 :> LSP_2_4 {
        doc /* ISRU facilities shall prevent hazardous environmental propagation toward crewed areas. */
    }
    requirement LSP_2_5 :> LSP_2 {
        doc /* The spaceport shall provide rapid, safe shutdown and purge capabilities. */
    }
    requirement LSP_2_5_1 :> LSP_2_5 {
        doc /* The ISRU subsystem abort shall be capable of being commanded by crew or Earth ground systems. */
    }
    requirement LSP_2_5_1_1 :> LSP_2_5_1 {
        doc /* The ISRU subsystem shall transition to a safe shutdown state within 30 seconds of commanded abort. */
        attribute shutdownTimeActual : TimeValue;
        attribute shutdownTimeRequired : TimeValue;
        require constraint {
            shutdownTimeActual <= shutdownTimeRequired
        }
    }
    requirement LSP_2_5_1_3 :> LSP_2_5_1 {
        doc /* The ISRU subsystem extraction processes shall abort if thermal limits exceed defined thresholds. */
    }
    requirement LSP_2_5_2 :> LSP_2_5 {
        doc /* The ISRU subsystem shall provide purge or depressurization capability for hazardous process volumes. */
    }
}
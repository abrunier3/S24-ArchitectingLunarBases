package 'Vehicle Requirements' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    // ============================================================
    // 2 - Top Level
    // ============================================================

    requirement LSP_2 {
        doc /* The spaceport shall support safe, controlled extraction, processing,
        storage, and distribution of lunar resources. */
    }

    // ============================================================
    // 2.1 Excavation
    // ============================================================

    requirement LSP_2_1 :> LSP_2 {
        doc /* The spaceport shall support extraction of lunar resources. */
    }

    requirement LSP_2_1_1 :> LSP_2_1 {
        doc /* The spaceport shall support mechanized excavation and collection
        of lunar regolith sufficient to supply continuous ISRU operations. */
    }

    requirement LSP_2_1_1_1 :> LSP_2_1_1 {
        doc /* The excavation system shall support regolith collection sufficient
        to enable ≥ 1 kg O2/hr production at the ISRU extraction system. */
        attribute o2ProductionSupported : MassFlowRateValue;
        attribute o2ProductionRequired : MassFlowRateValue;
        require constraint { o2ProductionSupported >= o2ProductionRequired }
    }

    requirement LSP_2_1_2 :> LSP_2_1 {
        doc /* The spaceport shall support excavation throughput matched to
        downstream ISRU mass-flow demand. */
    }

    requirement LSP_2_1_2_1 :> LSP_2_1_2 {
        doc /* The spaceport shall support simultaneous operation of ≥ 5 excavators. */
        attribute excavatorsActual : Integer;
        attribute excavatorsRequired : Integer;
        require constraint { excavatorsActual >= excavatorsRequired }
    }

    requirement LSP_2_1_3 :> LSP_2_1 {
        doc /* The spaceport shall support mobile excavation operations. */
    }

    requirement LSP_2_1_3_1 :> LSP_2_1_3 {
        doc /* The spaceport shall support excavation power demand of at least 1 kW per excavator. */
        attribute powerAvailable : PowerValue;
        attribute powerRequired : PowerValue;
        require constraint { powerAvailable >= powerRequired }
    }

    requirement LSP_2_1_4 :> LSP_2_1 {
        doc /* The spaceport shall support electrical energy provision, storage,
        and recharge for sustained excavation operations. */
    }

    // ============================================================
    // 2.2 Extraction
    // ============================================================

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
        require constraint { o2Produced >= o2Required }
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
        require constraint { thermalPowerProvided >= thermalPowerRequired }
    }

    requirement LSP_2_2_2_2 :> LSP_2_2_2 {
        doc /* Carbothermal extraction shall be supported at 28.6 kW thermal per 1 kg O2/hr. */
        attribute thermalPowerProvided : PowerValue;
        attribute thermalPowerRequired : PowerValue;
        require constraint { thermalPowerProvided >= thermalPowerRequired }
    }

    requirement LSP_2_2_2_3 :> LSP_2_2_2 {
        doc /* Molten-regolith electrolysis shall be supported at 30.1 kW electrical per 1 kg O2/hr. */
        attribute electricalPowerProvided : PowerValue;
        attribute electricalPowerRequired : PowerValue;
        require constraint { electricalPowerProvided >= electricalPowerRequired }
    }

    requirement LSP_2_2_3 :> LSP_2_2 {
        doc /* The spaceport shall support electrolysis of produced water. */
    }

    requirement LSP_2_2_4 :> LSP_2_2 {
        doc /* The spaceport shall support scaling of extraction output based on available power and regolith supply. */
    }

    // ============================================================
    // 2.3 Storage
    // ============================================================

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
        require constraint { temperatureActual <= temperatureRequired }
    }

    requirement LSP_2_3_2 :> LSP_2_3 {
        doc /* The spaceport shall support cryogenic storage of hydrogen when produced. */
    }

    requirement LSP_2_3_2_1 :> LSP_2_3_2 {
        doc /* Liquid hydrogen shall be stored at 20 K using multi-stage cryogenic cooling. */
        attribute temperatureActual : TemperatureValue;
        attribute temperatureRequired : TemperatureValue;
        require constraint { temperatureActual <= temperatureRequired }
    }

    requirement LSP_2_3_3 :> LSP_2_3 {
        doc /* The spaceport shall support active thermal control and boil-off mitigation. */
    }

    // ============================================================
    // 2.4 Safety
    // ============================================================

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
        require constraint { dustActual <= dustLimit }
    }

    requirement LSP_2_4_2 :> LSP_2_4 {
        doc /* The ISRU subsystem shall implement keep-out zones. */
    }

    requirement LSP_2_4_2_1 :> LSP_2_4_2 {
        doc /* An exclusion zone with minimum radius of 100 meters shall be established. */
        attribute radiusActual : LengthValue;
        attribute radiusRequired : LengthValue;
        require constraint { radiusActual >= radiusRequired }
    }

    requirement LSP_2_4_3 :> LSP_2_4 {
        doc /* ISRU facilities shall prevent hazardous environmental propagation toward crewed areas. */
    }

    // ============================================================
    // 2.5 Contingency Operations
    // ============================================================

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
        require constraint { shutdownTimeActual <= shutdownTimeRequired }
    }

    requirement LSP_2_5_1_3 :> LSP_2_5_1 {
        doc /* The ISRU subsystem extraction processes shall abort if thermal limits exceed defined thresholds. */
    }

    requirement LSP_2_5_2 :> LSP_2_5 {
        doc /* The ISRU subsystem shall provide purge or depressurization capability for hazardous process volumes. */
    }
}
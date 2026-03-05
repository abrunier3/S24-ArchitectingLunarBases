package 'Mission Requirements' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    // ============================================================
    // M-LSP1-001 — Mission Duration
    // ============================================================

    requirement M_LSP1_001 {
        doc /* Lunar Spaceport-1 architecture shall support a lunar surface mission of 10 days duration. */
        attribute missionDurationActual : TimeValue;
        attribute missionDurationRequired : TimeValue;
        require constraint { missionDurationActual >= missionDurationRequired }
    }

    verification def MissionDurationTest {
        private import VerificationCases::*;
        objective missionDurationVerificationObjective {
            verify M_LSP1_001;
        }
        return verdict : VerdictKind;
    }

    // ============================================================
    // M-LSP1-002 — ISRU LOX Production
    // ============================================================

    requirement M_LSP1_002 {
        doc /* Lunar Spaceport-1 architecture shall support in-situ resource utilization capable of generating 1000 kg of LOX. */
        attribute loxProducedActual : MassValue;
        attribute loxProducedRequired : MassValue;
        require constraint { loxProducedActual >= loxProducedRequired }
    }

    verification def ISRUProductionTest {
        private import VerificationCases::*;
        objective loxProductionVerificationObjective {
            verify M_LSP1_002;
        }
        return verdict : VerdictKind;
    }

    // ============================================================
    // M-LSP1-003 — LOX Delivery to Depot
    // ============================================================

    requirement M_LSP1_003 {
        doc /* Lunar Spaceport-1 architecture shall provide 1000 kg of LOX to the propellant depot. */
        attribute loxDeliveredActual : MassValue;
        attribute loxDeliveredRequired : MassValue;
        require constraint { loxDeliveredActual >= loxDeliveredRequired }
    }

    verification def LOXDeliveryTest {
        private import VerificationCases::*;
        objective loxDeliveryVerificationObjective {
            verify M_LSP1_003;
        }
        return verdict : VerdictKind;
    }

    // ============================================================
    // M-LSP1-004 — Landing Site Capability
    // ============================================================

    requirement M_LSP1_004 {
        doc /* Lunar Spaceport-1 architecture shall support a landing at <89.796°S, 54.9375°E>. */
        attribute landingLatitudeActual : Real;
        attribute landingLongitudeActual : Real;
        attribute landingLatitudeRequired : Real;
        attribute landingLongitudeRequired : Real;
        require constraint {
            landingLatitudeActual == landingLatitudeRequired and
            landingLongitudeActual == landingLongitudeRequired
        }
    }
}
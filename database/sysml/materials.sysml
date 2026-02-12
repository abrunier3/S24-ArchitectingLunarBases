package 'Materials' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    // -------------------------------------------------------------------------
    // Material definition (source of truth for physical properties)
    // -------------------------------------------------------------------------
    part def Material {
        attribute materialId : String;

        // Physical properties (SI units expected)
        attribute density_kg_m3;
        attribute youngModulus_Pa;
        attribute poissonRatio;
        attribute yieldStrength_Pa;
        attribute ultimateStrength_Pa;
        attribute thermalConductivity_W_mK;
        attribute specificHeat_J_kgK;
        attribute cte_1_K;

        // Traceability
        attribute standard : String;
        attribute source : String;
    }

    // -------------------------------------------------------------------------
    // Aluminum alloy 2219-T87
    // -------------------------------------------------------------------------
    part Aluminum_2219_T87 : Material {
        attribute materialId = "Aluminum_2219_T87";

        attribute density_kg_m3 = 2840;
        attribute youngModulus_Pa = 7.3e10;
        attribute poissonRatio = 0.33;
        attribute yieldStrength_Pa = 3.5e8;
        attribute ultimateStrength_Pa = 4.5e8;

        attribute thermalConductivity_W_mK = 120;
        attribute specificHeat_J_kgK = 900;
        attribute cte_1_K = 2.3e-5;

        attribute standard = "AA 2219-T87";
        attribute source = "TBD";
    }

    // -------------------------------------------------------------------------
    // Titanium alloy Ti-6Al-4V
    // -------------------------------------------------------------------------
    part Titanium_Ti6Al4V : Material {
        attribute materialId = "Titanium_Ti6Al4V";

        attribute density_kg_m3 = 4430;
        attribute youngModulus_Pa = 1.14e11;
        attribute poissonRatio = 0.34;
        attribute yieldStrength_Pa = 8.8e8;
        attribute ultimateStrength_Pa = 9.5e8;

        attribute thermalConductivity_W_mK = 6.7;
        attribute specificHeat_J_kgK = 560;
        attribute cte_1_K = 8.6e-6;

        attribute standard = "Ti-6Al-4V";
        attribute source = "TBD";
    }
}

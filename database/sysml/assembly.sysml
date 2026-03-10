package 'HabitationModule' {

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

        attribute HabitationModule_volume = (HabitationModule_dims.length * HabitationModule_dims.width * HabitationModule_dims.height) * HabitationModule_dims.metersPerUnit^3 * 1000;
        attribute geometry = "assets/geom/HabModule_geom.usda";
        attribute materialRef = "Titanium_Ti6Al4V";
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

        attribute ISRU_PLANT_volume = (ISRU_PLANT_dims.length * ISRU_PLANT_dims.width * ISRU_PLANT_dims.height) * ISRU_PLANT_dims.metersPerUnit^3 * 1000;
        attribute geometry = "assets/geom/ISRU_PLANT_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
    }

    part landing_site {
        part landing_site_dims {
            attribute length = 2;
            attribute width = 0;
            attribute height = 2;
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

        attribute landing_site_volume = (landing_site_dims.length * landing_site_dims.width * landing_site_dims.height) * landing_site_dims.metersPerUnit^3 * 1000;
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

        attribute Propellant_Depot_volume = (Propellant_Depot_dims.length * Propellant_Depot_dims.width * Propellant_Depot_dims.height) * Propellant_Depot_dims.metersPerUnit^3 * 1000;
        attribute geometry = "assets/geom/Propellant_Depot_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
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

        attribute Rover_volume = (Rover_dims.length * Rover_dims.width * Rover_dims.height) * Rover_dims.metersPerUnit^3 * 1000;
        attribute geometry = "assets/geom/Rover_geom.usda";
        attribute materialRef = "Aluminum_2219_T87";
    }

}

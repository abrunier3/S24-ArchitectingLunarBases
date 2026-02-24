package 'HabitationModule' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    part HabitationModule {
        part HabitationModule_dims {
            attribute length = 15;
            attribute width = 10;
            attribute height = 5;
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

        attribute HabitationModule_volume = (HabitationModule_dims.length * HabitationModule_dims.width * HabitationModule_dims.height) * HabitationModule_dims.metersPerUnit^3 * 1000;
        attribute geometry = "assets/geom/HabModule_geom.usda";
        attribute materialRef = "Titanium_Ti6Al4V";

        part O2Tank1 {
            part O2Tank1_dims {
                attribute length = 1.5;
                attribute width = 1.2;
                attribute height = 1.3;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute angleUnit = "deg";
                attribute pressureUnit = "kPa";
                attribute massUnit = "kg";
                attribute lengthUnit = "m";
                attribute X = 5;
                attribute Y = 2;
                attribute Z = 7;
                attribute rX_deg = 0;
                attribute rY_deg = 0;
                attribute rZ_deg = 0;
            }

            attribute O2Tank1_volume = (O2Tank1_dims.length * O2Tank1_dims.width * O2Tank1_dims.height) * O2Tank1_dims.metersPerUnit^3 * 1000;
            attribute O2Tank1_usableO2Capacity = O2Tank1_volume * 0.85;
            attribute O2Tank1_dryMass = 400;
            attribute O2Tank1_operatingPressure = 250;
            attribute O2Tank1_maxPressure = 400;
            attribute O2Tank1_wallThickness = 0.01;
            attribute geometry = "assets/geom/O2Tank_geom.usda";
            attribute materialRef = "Aluminum_2219_T87";
        }
        part O2Tank2 {
            part O2Tank2_dims {
                attribute length = 1.5;
                attribute width = 1.2;
                attribute height = 1.3;
                attribute metersPerUnit = 1;
                attribute upAxis = "Z";
                attribute angleUnit = "deg";
                attribute pressureUnit = "kPa";
                attribute massUnit = "kg";
                attribute lengthUnit = "m";
                attribute X = -3;
                attribute Y = -3;
                attribute Z = -6;
                attribute rX_deg = 0;
                attribute rY_deg = 0;
                attribute rZ_deg = 0;
            }

            attribute O2Tank2_volume = (O2Tank2_dims.length * O2Tank2_dims.width * O2Tank2_dims.height) * O2Tank2_dims.metersPerUnit^3 * 1000;
            attribute O2Tank2_usableO2Capacity = O2Tank2_volume * 0.85;
            attribute O2Tank2_dryMass = 400;
            attribute O2Tank2_operatingPressure = 250;
            attribute O2Tank2_maxPressure = 400;
            attribute O2Tank2_wallThickness = 0.01;
            attribute geometry = "assets/geom/O2Tank_geom.usda";
            attribute materialRef = "Aluminum_2219_T87";
        }
        part rover {
            part rover_dims {
                attribute length = 30;
                attribute width = 0;
                attribute height = 0;
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

            attribute rover_volume = (rover_dims.length * rover_dims.width * rover_dims.height) * rover_dims.metersPerUnit^3 * 1000;
            attribute geometry = "assets/geom/rover_geom.usda";
            attribute materialRef = "Aluminum_2219_T87";
        }
    }

}

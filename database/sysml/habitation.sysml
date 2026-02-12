    package 'Habitation Module' {

        // -------------------------------------------------------------------------
        // Basic items
        // -------------------------------------------------------------------------
        private import SysML::*;
        private import SI::*;
        private import ISQBase::*;
        private import ScalarValues::*;

        part HabitationModule {
            part HabitationModule_dims {
                attribute length = 15; // meters
                attribute width = 10; // meters
                attribute height = 5; // meters

                attribute metersPerUnit = 1;
                attribute upAxis = "Z";

                attribute X = 0; // meters
                attribute Y = 0; // meters
                attribute Z = 0; // meters
            }

            attribute HabitationModule_volume = (HabitationModule_dims.length * HabitationModule_dims.width * HabitationModule_dims.height) * HabitationModule_dims.metersPerUnit^3 * 1000; // liters

            attribute geometry = "assets/geom/HabModule_geom.usda";
            attribute materialRef = "Titanium_Ti6Al4V"; // Titanium

            part O2Tank1 {
                part O2Tank1_dims {
                    attribute length = 1.5; // meters
                    attribute width = 1.2; // meters
                    attribute height = 1.3; // meters

                    attribute metersPerUnit = 1;
                    attribute upAxis = "Z";

                    attribute X = 5; // meters
                    attribute Y = 2; // meters
                    attribute Z = 7; // meters
                }

                attribute O2Tank1_volume = (O2Tank1_dims.length * O2Tank1_dims.width * O2Tank1_dims.height) * O2Tank1_dims.metersPerUnit^3 * 1000; // liters
                attribute O2Tank1_usableO2Capacity = O2Tank1_volume * 0.85; // liters
                attribute O2Tank1_dryMass = 400; // kg
                attribute O2Tank1_operatingPressure = 250; // kPa
                attribute O2Tank1_maxPressure = 400; // kPa
                attribute O2Tank1_wallThickness = 0.01; // meters

                attribute geometry = "assets/geom/O2Tank_geom.usda";
                attribute materialRef = "Aluminum_2219_T87"; // Aluminum alloy 2219-T87
            }

            part O2Tank2 {
                part O2Tank2_dims {
                    attribute length = 1.5; // meters
                    attribute width = 1.2; // meters
                    attribute height = 1.3; // meters

                    attribute metersPerUnit = 1;
                    attribute upAxis = "Z";

                    attribute X = -3; // meters
                    attribute Y = -3; // meters
                    attribute Z = -6; // meters
                }

                attribute O2Tank2_volume = (O2Tank2_dims.length * O2Tank2_dims.width * O2Tank2_dims.height) * O2Tank2_dims.metersPerUnit^3 * 1000; // liters
                attribute O2Tank2_usableO2Capacity = O2Tank2_volume * 0.85; // liters
                attribute O2Tank2_dryMass = 400; // kg
                attribute O2Tank2_operatingPressure = 250; // kPa
                attribute O2Tank2_maxPressure = 400; // kPa
                attribute O2Tank2_wallThickness = 0.01; // meters

                attribute geometry = "assets/geom/O2Tank_geom.usda";
                attribute materialRef = "Aluminum_2219_T87"; // Aluminum alloy 2219-T87
            }
        }
    }
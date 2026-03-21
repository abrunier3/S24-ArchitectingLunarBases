package 'LunarSpaceport-1' {

    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    part HabitationModule {
        part dimensions {
            attribute length = 6;
            attribute width = 3;
            attribute height = 2.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute x = 30;
            attribute y = 0;
            attribute z = 0;
            attribute rx_deg = 0;
            attribute ry_deg = 0;
            attribute rz_deg = 0;
        }

        attribute volume = (dimensions.length * dimensions.width * dimensions.height) * dimensions.metersPerUnit^3 * 1000;
        attribute materialRef = "Titanium_Ti6Al4V";
    }

    part ISRUPlant {
        part dimensions {
            attribute length = 5;
            attribute width = 4;
            attribute height = 2;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute x = 10;
            attribute y = 0;
            attribute z = 0;
            attribute rx_deg = 0;
            attribute ry_deg = 0;
            attribute rz_deg = 0;
        }

        attribute volume = (dimensions.length * dimensions.width * dimensions.height) * dimensions.metersPerUnit^3 * 1000;
        attribute materialRef = "Aluminum_2219_T87";
    }

    part LandingSite {
        part dimensions {
            attribute length = 1;
            attribute width = 1;
            attribute height = 0.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute x = 0;
            attribute y = 0;
            attribute z = 0;
            attribute rx_deg = 0;
            attribute ry_deg = 0;
            attribute rz_deg = 0;
        }

        attribute volume = (dimensions.length * dimensions.width * dimensions.height) * dimensions.metersPerUnit^3 * 1000;
        attribute materialRef = "Aluminum_2219_T87";
    }

    part PropellantDepot {
        part dimensions {
            attribute length = 4;
            attribute width = 4;
            attribute height = 2.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute x = 0;
            attribute y = 5;
            attribute z = 0;
            attribute rx_deg = 0;
            attribute ry_deg = 0;
            attribute rz_deg = 0;
        }

        attribute volume = (dimensions.length * dimensions.width * dimensions.height) * dimensions.metersPerUnit^3 * 1000;
        attribute materialRef = "Aluminum_2219_T87";
    }

    part Rover {
        part dimensions {
            attribute length = 4;
            attribute width = 2;
            attribute height = 1.5;
            attribute metersPerUnit = 1;
            attribute upAxis = "Z";
            attribute angleUnit = "deg";
            attribute pressureUnit = "kPa";
            attribute massUnit = "kg";
            attribute lengthUnit = "m";
            attribute x = 9;
            attribute y = 0;
            attribute z = 0;
            attribute rx_deg = 0;
            attribute ry_deg = 0;
            attribute rz_deg = 0;
        }

        attribute volume = (dimensions.length * dimensions.width * dimensions.height) * dimensions.metersPerUnit^3 * 1000;
        attribute materialRef = "Aluminum_2219_T87";
    }

}
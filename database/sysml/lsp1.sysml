package 'Lunar Spaceport-1' {

    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    part LunarSpaceport1 {
        part LunarSpaceport1_dims {
            attribute length = 1000; // meters
            attribute width  = 3000; // meters
            attribute height = 300;  // meters

            attribute metersPerUnit = 1;
            attribute upAxis = "Z";

            attribute X = 0; // meters
            attribute Y = 0; // meters
            attribute Z = 0; // meters
        }

        attribute coordinates = "<89.796°S, 54.9375°E>";
    }
}
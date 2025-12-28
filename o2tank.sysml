package 'Oxygen Tank for Habitation' {

    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

part def O2Tank {

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 0.2;  // meters
            attribute height : Real = 0.1;
            attribute depth : Real = 0.5;

            attribute meshAddr : String = "0x47f62756";  // unique identifier for mesh
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/landpadcomplex.usd";   // path to .usd or .usdz file
            attribute color : String = "#ffffff84";      // hex or named color
            attribute material : String = "";   // optional material name
        }
    }
}
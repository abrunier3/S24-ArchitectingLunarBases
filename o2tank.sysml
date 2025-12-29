package 'Oxygen Tank for Habitation' {

    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    part def Mesh {
        attribute points : String;
        attribute faceVertexCounts : String;
        attribute faceVertexIndices : String;
    }

        // -------------------------------------------------------------------------
        // Oxygen Tank
        // -------------------------------------------------------------------------

    part O2Tank {
        part mesh : Mesh {
            points = "[(-1, -1, -1),( 1, -1, -1),( 1,  1, -1),(-1,  1, -1),(-1, -1,  1),( 1, -1,  1),( 1,  1,  1),(-1,  1,  1)]";

            faceVertexCounts = "[4,4,4,4,4,4]";

            faceVertexIndices = "[0,1,2,3,4,5,6,7,0,1,5,4,3,2,6,7,0,3,7,4,1,2,6,5]";
        }
    }
}
package 'Lunar Spaceport-1 Architecture' {

    // -------------------------------------------------------------------------
    // Basic items
    // -------------------------------------------------------------------------
    private import SysML::*;
    private import SI::*;
    private import ISQBase::*;
    private import ScalarValues::*;

    // Resources and physical stuff
    item def CrewMember;
    item def Passenger;
    item def Cargo;
    item def Oxygen;
    item def Water;
    item def Power;
    item def Heat;
    item def Waste;
    item def CO2;
    item def Regolith;
    item def Propellant;
    item def DataLink;

    item def LandingRequest;
    item def LandingComplete;
    item def EVAStart;
    item def EVAEnd;
    item def FaultDetected;

    // -------------------------------------------------------------------------
    // Port definitions for common interfaces
    // -------------------------------------------------------------------------

    // Life support interfaces
    port def AtmosphereInPort {
        in item o2 : Oxygen;
        in item co2 : CO2;
        in item makeUpWater : Water;
    }

    port def AtmosphereOutPort {
        out item o2 : Oxygen;
        out item co2 : CO2;
        out item wasteAir : Waste;
    }

    port def WaterInPort {
        in item rawWater : Water;
    }

    port def WaterOutPort {
        out item potableWater : Water;
        out item wasteWater : Waste;
    }

    // Power interfaces
    port def PowerOutPort {
        out item power : Power;
    }

    port def PowerInPort {
        in item power : Power;
    }

    // Thermal interfaces
    port def HeatRejectionPort {
        out item rejectHeat : Heat;
    }

    port def HeatLoadPort {
        in item heatLoad : Heat;
    }

    // Propellant interfaces (for landing pad / ISRU / prop depots)
    port def PropellantOutPort {
        out item propellant : Propellant;
    }

    port def PropellantInPort {
        in item propellant : Propellant;
    }

    // Regolith interfaces (ISRU feedstock)
    port def RegolithInPort {
        in item regolith : Regolith;
    }

    // Communications interfaces
    port def CommsOutPort {
        out item link : DataLink;
    }

    port def CommsInPort {
        in item link : DataLink;
    }

    ////////////////////////////////////////////////////////////////////////
    // Operational actions
    ////////////////////////////////////////////////////////////////////////

    // 2.1 Vehicle Turnaround at Landing Pad

    action def VehicleTurnaround {
        in item inboundPropellant : Propellant;
        in item inboundCargo : Cargo;
        out item outboundPropellant : Propellant;
        out item outboundCargo : Cargo;

        // Simple structure: unload → service → reload

        action unloadVehicle {
            in item inCargo : Cargo;
            out item toLogistics : Cargo;
        }

        action serviceVehicle {
            in item inPropellant : Propellant;
            out item servicedPropellant : Propellant;
        }

        action loadVehicle {
            in item loadCargo : Cargo;
            out item outCargo : Cargo;
        }

        // Flow and succession
        first unloadVehicle then serviceVehicle;
        first serviceVehicle then loadVehicle;

        flow unloadVehicle.toLogistics to serviceVehicle.inPropellant;
        flow serviceVehicle.servicedPropellant to loadVehicle.loadCargo;

        bind outboundPropellant = serviceVehicle.servicedPropellant;
        bind outboundCargo = loadVehicle.outCargo;
    }

    // 2.2 ISRU Production Cycle

    action def ISRUCycle {
        in item regolithFeed : Regolith;
        out item producedO2 : Oxygen;
        out item producedWater : Water;
        out item producedPropellant : Propellant;

        action excavate {
            in item inRegolith : Regolith;
            out item excavatedRegolith : Regolith;
        }

        action processRegolith {
            in item feedRegolith : Regolith;
            out item o2 : Oxygen;
            out item water : Water;
            out item propellant : Propellant;
        }

        // Simple sequence: excavate then process
        first excavate then processRegolith;

        flow excavate.excavatedRegolith to processRegolith.feedRegolith;

        bind producedO2 = processRegolith.o2;
        bind producedWater = processRegolith.water;
        bind producedPropellant = processRegolith.propellant;
    }

    // 2.3 Crew & Passenger Rotation

    action def CrewRotation {
        in item arrivingCrew : CrewMember[*];
        in item arrivingPassengers : Passenger[*];
        out item departingCrew : CrewMember[*];
        out item departingPassengers : Passenger[*];

        action disembark {
            in item inCrew : CrewMember[*];
            in item inPax : Passenger[*];
            out item toHabCrew : CrewMember[*];
            out item toHabPax : Passenger[*];
        }

        action embark {
            in item fromHabCrew : CrewMember[*];
            in item fromHabPax : Passenger[*];
            out item outCrew : CrewMember[*];
            out item outPax : Passenger[*];
        }

        first disembark then embark;

        flow disembark.toHabCrew to embark.fromHabCrew;
        flow disembark.toHabPax to embark.fromHabPax;

        bind departingCrew = embark.outCrew;
        bind departingPassengers = embark.outPax;
    }

    state def SpaceportOpsStates {

        entry; then NominalOps;

        state NominalOps;
        state LandingOps;
        state EVAOps;
        state SafeMode;

        // Example transitions (triggers are conceptual items/events)

        // Nominal → LandingOps on LandingRequest
        transition nominal_to_landing
            first NominalOps
            accept LandingRequest
            then LandingOps;

        // LandingOps → Nominal after LandingComplete
        transition landing_to_nominal
            first LandingOps
            accept LandingComplete
            then NominalOps;

        // Nominal → EVAOps on EVAStart
        transition nominal_to_eva
            first NominalOps
            accept EVAStart
            then EVAOps;

        // EVAOps → Nominal on EVAEnd
        transition eva_to_nominal
            first EVAOps
            accept EVAEnd
            then NominalOps;

        // Any state → SafeMode on FaultDetected
        transition any_to_safe
            first NominalOps
            accept FaultDetected
            then SafeMode;

        // You could add similar transitions from other states as needed
    }


    // -------------------------------------------------------------------------
    // Major subsystem part definitions
    // -------------------------------------------------------------------------

    // Habitation for commercial crew/passengers
    part def HabitationModule {
        attribute internalVolume : Real;             // m^3
        attribute maxCrew : Integer;
        attribute maxPassengers : Integer;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/hab.usd";   // path to .usd or .usdz file
            attribute color : String = "#6ec21fff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part crewQuarters;
        part passengerQuarters;
        part galley;
        part hygiene;

        port atmIn : AtmosphereInPort;
        port atmOut : AtmosphereOutPort;
        port waterIn : WaterInPort;
        port waterOut : WaterOutPort;
        port powerIn : PowerInPort;
        port heatLoad : HeatLoadPort;
        port commsIn : CommsInPort;
        port commsOut : CommsOutPort;

        perform action crewRotations : CrewRotation [*] ordered;
    }

    // Power generation and storage
    part def PowerPlant {
        attribute maxPowerOutput : Real;         // kW
        attribute availability : Real;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/powerplant.usd";   // path to .usd or .usdz file
            attribute color : String = "#e3da21ff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part generation;     // solar, nuclear, etc.
        part storage;        // batteries, fuel cells

        port powerOut : PowerOutPort;
        port heatRejection : HeatRejectionPort;
    }

    // Power distribution to loads and visiting vehicles
    part def PowerDistribution {
        attribute conversionLoss : Real;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/powerdist.usd";   // path to .usd or .usdz file
            attribute color : String = "#ffff00ff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        port powerIn : PowerInPort;
        port powerToHab : PowerOutPort;
        port powerToECLSS : PowerOutPort;
        port powerToISRU : PowerOutPort;
        port powerToThermal : PowerOutPort;
        port powerToComms : PowerOutPort;
        port powerToLandingPad : PowerOutPort;
    }

    // ECLSS for life support
    part def ECLSS {
        attribute o2ProductionReal : Real;           // kg/day
        attribute co2RemovalReal : Real;            // kg/day
        attribute waterRecoveryEfficiency : Real;      // %

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/eclss.usd";   // path to .usd or .usdz file
            attribute color : String = "#4ff66eff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part atmosphereLoop;
        part waterLoop;
        part wasteManagement;

        port atmSupply : AtmosphereOutPort;
        port atmReturn : AtmosphereInPort;
        port waterSupplyOut : WaterOutPort;
        port waterReturnIn : WaterInPort;
        port powerIn : PowerInPort;
        port heatRejection : HeatRejectionPort;
    }

    // Thermal control for rejecting heat to space
    part def ThermalControl {
        attribute coolingReal : Real;        // kW

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/thermalcontrol.usd";   // path to .usd or .usdz file
            attribute color : String = "#ff2a2aff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part radiators;
        part internalFluidLoops;

        port heatFromHab : HeatRejectionPort;
        port heatFromECLSS : HeatRejectionPort;
        port heatFromPower : HeatRejectionPort;
        port heatFromISRU : HeatRejectionPort;
    }

    // Landing pad / landing operations
    part def LandingPadComplex {
        attribute padReal : Real;
        attribute maxLandingMass : Real;         // metric tons
        attribute numberOfPads : Integer;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/landpadcomplex.usd";   // path to .usd or .usdz file
            attribute color : String = "#ffffff84";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part landingPads[numberOfPads];

        port powerIn : PowerInPort;
        port commsIn : CommsInPort;
        port commsOut : CommsOutPort;
        port propellantIn : PropellantInPort;        // from prop depot / ISRU
    
        perform action turnaround : VehicleTurnaround [*] ordered;
    }

    // ISRU plant (regolith to consumables/propellant)
    part def ISRUPlant {
        attribute regolithThroughput : Real;         // tons/day
        attribute o2ProductionReal : Real;
        attribute propellantProductionReal : Real;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/isru.usd";   // path to .usd or .usdz file
            attribute color : String = "#269bfbff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part excavation;
        part processing;
        part storage;

        port regolithIn : RegolithInPort;
        port powerIn : PowerInPort;
        port heatRejection : HeatRejectionPort;

        port o2Out : AtmosphereInPort;          // to ECLSS or storage
        port waterOut : WaterOutPort;           // to ECLSS / hab
        port propellantOut : PropellantOutPort; // to depot / landing pad

        perform action isruOps : ISRUCycle [*] ordered;
    }

    // Propellant storage / depot
    part def PropellantDepot {
        attribute storageReal : Real;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/propdepot.usd";   // path to .usd or .usdz file
            attribute color : String = "#4d86ffff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part tanks;
        part transferManifold;

        port propellantIn : PropellantInPort;
        port propellantOutToPad : PropellantOutPort;
        port powerIn : PowerInPort;
        port heatRejection : HeatRejectionPort;
    }

    // Communications and navigation
    part def CommsSystem {
        attribute downlinkReal : Real;
        attribute uplinkReal : Real;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/comms.usd";   // path to .usd or .usdz file
            attribute color : String = "#ffa928ff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        port baseCommsIn : CommsInPort;
        port baseCommsOut : CommsOutPort;
    }

    // Surface logistics and cargo handling
    part def SurfaceLogistics {
        attribute cargoThroughput : Real;
        attribute storageReal : Real;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/logistics.usd";   // path to .usd or .usdz file
            attribute color : String = "#ffffff31";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        part cargoYard;
        part loaders;
        part surfaceVehicles;
    }

    // -------------------------------------------------------------------------
    // Top-level spaceport definition
    // -------------------------------------------------------------------------

    part def LunarSpaceport1 {
        attribute portName : String;

        attribute spatial {
            attribute x : Real = 0.0;      // meters, local frame
            attribute y : Real = 0.0;
            attribute z : Real = 0.0;

            attribute qx : Real = 0.0;     // quaternion orientation
            attribute qy : Real = 0.0;
            attribute qz : Real = 0.0;
            attribute qw : Real = 1.0;

            attribute scaleX : Real = 1.0;
            attribute scaleY : Real = 1.0;
            attribute scaleZ : Real = 1.0;

            attribute width : Real = 120.0;  // meters
            attribute height : Real = 20.0;
            attribute depth : Real = 80.0;
        }

        attribute visual {
            attribute usdAsset : String = "assets/spaceport/spaceport.usd";   // path to .usd or .usdz file
            attribute color : String = "#ff4ae7ff";      // hex or named color
            attribute material : String = "";   // optional material name
        }

        attribute ossf {
            attribute body : String = "Moon";              // "Moon"
            attribute referenceFrame : String = "IAU_MOON";    // "IAU_MOON"
            attribute latitude : Real = -89.5;            // degrees
            attribute longitude : Real = 45.0;           // degrees
            attribute elevation : Real = 0.0;           // meters
            attribute terrainTile : String = "LRO_NAC_SouthPole_001";       // OSSF tile ID
            attribute illuminationModel : String = "SouthPoleLowSun"; // "SouthPoleLowSun"
        }

        state opsStates : SpaceportOpsStates;

        // Major subsystems
        part hab : HabitationModule;
        part eclss : ECLSS;
        part powerPlant : PowerPlant;
        part powerDist : PowerDistribution;
        part thermal : ThermalControl;
        part landingPadComplex : LandingPadComplex;
        part isru : ISRUPlant;
        part propDepot : PropellantDepot;
        part comms : CommsSystem;
        part logistics : SurfaceLogistics;
    }

    // -------------------------------------------------------------------------
    // One concrete instance: "Lunar Spaceport-1"
    // -------------------------------------------------------------------------

    part 'Lunar Spaceport-1' : LunarSpaceport1 {

        attribute redefines portName = "Lunar Spaceport-1";

        // Rough sizing (placeholder values)
        part hab : HabitationModule {
            attribute redefines internalVolume = 500.0;
            attribute redefines maxCrew = 12;
            attribute redefines maxPassengers = 24;
        }

        part eclss : ECLSS {
            attribute redefines o2ProductionReal = 6.0;
            attribute redefines co2RemovalReal = 6.0;
            attribute redefines waterRecoveryEfficiency = 90.0;
        }

        part powerPlant : PowerPlant {
            attribute redefines maxPowerOutput = 200.0;
            attribute redefines availability = 0.99;
        }

        part powerDist : PowerDistribution {
            attribute redefines conversionLoss = 5.0;
        }

        part thermal : ThermalControl {
            attribute redefines coolingReal = 80.0;
        }

        part landingPadComplex : LandingPadComplex {
            attribute redefines padReal = 10000.0;
            attribute redefines maxLandingMass = 150.0;
            attribute redefines numberOfPads = 4;
        }

        part isru : ISRUPlant {
            attribute redefines regolithThroughput = 20.0;
            attribute redefines o2ProductionReal = 5.0;
            attribute redefines propellantProductionReal = 3.0;
        }

        part propDepot : PropellantDepot {
            attribute redefines storageReal = 500.0;
        }

        part logistics : SurfaceLogistics {
            attribute redefines cargoThroughput = 50.0;
            attribute redefines storageReal = 200.0;
        }

        part comms : CommsSystem {
            attribute redefines downlinkReal = 100.0;
            attribute redefines uplinkReal = 50.0;
        }

        // ---------------------------------------------------------------------
        // Internal wiring: power
        // ---------------------------------------------------------------------

        // PowerPlant → PowerDistribution
        connect powerPlant.powerOut.power to powerDist.powerIn.power;

        // Distribution to loads
        connect powerDist.powerToHab.power to hab.powerIn.power;
        connect powerDist.powerToECLSS.power to eclss.powerIn.power;
        connect powerDist.powerToISRU.power to isru.powerIn.power;
        connect powerDist.powerToThermal.power to thermal.heatFromPower.rejectHeat;
        connect powerDist.powerToComms.power to comms.baseCommsIn.link;      // or define a PowerInPort on Comms
        connect powerDist.powerToLandingPad.power to landingPadComplex.powerIn.power;

        // ---------------------------------------------------------------------
        // Life support loops: hab ↔ ECLSS ↔ (optionally ISRU)
        // ---------------------------------------------------------------------

        // ECLSS supplies hab atmosphere and water
        connect eclss.atmSupply.o2 to hab.atmIn.o2;
        connect eclss.atmReturn.makeUpWater to hab.atmIn.makeUpWater;

        // Hab returns used atmosphere to ECLSS
        connect hab.atmOut.co2 to eclss.atmSupply.co2;
        connect hab.atmOut.wasteAir to eclss.atmSupply.wasteAir;

        // Water loop between ECLSS and hab
        connect eclss.waterSupplyOut.potableWater to hab.waterIn.rawWater;
        connect hab.waterOut.wasteWater to eclss.waterReturnIn.rawWater;

        // ISRU can provide additional O2 / water into the life support chain
        connect isru.o2Out.o2 to eclss.atmSupply.o2;
        connect isru.waterOut.potableWater to eclss.waterReturnIn.rawWater;

        // ---------------------------------------------------------------------
        // Thermal paths
        // ---------------------------------------------------------------------

        connect hab.heatLoad.heatLoad to thermal.heatFromHab.rejectHeat;
        connect eclss.heatRejection.rejectHeat to thermal.heatFromECLSS.rejectHeat;
        connect powerPlant.heatRejection.rejectHeat to thermal.heatFromPower.rejectHeat;
        connect isru.heatRejection.rejectHeat to thermal.heatFromISRU.rejectHeat;

        // ---------------------------------------------------------------------
        // Propellant chain: ISRU → PropellantDepot → LandingPad → external
        // ---------------------------------------------------------------------

        // ISRU to depot
        connect isru.propellantOut.propellant to propDepot.propellantIn.propellant;

        // Depot to landing pad complex (for vehicle refueling)
        connect propDepot.propellantOutToPad.propellant to landingPadComplex.propellantIn.propellant;

        // ---------------------------------------------------------------------
        // Communications
        // ---------------------------------------------------------------------

        // Hab ↔ Comms
        connect hab.commsOut.link to comms.baseCommsIn.link;
        connect comms.baseCommsOut.link to hab.commsIn.link;

        // Landing pad ops comms via base comms
        connect landingPadComplex.commsOut.link to comms.baseCommsIn.link;
        connect comms.baseCommsOut.link to landingPadComplex.commsIn.link;

        // PowerPlant → PowerDistribution
        flow from powerPlant.powerOut.power
             to powerDist.powerIn.power;

        // Distribution to loads
        flow from powerDist.powerToHab.power
             to hab.powerIn.power;

        flow from powerDist.powerToECLSS.power
             to eclss.powerIn.power;

        flow from powerDist.powerToISRU.power
             to isru.powerIn.power;

        // Atmosphere loop: ECLSS ↔ Hab
        flow from eclss.atmSupply.o2
             to hab.atmIn.o2;

        flow from hab.atmOut.co2
             to eclss.atmReturn.co2;

        // Water loop: ECLSS ↔ Hab
        flow from eclss.waterSupplyOut.potableWater
             to hab.waterIn.rawWater;

        flow from hab.waterOut.wasteWater
             to eclss.waterReturnIn.rawWater;

        // ISRU to depot and pad
        flow from isru.propellantOut.propellant
             to propDepot.propellantIn.propellant;

        flow from propDepot.propellantOutToPad.propellant
             to landingPadComplex.propellantIn.propellant;

        // Comms flows
        flow from hab.commsOut.link
             to comms.baseCommsIn.link;

        flow from landingPadComplex.commsOut.link
             to comms.baseCommsIn.link;

        exhibit opsStates;
    }
}
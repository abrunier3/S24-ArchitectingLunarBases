// Rebuild the physical network from the surviving placements, preserving edited edges.
const fs = require('node:fs');
const vm = require('node:vm');
const [archivePath, systemPath, outputPath] = process.argv.slice(2);
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const page = fs.readFileSync('ScenarioIndex.html', 'utf8');
const cfg = JSON.parse(read(archivePath).inputs.scenario_config);
const logic = cfg.scenario_builder;
const old = read(systemPath).urban_planning;
const grid = JSON.parse(page.match(/^let up42SlopeGrids = (\{.*\});/m)[1]).MMA;
const frame = old.map_frame_m.frame_px;
const width = 2 * frame.x + frame.size, height = frame.size;
const instances = logic.instances.filter(i => i.type !== 'HabitationModule');
const placements = Object.fromEntries(instances.map(i => [i.id, i.position_canvas]));
const assignments = logic.resource_routes.map(r => ({...r, stops: r.stops.filter(s => s !== 'HabitationModule')}));
const ui = vm.createContext({
  up42W: width, up42H: height, KM_PER_PX: old.map_frame_m.meters_per_pixel / 1000,
  UP42_MAX_ROUTE_SLOPE: 15, up42SyntheticTerrain: grid.data, up42Routes: [],
  up42Placements: placements, up42Orientations: Object.fromEntries(instances.map(i => [i.id, i.orientation_deg])),
  up42Scenario: {resourceRoutes: assignments}, currentScenarioMode: 'isru',
  getScenarioInstances: () => instances, syncScenarioInterfacesFromSysML() {},
  syncModuleClassesWithCurrentGraph() {}, isPowerIgnored: () => false,
  upSelectedSite: {id: old.site, name: old.site_name, lat: old.site_lat, lon: old.site_lon},
});
for (const name of ('primMST aStar routeSegmentIsTraversable terrainGridToCanvas findNearestTraversableGridCell simplifyPath createPathBetweenModules getDirectedRoutePoints getNetworkRoutePath getRoutePathDistanceKm recomputeScenarioResourceRoutePath refreshScenarioResourceRoutePaths getRouteSlopeStats getRouteSegmentCells terrainSlopeAtGrid canvasPointToTerrainGrid getUp42MapFrame getBaseModuleId buildScenarioLogicPayload buildUrbanPlanningPayload straightLinePath ensureWaypoints inferRouteFlow').split(' ')) {
  const definition = page.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'));
  vm.runInContext(definition[0], ui);
}
const history = [];
const placed = Object.entries(placements);
for (const [i,j] of ui.primMST(placed)) {
  const [from,a] = placed[i], [to,b] = placed[j];
  const edge = old.routes.find(e => (e.from === from && e.to === to) || (e.from === to && e.to === from));
  let pts;
  if (edge) {
    pts = old.route_geometry[edge.key].waypoints_m.map(([x,y]) => ({x:width/2+x/5,y:height/2-y/5}));
    if (edge.from !== from) pts.reverse();
  } else {
    pts = ui.aStar(a,b,grid.rows);
    if (!pts) throw Error('No traversable new edge: ' + from + ' to ' + to);
  }
  ui.up42Routes.push({from,to,pts,flow:ui.inferRouteFlow(from,to)});
  history.push({from,to,provenance:edge ? 'archived edited polyline' : 'new A* on embedded MMA grid'});
}
const urban = ui.buildUrbanPlanningPayload({quiet:true});
fs.writeFileSync(outputPath, JSON.stringify({urban,history,grid_spacing_m:grid.spacing_m},null,2));

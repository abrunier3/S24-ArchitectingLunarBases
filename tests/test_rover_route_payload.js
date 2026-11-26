const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const page = fs.readFileSync(path.join(__dirname, '..', 'ScenarioIndex.html'), 'utf8');

function planningPage() {
  const ui = vm.createContext({
    KM_PER_PX: 0.005, up42W: 100, up42H: 100,
    up42SyntheticTerrain: [[0, 0, 0], [0, 0, 12], [0, 0, 0]],
    upSelectedSite: {id: 'site', lat: -85, lon: 0},
    up42Placements: {Plant: {cx: 0, cy: 0}, Depot: {cx: 100, cy: 0}, Lab: {cx: 100, cy: 100}},
    up42Orientations: {}, currentScenarioMode: 'new',
    up42Routes: [
      {from: 'Depot', to: 'Plant', pts: [{x: 100, y: 0}, {x: 50, y: 0}, {x: 0, y: 0}]},
      {from: 'Depot', to: 'Lab', pts: [{x: 100, y: 0}, {x: 100, y: 100}]},
    ],
    up42Scenario: {resourceRoutes: [
      {id: 'first', from: 'Plant', to: 'Depot', flow: 'Ore', rover_id: 'Rover_1', stops: []},
      {id: 'second', from: 'Plant', to: 'Depot', flow: 'Ore', rover_id: 'Rover_2', stops: ['Lab']},
    ]},
    getScenarioInstances: () => [], syncScenarioInterfacesFromSysML() {},
    syncModuleClassesWithCurrentGraph() {}, isPowerIgnored: () => true,
  });
  for (const name of [
    'createPathBetweenModules', 'getDirectedRoutePoints', 'getNetworkRoutePath',
    'getRoutePathDistanceKm', 'recomputeScenarioResourceRoutePath', 'refreshScenarioResourceRoutePaths',
    'getRouteSlopeStats', 'getRouteSegmentCells', 'terrainSlopeAtGrid', 'canvasPointToTerrainGrid',
    'getUp42MapFrame', 'getBaseModuleId', 'buildScenarioLogicPayload', 'buildUrbanPlanningPayload',
    'straightLinePath', 'ensureWaypoints',
  ]) {
    const definition = page.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'));
    assert.ok(definition, name);
    vm.runInContext(definition[0], ui);
  }
  return ui;
}

test('an edited physical waypoint reaches both DES assignments and their distinct published paths', () => {
  const ui = planningPage();
  const before = ui.buildScenarioLogicPayload().resource_routes;
  assert.equal(before[0].distance_km, 0.5);
  assert.equal(before[1].distance_km, 1.5);
  ui.up42Routes[0].pts[1] = {x: 100, y: 50};
  const routes = ui.buildScenarioLogicPayload().resource_routes;
  const urban = ui.buildUrbanPlanningPayload({quiet: true});
  const [first, second] = routes;
  assert.notEqual(first.route_name, second.route_name);
  assert.equal(first.distance_km, 0.809);
  assert.equal(second.distance_km, 1.809);
  assert.equal(before[0].max_slope_deg, 0);
  assert.equal(first.max_slope_deg, 12);
  assert.deepEqual(urban.scenario_logic.resource_routes, routes);
  for (const route of routes) {
    const published = urban.connections[route.route_name];
    assert.equal(published.rover_id, route.rover_id);
    assert.equal(published.distance_km, route.distance_km);
  }
  const waypoints = name => Array.from(urban.connections[name].waypoints_m, point => Array.from(point));
  const direct = [[-250, 250, 0], [250, 0, 0], [250, 250, 0]];
  assert.deepEqual(waypoints(first.route_name), direct);
  assert.deepEqual(waypoints(second.route_name), [...direct, [250, -250, 0], direct[2]]);
});

test('an unconnected leg uses terrain routing and retains its straight-line fallback', () => {
  const ui = planningPage();
  ui.up42Routes.pop();
  const terrainPath = [{x: 100, y: 0}, {x: 80, y: 40}, {x: 100, y: 100}];
  ui.aStar = () => terrainPath;
  assert.equal(ui.createPathBetweenModules('Depot', 'Lab'), terrainPath);
  ui.aStar = () => null;
  assert.equal(ui.getRoutePathDistanceKm(ui.createPathBetweenModules('Depot', 'Lab')), 0.5);
});

const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const page = fs.readFileSync(path.join(__dirname, '..', 'ScenarioIndex.html'), 'utf8');

test('batch input round-trips through the saved form and prefers live route geometry and equations', () => {
  const input = {value: ''};
  const ui = vm.createContext({
    document: {getElementById: () => input}, currentScenarioName: 'B0',
    currentScenarioSlug: 'B0', currentSysmlFile: 'B0.sysml',
    getNumberInputValue: () => 168,
    buildScenarioLogicPayload: () => ({
      resource_routes: [{id: 'edited-route', distance_km: 4.065}],
      module_equations: {ISRUPlant: 'OxygenOut = 0.121 * RegolithIn'},
    }),
  });
  for (const name of ['isTimedBatchConfigured', 'readBatchScenarioInput', 'buildTimedBatchConfig']) {
    const part = page.match(new RegExp('^  function ' + name + '\\([^]*?^  }', 'm'));
    assert.ok(part, name);
    vm.runInContext(part[0], ui);
  }
  assert.equal(ui.readBatchScenarioInput(), null);
  const saved = {desBatchOperations: JSON.stringify({
    batch_operations: {lines: [{plant_id: 'ISRUPlant_1', batch_kg: 9.3}]},
    auxiliary_routes: [{id: 'residue'}],
  })};
  input.value = saved.desBatchOperations;
  const config = ui.buildTimedBatchConfig(ui.readBatchScenarioInput());
  assert.equal(config.engine.mode, 'isru');
  assert.equal(config.simulation.duration_hr, 168);
  assert.equal(config.batch_operations.lines[0].batch_kg, 9.3);
  assert.equal(config.scenario_builder.resource_routes[0].distance_km, 4.065);
  assert.equal(config.scenario_builder.resource_routes[1].id, 'residue');
  assert.equal(config.scenario_builder.module_equations.ISRUPlant, 'OxygenOut = 0.121 * RegolithIn');
});

test('saved comparison keeps total electric demand and disjoint LOX stocks', () => {
  const ui = vm.createContext({});
  const part = page.match(/^  function getScenarioResourceSeries\([^]*?^  }/m);
  vm.runInContext(part[0], ui);
  const state = {Total_LOX_Produced_kg: 5, Total_LOX_Delivered_kg: 2, Plant_LOX_kg: 1,
    In_Transit_LOX_kg: 2, Total_System_Demand_kWh: 9, Total_Regolith_Received_kg: 6};
  const rows = ui.getScenarioResourceSeries({results: {results: {Engine: 'BatchISRU'},
    log: {1: {Batch_Operations: state, Power_Manager: {total_energy_consumed: 9}}}}});
  assert.equal(rows[0].energy, 9);
  assert.equal(rows[0].lox, 5);
  assert.equal(rows[0].regolith, 6);
});

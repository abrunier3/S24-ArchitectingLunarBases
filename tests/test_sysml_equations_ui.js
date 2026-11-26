// Run with node --test tests/test_sysml_equations_ui.js
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const page = fs.readFileSync(path.join(__dirname, '..', 'ScenarioIndex.html'), 'utf8');
function setup() {
  const scope = vm.createContext({
    currentScenarioMode: 'new',
    up42Scenario: {moduleEquations: {}},
    isPowerGeneratorModule: () => false
  });
  const functions = [
    'importSysmlModuleEquations', 'getModuleEquationList', 'setModuleEquationList',
    'getEquationOutputName', 'getBaseModuleId', 'splitModuleEquations', 'getModuleDemandEquation'
  ];
  for (const name of functions) {
    const definition = page.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'));
    assert.ok(definition, name);
    vm.runInContext(definition[0], scope);
  }
  return scope;
}

test('graph refresh, user edits, explicit deletions and saved overrides', () => {
  const ui = setup();
  const load = law => ui.importSysmlModuleEquations({Plant: {operational_equations: [law]}});
  load('ProductOut = FeedIn');
  ui.setModuleEquationList('Plant', [...ui.getModuleEquationList('Plant'), 'PowerOut = 0']);
  load('ProductOut = FeedIn * 2');
  assert.equal(ui.up42Scenario.moduleEquations.Plant, 'ProductOut = FeedIn * 2');
  ui.setModuleEquationList('Plant_2', ['ProductOut = 7'], true);
  ui.setModuleEquationList('Plant', [], true);
  ui.up42Scenario = JSON.parse(JSON.stringify(ui.up42Scenario));
  load('ProductOut = FeedIn * 3');
  assert.equal(ui.up42Scenario.moduleEquations.Plant, '');
  assert.equal(ui.up42Scenario.moduleEquations.Plant_2, 'ProductOut = 7');
});

test('historical preset, customized legacy scenarios and older graphs', () => {
  const ui = setup();
  const graph = {Plant: {operational_equations: ['ProcessingTime = 1']}};
  ui.currentScenarioMode = 'isru';
  ui.importSysmlModuleEquations(graph);
  assert.equal(ui.up42Scenario.moduleEquations.Plant, undefined);
  ui.currentScenarioMode = 'new';
  ui.up42Scenario.moduleEquations.Plant = 'ProcessingTime = 77';
  ui.importSysmlModuleEquations(graph);
  ui.importSysmlModuleEquations({Plant: {}});
  assert.equal(ui.up42Scenario.moduleEquations.Plant, 'ProcessingTime = 77');
});

test('power demand includes its intermediate assignments only', () => {
  const ui = setup();
  ui.setModuleEquationList('Plant', ['Load = SimulationTime * 2', 'ProductOut = FeedIn', 'PowerIn = Load']);
  assert.equal(ui.getModuleDemandEquation('Plant_2'), 'Load = SimulationTime * 2\nPowerIn = Load');
});

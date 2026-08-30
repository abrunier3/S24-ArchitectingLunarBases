import unittest

from S24.DES_pipeline_version.scenario_equations import (
    ScenarioEquationError,
    evaluate_equations,
    evaluate_selected_equations,
    get_equation_contract,
)


class ScenarioEquationTests(unittest.TestCase):
    def test_neutral_power_boundary_is_allowed_without_runtime_effect(self):
        outputs = evaluate_equations(
            "RegolithOut = RequestedRegolith\nPowerOut = 0",
            {"RequestedRegolith": 4000},
            effect_outputs={"RegolithOut"},
        )
        self.assertEqual(outputs["RegolithOut"], 4000)
        self.assertEqual(outputs["PowerOut"], 0)

    def test_nonzero_unused_power_boundary_is_rejected(self):
        with self.assertRaises(ScenarioEquationError):
            evaluate_equations(
                "RegolithOut = RequestedRegolith\nPowerOut = 1",
                {"RequestedRegolith": 4000},
                effect_outputs={"RegolithOut"},
            )

    def test_selected_outputs_keep_dependencies(self):
        equations = "Intermediate = ResourceIn * efficiency\nResourceOut = Intermediate - loss"
        outputs = evaluate_selected_equations(
            equations,
            {"ResourceIn": 20, "efficiency": 0.5, "loss": 1},
            {"ResourceOut"},
        )
        self.assertEqual(outputs["Intermediate"], 10)
        self.assertEqual(outputs["ResourceOut"], 9)

    def test_contract_reports_external_inputs(self):
        contract = get_equation_contract(
            "Intermediate = ResourceIn * efficiency\nResourceOut = Intermediate"
        )
        self.assertEqual(contract["outputs"], {"Intermediate", "ResourceOut"})
        self.assertEqual(contract["inputs"], {"ResourceIn", "efficiency"})

    def test_duplicate_output_is_rejected(self):
        with self.assertRaises(ScenarioEquationError):
            get_equation_contract("ResourceOut = 1\nResourceOut = 2")


if __name__ == "__main__":
    unittest.main()

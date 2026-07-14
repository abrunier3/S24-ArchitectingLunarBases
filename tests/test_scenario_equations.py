import unittest

from S24.DES_pipeline_version.scenario_equations import (
    ScenarioEquationError,
    evaluate_selected_equations,
    get_equation_contract,
)


class ScenarioEquationTests(unittest.TestCase):
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

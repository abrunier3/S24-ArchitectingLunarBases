import unittest

from S24.DES_pipeline_version.scenario_equations import evaluate_selected_equations
from S24.sysml.main_api import sysml_to_json_transformer


class SysmlOperationalEquationTests(unittest.TestCase):
    def part(self, declarations):
        source = (
            "package Test {\npart Processor {\n"
            "port feed {\nin item WaterIn;\n}\n"
            "port product {\nout item ProductOut;\n}\n"
            + declarations + "\n}\n}"
        )
        return sysml_to_json_transformer(0, source)["parts"][0]

    def test_imports_effects_and_orders_intermediates_but_keeps_static_parameters(self):
        part = self.part("""
            attribute ProductOut : Real = Recovered;
            attribute ProcessingTime = 2;
            attribute Recovered = WaterIn * yieldFactor;
            attribute yieldFactor = factor * 2;
            attribute factor = 0.4;
            attribute unrelated = WaterIn + 9;
        """)
        laws = part["operational_equations"]
        self.assertEqual(set(laws), {"ProductOut = Recovered", "ProcessingTime = 2",
                                     "Recovered = WaterIn * yieldFactor"})
        self.assertEqual(part["attributes"]["yieldFactor"], 0.8)
        outputs = evaluate_selected_equations("\n".join(laws), {"WaterIn": 10, **part["attributes"]},
                                              {"ProductOut", "ProcessingTime"})
        self.assertEqual(outputs["ProductOut"], 8)
        self.assertEqual(outputs["ProcessingTime"], 2)

    def test_imported_law_uses_original_units_of_normalized_properties(self):
        part = self.part("attribute volume = 2000;\nattribute ProcessingTime = volume / 1000;")
        outputs = evaluate_selected_equations("\n".join(part["operational_equations"]),
                                              {"volume_m3": 3}, {"ProcessingTime"})
        self.assertEqual(outputs["ProcessingTime"], 3)

    def test_output_inventory_on_a_producer_is_a_property(self):
        part = self.part("attribute ProductStored = 0;")
        self.assertEqual(part["operational_equations"], [])
        self.assertEqual(part["attributes"]["ProductStored"], 0)

    def test_storage_law_reads_previous_inventory(self):
        part = self.part("attribute WaterStored = WaterStored + WaterIn;")
        self.assertEqual(part["operational_equations"], ["WaterStored = WaterStored + WaterIn"])

    def test_cyclic_outputs_report_the_part_and_dependency(self):
        with self.assertRaisesRegex(ValueError, "Processor: cyclic operational equations"):
            self.part("attribute ProductOut = helper;\nattribute helper = ProductOut * 2;")

    def test_static_properties_and_descriptive_metadata_do_not_become_laws(self):
        part = self.part('attribute note = "WaterIn * factor";\nattribute area = 3 * 2;')
        self.assertEqual(part["operational_equations"], [])
        self.assertEqual(part["attributes"]["area"], 6)

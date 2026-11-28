"""Focused CPU tests for the Palace warm-start trainer and bundle contract."""

import contextlib
import io
import json
import math
import tempfile
import unittest
from pathlib import Path

import torch

import warmstart


class WarmStartTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def sample(self, name, omega=1.0, **changes):
        sample = dict(
            schema=warmstart.SAMPLE_SCHEMA, space_id="fixed mesh", n=3, omega=omega,
            excitation=1, rhs_norm=2.0, initial_residual=1.0, residual_norm=1e-8,
            epsilon=1e-7, field_real=[omega, 0.0, 0.0], field_imag=[0.0, -omega, 0.0],
        )
        sample.update(changes)
        path = self.root / name
        path.write_text(json.dumps(sample), encoding="utf-8")
        return path

    def test_cli_exports_training_only_pod_and_runtime_layout(self):
        before = self.sample("before.json", 0.5)
        one = self.sample("one.json")
        three = self.sample("three.json", 3.0)
        three_other = self.sample("three-other.json", 3.0, excitation=2)
        held = self.sample("held.json", 4.0, field_real=[4.0, 0.0, 10.0])
        output = self.root / "model.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            warmstart.main([
                "--train", str(one), str(three), str(three_other),
                "--validation", str(before), str(held),
                "--output", str(output), "--epochs", "8",
            ])
        bundle = json.loads(output.read_text(encoding="utf-8"))
        report = json.loads(stdout.getvalue())

        self.assertEqual(bundle["schema"], warmstart.MODEL_SCHEMA)
        self.assertEqual(bundle["rank"], 2)
        self.assertEqual(bundle["excitations"], [1, 2])
        self.assertEqual(bundle["basis"][2], [0.0, 0.0])
        self.assertAlmostEqual(bundle["mean"][0], 7.0 / 3.0)
        self.assertAlmostEqual(bundle["mean"][2], math.log1p(2.0))
        self.assertEqual(bundle["scale"][2], 1.0)
        widths = [3, 128, 128, 128, 128, 4]
        for layer, fan_in, fan_out in zip(bundle["layers"], widths, widths[1:]):
            self.assertEqual(len(layer["bias"]), fan_out)
            self.assertEqual(len(layer["weight"]), fan_out)
            self.assertTrue(all(len(row) == fan_in for row in layer["weight"]))
        self.assertEqual(report["train_examples"], 3)
        self.assertEqual(report["train_frequency_points"], 2)
        self.assertEqual(report["validation_examples"], 2)
        self.assertEqual(report["validation_history"]["examples"], 1)
        self.assertAlmostEqual(
            report["validation_history"]["history_coefficient"]["rmse"], math.sqrt(2.0 / 4)
        )
        self.assertAlmostEqual(
            report["validation_history"]["history_field"]["rmse"], math.sqrt(102.0 / 6)
        )

        # Independently evaluate the serialized dense layers and complex coefficient layout.
        all_coefficient_errors = []
        all_field_errors = []
        for sample in (warmstart.load_sample(before), warmstart.load_sample(held)):
            features = [sample.omega, sample.excitation, math.log1p(sample.rhs_norm)]
            values = [(x - m) / s for x, m, s in zip(features, bundle["mean"], bundle["scale"])]
            for index, layer in enumerate(bundle["layers"]):
                values = [math.fsum(w * x for w, x in zip(row, values)) + b
                          for row, b in zip(layer["weight"], layer["bias"])]
                if index < 4:
                    values = [x / (1.0 + math.exp(-x)) for x in values]
            basis = torch.tensor(bundle["basis"], dtype=torch.float64)
            coeff = torch.tensor(values, dtype=torch.float64).reshape(2, 2)
            all_coefficient_errors.append((coeff - sample.field @ basis).square().flatten())
            all_field_errors.append((coeff @ basis.T - sample.field).square().flatten())
        self.assertAlmostEqual(report["validation_coefficient"]["rmse"],
                               float(torch.cat(all_coefficient_errors).mean().sqrt()))
        self.assertAlmostEqual(report["validation_field"]["rmse"],
                               float(torch.cat(all_field_errors).mean().sqrt()))

    def test_rejects_duplicate_identity_even_in_distinct_files(self):
        one = self.sample("one.json")
        replay = self.sample("replay.json", rhs_norm=3.0)
        two = self.sample("two.json", 2.0)
        with self.assertRaisesRegex(ValueError, "duplicate sample identity"):
            warmstart.load_splits([one, replay], [two])
        with self.assertRaisesRegex(ValueError, "duplicate sample identity"):
            warmstart.load_splits([one], [replay])

    def test_rejects_frequency_leak_across_excitations(self):
        one = self.sample("one.json")
        one_other = self.sample("one-other.json", excitation=2)
        two_other = self.sample("two-other.json", 2.0, excitation=2)
        with self.assertRaisesRegex(ValueError, "frequency point crosses splits"):
            warmstart.load_splits([one, two_other], [one_other])

    def test_rejects_mixed_spaces_and_unseen_validation_excitation(self):
        one = self.sample("one.json")
        for changes, message in [
            ({"space_id": "other"}, "fixed space"),
            ({"n": 1, "field_real": [1.0], "field_imag": [0.0]}, "fixed space"),
            ({"excitation": 2}, "unsupported excitation"),
        ]:
            with self.subTest(changes=changes):
                two = self.sample("two.json", 2.0, **changes)
                with self.assertRaisesRegex(ValueError, message):
                    warmstart.load_splits([one], [two])

    def test_rejects_bad_sample_labels_and_values(self):
        for changes, message in [
            ({"schema": "v0"}, "expected schema"),
            ({"residual_norm": 1e-6}, "absolute residual tolerance"),
            ({"epsilon": -1.0}, "invalid"),
            ({"initial_residual": -1.0}, "invalid"),
            ({"rhs_norm": 0.0}, "invalid"),
            ({"excitation": True}, "integer"),
            ({"n": warmstart.MAX_DOFS + 1}, "integer"),
            ({"field_real": [1.0]}, "exactly n entries"),
            ({"field_imag": [1.0, float("nan"), 0.0]}, "finite"),
            ({"field_imag": [1.0, False, 0.0]}, "finite"),
        ]:
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, message):
                    warmstart.load_sample(self.sample("bad.json", **changes))

    def test_rejects_zero_numerical_rank(self):
        zero = self.sample("zero.json", field_real=[0.0] * 3, field_imag=[0.0] * 3)
        held = self.sample("held.json", 2.0)
        train, validation = warmstart.load_splits([zero], [held])
        with self.assertRaisesRegex(ValueError, "numerical rank zero"):
            warmstart.train_model(train, validation, rank=32, epochs=1, seed=0)


if __name__ == "__main__":
    unittest.main()

import csv
import json
import tempfile
import unittest
from pathlib import Path

from audit_research import CORPUS_FIELDS, audit


class ResearchAuditTest(unittest.TestCase):
    def make_dossier(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        rows = []
        for index in range(30):
            rows.append({
                "id": f"r{index:03d}",
                "url": f"https://example.com/traveler/{index}",
                "platform": f"community-{index % 3}",
                "source_role": "traveler",
                "published_at": "2026-08-01",
                "trip_date": "2026-07",
                "traveler_origin": "US",
                "trip_style": "self-drive",
                "season": "summer",
                "firsthand": "true",
                "topics": "car-coverage",
                "notes": "Paraphrased account with trip context and outcome.",
            })
        rows.append({
            "id": "provider-1",
            "url": "https://example.com/provider/terms",
            "platform": "rental-provider",
            "source_role": "provider",
            "published_at": "2026-09-01",
            "trip_date": "unknown",
            "traveler_origin": "unknown",
            "trip_style": "unknown",
            "season": "unknown",
            "firsthand": "false",
            "topics": "car-coverage",
            "notes": "Current provider terms and exclusions.",
        })
        with (root / "corpus.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CORPUS_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        dossier = {
            "schemaVersion": 1,
            "country": "IS",
            "audience": "en-US:first-time",
            "asOf": "2026-10-10",
            "status": "review-ready",
            "researchWindowMonths": 24,
            "travelModes": [{
                "id": "rental-car",
                "status": "primary",
                "travelerFit": "Travelers who want flexible stops with fixed lodging.",
                "advantages": ["Route flexibility"],
                "frictions": ["Driver workload"],
                "seasonality": "Conditions vary by season.",
                "sourceIds": ["r000", "provider-1"],
                "coverage": ["briefing:start-here"],
            }],
            "batches": [
                {"id": "b1", "scope": "Discovery", "sourceIds": ["r000"],
                 "newHighImpactTopics": ["car-coverage"], "newDecisionFactors": ["excess"]},
                {"id": "b2", "scope": "Counterexamples", "sourceIds": ["r001"],
                 "newHighImpactTopics": [], "newDecisionFactors": []},
                {"id": "b3", "scope": "Another community", "sourceIds": ["r002"],
                 "newHighImpactTopics": [], "newDecisionFactors": []},
            ],
            "topics": [{
                "id": "car-coverage",
                "title": "Decide coverage before the counter",
                "importance": "core",
                "risk": ["insurance"],
                "signal": "split",
                "sourceIds": ["r000", "r001", "r002", "r003", "r004", "r005", "provider-1"],
                "anecdotes": [
                    {"sourceId": "r000", "stance": "damage-covered",
                     "context": "Summer self-drive", "event": "Glass was damaged.",
                     "action": "Coverage was selected before arrival.",
                     "outcome": "The traveler reported reimbursement."},
                    {"sourceId": "r001", "stance": "no-damage",
                     "context": "Summer self-drive", "event": "No damage occurred.",
                     "action": "The traveler used ordinary precautions.",
                     "outcome": "The car was returned without a claim."},
                ],
                "synthesis": {
                    "travelerPattern": "Travelers repeatedly discuss several damage types.",
                    "counterPattern": "Outcomes and coverage reports differ.",
                    "decisionHelp": "Compare exclusions and reimbursement mechanics.",
                    "verify": "Obtain current written terms.",
                    "limits": "The corpus cannot establish an incident rate.",
                },
            }],
        }
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        return temp, root, dossier

    def test_strict_dossier_passes(self):
        temp, root, _ = self.make_dossier()
        self.addCleanup(temp.cleanup)
        errors, warnings = audit(root, strict=True)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_repeated_signal_rejects_one_community(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        dossier["topics"][0]["signal"] = "repeated"
        dossier["topics"][0]["sourceIds"] = ["r000", "r003", "r006", "r009", "r012", "r015", "provider-1"]
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("repeated signal" in error for error in errors))

    def test_missing_travel_modes_fails(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        del dossier["travelModes"]
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("travel mode" in error.lower() for error in errors))

    def test_primary_travel_mode_requires_reader_coverage(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        dossier["travelModes"][0]["coverage"] = []
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("coverage must be non-empty" in error for error in errors))

    def test_sensitive_topic_requires_verifying_source(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        dossier["topics"][0]["sourceIds"].remove("provider-1")
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("sensitive topic" in error for error in errors))

    def test_long_quote_fails(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        dossier["topics"][0]["anecdotes"][0]["quote"] = "word " * 26
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("quotation exceeds" in error for error in errors))

    def test_split_signal_requires_two_anecdote_stances(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        dossier["topics"][0]["anecdotes"][1]["stance"] = "damage-covered"
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("split signal needs anecdotes" in error for error in errors))

    def test_strict_saturation_rejects_new_factor_in_last_batch(self):
        temp, root, dossier = self.make_dossier()
        self.addCleanup(temp.cleanup)
        dossier["batches"][-1]["newDecisionFactors"] = ["seasonal-road-risk"]
        (root / "dossier.yaml").write_text(json.dumps(dossier), encoding="utf-8")
        errors, _ = audit(root, strict=True)
        self.assertTrue(any("last two batches" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

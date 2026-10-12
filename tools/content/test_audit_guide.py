import csv
import json
import tempfile
import unittest
from pathlib import Path

from audit_guide import audit
from audit_research import CORPUS_FIELDS


class GuideAuditTest(unittest.TestCase):
    def make_guide(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "research").mkdir()
        with (root / "research" / "corpus.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CORPUS_FIELDS)
            writer.writeheader()
            for index in range(1, 9):
                row = dict.fromkeys(CORPUS_FIELDS, "x")
                row.update({"id": f"r{index}", "url": "https://example.com", "firsthand": "true",
                            "source_role": "official" if index == 8 else "traveler"})
                writer.writerow(row)
        sources = [f"r{index}" for index in range(1, 9)]
        playbook = {
            "title": "Playbook", "hook": "A concrete stake.", "sourceIds": sources,
            "cardImage": {"src": "a.webp", "alt": "A described scene."},
            "body": [" ".join(["word"] * 80)] * 4,
            "decision": {"easiestPath": "a", "researchPath": "b", "acceptMoreRiskPath": "c"},
            "checklist": ["1", "2", "3", "4", "5"],
            "liveChecks": [{"label": "x", "url": "https://example.com"}] * 3,
        }
        route = {
            "title": "Route", "whoFor": "First-time drivers.", "duration": "4 nights",
            "days": [{"base": "B", "travel": "1 h", "highlights": ["h"]}] * 3
                    + [{"base": "B", "travel": "none", "highlights": ["h"], "flexible": True}],
            "seasonNotes": "Shorter in winter.", "tradeoff": "Long days.",
            "liveChecks": ["roads", "weather"], "sourceIds": sources,
        }
        briefing = {"schemaVersion": 1, "briefings": [{"id": "b", "title": "Brief",
            "hook": "Hook", "sections": [{"sourceIds": ["r1"]}] * 3}]}
        playbooks = {"schemaVersion": 1, "playbooks": [
            {"id": f"p{i}", **playbook} for i in range(5)]}
        routes = {"schemaVersion": 1, "routes": [
            {"id": f"route{i}", **route} for i in range(3)]}
        for name, data in [("briefings.yaml", briefing), ("playbooks.yaml", playbooks),
                           ("routes.yaml", routes)]:
            (root / name).write_text(json.dumps(data), encoding="utf-8")
        return temp, root

    def test_valid_guide_passes(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        self.assertEqual([], audit(root))

    def test_unknown_source_fails(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        data = json.loads((root / "routes.yaml").read_text(encoding="utf-8"))
        data["routes"][0]["sourceIds"] = ["missing"]
        (root / "routes.yaml").write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("unknown source" in error for error in audit(root)))


    def test_thin_playbook_fails_depth(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        data = json.loads((root / "playbooks.yaml").read_text(encoding="utf-8"))
        data["playbooks"][0]["body"] = ["Too short."]
        data["playbooks"][0]["evidenceLabel"] = "Experiences vary"
        (root / "playbooks.yaml").write_text(json.dumps(data), encoding="utf-8")
        errors = audit(root)
        self.assertTrue(any("p0: depth: body" in error for error in errors))
        self.assertTrue(any("travelerStories" in error for error in errors))
        self.assertTrue(any("limits" in error for error in errors))

    def test_route_without_days_fails_depth(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        data = json.loads((root / "routes.yaml").read_text(encoding="utf-8"))
        del data["routes"][0]["days"]
        (root / "routes.yaml").write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("route0: depth: days" in error for error in audit(root)))


    def test_basics_needs_pronounced_names_and_iconned_numbers(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        basics = {"names": [{"english": "A", "local": "A", "respelling": "ah", "meaning": "x", "sourceIds": ["r1"]},
                            {"english": "B", "local": "B", "respelling": "", "meaning": "x", "sourceIds": ["r1"]}],
                  "numbers": [{"label": str(i), "sourceIds": ["r1"]} for i in range(4)]}
        (root / "basics.yaml").write_text(json.dumps(basics), encoding="utf-8")
        errors = audit(root)
        self.assertTrue(any("respelling is required" in e for e in errors))
        self.assertTrue(any("an icon is required" in e for e in errors))


    def test_vocabulary_needs_courtesy_and_emergency_groups(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        vocab = {"rules": {"maxWords": 2}, "groups": [{"id": "courtesy", "alwaysShow": True}],
                 "extraWords": [{"local": "Slys", "respelling": "", "meaning": "Accident", "sourceIds": ["r1"]},
                                {"local": "Hringdu í lögregluna", "respelling": "x", "meaning": "Call the police", "sourceIds": ["r1"]}]}
        (root / "vocabulary.yaml").write_text(json.dumps(vocab), encoding="utf-8")
        errors = audit(root)
        self.assertTrue(any("emergency group is required" in e for e in errors))
        self.assertTrue(any("respelling is required" in e for e in errors))
        self.assertTrue(any("keep the word page simple" in e for e in errors))


    def test_map_points_must_fall_on_the_map(self):
        temp, root = self.make_guide()
        self.addCleanup(temp.cleanup)
        outline = [[-24.0 + i * 0.1, 63.0 + (i % 7) * 0.2] for i in range(80)]
        bad = {"outline": outline, "credit": "x", "sourceIds": ["r1"],
               "points": [{"id": "a", "kind": "town", "lon": -21.9, "lat": 63.5},
                          {"id": "b", "kind": "town", "lon": 5.0, "lat": 52.0}],
               "lines": []}
        (root / "map.yaml").write_text(json.dumps(bad), encoding="utf-8")
        errors = audit(root)
        self.assertTrue(any("point b: outside" in e for e in errors))
        self.assertFalse(any("point a" in e for e in errors))


    def test_route_places_must_exist(self):
        from audit_guide import route_place_errors
        route = {"id": "r", "days": [{"placeIds": ["sight-a", "soak:blue-lagoon", "sight-missing", "soak:nowhere"]}]}
        errors = route_place_errors(route, {"sight-a"}, {"blue-lagoon"})
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("sight-missing" in e for e in errors))
        self.assertTrue(any("soak:nowhere" in e for e in errors))


    def test_article_layout_fields_are_checked(self):
        from audit_guide import layout_errors
        item = {"id": "g", "body": ["a", "b", "c"], "keyPoints": ["one"],
                "sectionBreaks": [{"at": 1, "title": "x"}, {"at": 1, "title": "y"}],
                "figures": [{"after": 5, "placeId": "sight-nowhere", "caption": ""}]}
        errors = layout_errors(item, "playbooks.yaml", {"sight-a"})
        self.assertTrue(any("keyPoints" in e for e in errors))
        self.assertTrue(any("sectionBreaks" in e for e in errors))
        self.assertTrue(any("does not exist" in e for e in errors))
        self.assertTrue(any("caption" in e for e in errors))
        self.assertTrue(any("after" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

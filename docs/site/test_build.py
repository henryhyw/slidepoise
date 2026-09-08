"""Contract checks for the portable showcase, using no production artifacts."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("showcase_build", Path(__file__).with_name("build.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PortableShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="slidepoise-site-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "source"
        self.site = self.root / "docs" / "site"
        self.example = self.root / "examples" / "sample"
        self.site.mkdir(parents=True)
        self.example.mkdir(parents=True)
        for name in BUILDER.STATIC_FILES:
            (self.site / name).write_text("fixture", encoding="utf-8")
        (self.root / "LICENSE").write_text("License fixture", encoding="utf-8")
        for name in ("target.png", "render.png", "deck.pptx", "outline.json"):
            (self.example / name).write_text("artifact fixture", encoding="utf-8")
        (self.site / "showcases.json").write_text(json.dumps({
            "showcases": ["../../examples/sample/showcase.json"],
            "brief_sources": {"sample": "outline.json"},
            "planning_inputs": {"sample": {"s1": {"intent": "intent-s1.json", "inputs": [{"label": "Initial input", "path": "prompt.txt"}]}}},
            "workflow": {"sample": {"plan": ["outline.json"], "design": [], "reconstruct": [], "review": []}},
        }))
        self.manifest = {
            "id": "sample", "title": "Sample", "summary": "Packaging fixture",
            "slides": [{"id": "s1", "title": "First slide", "target": "target.png", "render": "render.png"}],
            "downloads": {"pptx": "deck.pptx"},
            "process": [{"title": "Outline", "description": "An actual file", "artifact": "outline.json"}],
        }
        self.write_manifest()
        self.patcher = patch.multiple(BUILDER, ROOT=self.root, SITE=self.site)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def write_manifest(self):
        (self.example / "outline.json").write_text(json.dumps({"title": "Sample", "throughline": "A test argument", "slides": [{"slide_id": slide["id"], "dominant_message": slide["title"]} for slide in self.manifest["slides"]]}))
        (self.example / "showcase.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.example / "prompt.txt").write_text("Preserve the test message and its supporting evidence.")
        inputs = {}
        for slide in self.manifest["slides"]:
            path = "intent-" + slide["id"] + ".json"
            (self.example / path).write_text(json.dumps({"dominant_message": slide["title"], "required_content": ["Supporting content"]}))
            inputs[slide["id"]] = {"intent": path, "inputs": [{"label": "Initial input", "path": "prompt.txt"}]}
        index_path = self.site / "showcases.json"
        index = json.loads(index_path.read_text())
        index["planning_inputs"] = {"sample": inputs}
        index_path.write_text(json.dumps(index))

    def attach_object_documents(self):
        for page, slide in enumerate(self.manifest["slides"], start=1):
            slide["objects"] = f"{slide['id']}-objects.json"
            document = {
                "schema_version": 1, "slide_id": slide["id"], "page_number": page,
                "objects": [],
                "source": {
                    "pptx": {"path": "deck.pptx", "sha256": BUILDER.sha256(self.example / "deck.pptx")},
                    "render": {"path": slide["render"], "sha256": BUILDER.sha256(self.example / slide["render"])},
                },
            }
            (self.example / slide["objects"]).write_text(json.dumps(document), encoding="utf-8")
        self.write_manifest()

    def test_bundle_preserves_complete_evidence_and_verifiable_inventory(self):
        (self.example / "unlisted-review.txt").write_text("Retained evidence", encoding="utf-8")
        output = Path(self.temporary.name) / "bundle"
        BUILDER.build(output, BUILDER.validate())
        inventory = json.loads((output / "asset-inventory.json").read_text())
        self.assertTrue((output / "examples/sample/unlisted-review.txt").is_file())
        for item in inventory["files"]:
            artifact = output / item["path"]
            self.assertEqual(item["sha256"], BUILDER.sha256(artifact))
            self.assertEqual(item["bytes"], artifact.stat().st_size)
        self.assertIn("docs/site/", (output / "index.html").read_text())

    def test_entrypoint_requests_the_styles_and_script_from_its_build(self):
        markup = '<link href="styles.css"><script src="app.mjs"></script>'
        (self.site / "index.html").write_text(markup)
        first = Path(self.temporary.name) / "first"
        BUILDER.build(first, BUILDER.validate())
        old_html = (first / "docs/site/index.html").read_text()
        old_style = BUILDER.sha256(self.site / "styles.css")[:16]
        self.assertIn(f'"styles.css?v={old_style}"', old_html)
        script_version = BUILDER.sha256(self.site / "app.mjs")[:16]
        self.assertIn(f'"app.mjs?v={script_version}"', old_html)
        (self.site / "styles.css").write_text("body { color: black; }")
        second = Path(self.temporary.name) / "second"
        BUILDER.build(second, BUILDER.validate())
        new_html = (second / "docs/site/index.html").read_text()
        self.assertNotIn(f'"styles.css?v={old_style}"', new_html)
        self.assertIn(f'"app.mjs?v={script_version}"', new_html)
        self.assertEqual((self.site / "index.html").read_text(), markup)

    def test_presentation_goal_cannot_link_to_another_slides_outline(self):
        BUILDER.validate()
        path = self.example / "outline.json"
        outline = json.loads(path.read_text())
        outline["slides"][0]["slide_id"] = "a-different-slide"
        path.write_text(json.dumps(outline))
        with self.assertRaisesRegex(ValueError, "actual slides in order"):
            BUILDER.validate()

    def test_missing_full_planning_content_cannot_publish_a_headline_only_view(self):
        path = self.example / "intent-s1.json"
        path.write_text(json.dumps({"dominant_message": "First slide", "required_content": []}))
        with self.assertRaisesRegex(ValueError, "required content"):
            BUILDER.validate()
        self.write_manifest()
        (self.example / "prompt.txt").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or empty artifact"):
            BUILDER.validate()

    def test_missing_reconstruction_cannot_be_published(self):
        (self.example / "render.png").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or empty artifact"):
            BUILDER.validate()

    def test_artifacts_cannot_escape_the_example(self):
        self.manifest["slides"][0]["target"] = "../../LICENSE"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "escapes"):
            BUILDER.validate()

    def test_duplicate_slide_identity_is_rejected(self):
        self.manifest["slides"].append(dict(self.manifest["slides"][0]))
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Duplicate slide id"):
            BUILDER.validate()

    def test_existing_output_survives_an_attempted_build(self):
        output = Path(self.temporary.name) / "published"
        output.mkdir()
        sentinel = output / "index.html"
        sentinel.write_text("Previous release", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            BUILDER.build(output, BUILDER.validate())
        self.assertEqual(sentinel.read_text(), "Previous release")

    def test_replaced_powerpoint_requires_fresh_object_extraction(self):
        self.attach_object_documents()
        BUILDER.validate()
        (self.example / "deck.pptx").write_text("New PowerPoint with different geometry", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Object pptx binding is stale"):
            BUILDER.validate()
        self.attach_object_documents()
        BUILDER.validate()

    def test_changed_render_cannot_keep_old_selection_geometry(self):
        self.attach_object_documents()
        (self.example / "render.png").write_text("Updated rendered slide", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Object render binding is stale"):
            BUILDER.validate()

    def test_duplicate_browser_object_ids_cannot_be_packaged(self):
        self.attach_object_documents()
        path = self.example / self.manifest["slides"][0]["objects"]
        document = json.loads(path.read_text())
        document["objects"] = [{"id": "p1-3"}, {"id": "p1-3"}]
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, "duplicate browser object ids"):
            BUILDER.validate()

    def test_reordered_slides_require_matching_object_page_numbers(self):
        self.manifest["slides"].append({
            "id": "s2", "title": "Second slide", "target": "target.png", "render": "render.png",
        })
        self.attach_object_documents()
        BUILDER.validate()
        self.manifest["slides"].reverse()
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Object slide identity or page order"):
            BUILDER.validate()

    def test_body_only_target_retains_its_full_slide_coordinates(self):
        self.manifest["canvas"] = {"full_slide_px": [1920, 1080], "content_region_px": [0, 64, 1920, 960]}
        self.write_manifest()
        output = Path(self.temporary.name) / "body-only-bundle"
        BUILDER.build(output, BUILDER.validate())
        copied = json.loads((output / "examples/sample/showcase.json").read_text())
        self.assertEqual(copied["canvas"], self.manifest["canvas"])

    def test_invalid_content_regions_cannot_be_packaged(self):
        invalid = [
            {"full_slide_px": [1920, 1080], "content_region_px": [0, 64, 1920, 1080]},
            {"full_slide_px": [1920, 1080], "content_region_px": [-1, 64, 1920, 960]},
            {"full_slide_px": [1920, 1080], "content_region_px": [0, 64, 0, 960]},
            {"full_slide_px": [0, 1080], "content_region_px": [0, 64, 1920, 960]},
            {"full_slide_px": [1920, 1080], "content_region_px": [0, True, 1920, 960]},
            {"full_slide_px": [1920, 1080], "content_region_px": [0, float("nan"), 1920, 960]},
            {"full_slide_px": [1920, 1080], "content_region_px": [0, 64, 1920]},
        ]
        for canvas in invalid:
            with self.subTest(canvas=canvas):
                self.manifest["canvas"] = canvas
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, "Canvas"):
                    BUILDER.validate()

    def test_workflow_keeps_one_stage_per_retained_artifact(self):
        index = {"showcases": ["../../examples/sample/showcase.json"],
            "brief_sources": {"sample": "outline.json"},
            "planning_inputs": {"sample": {"s1": {"intent": "intent-s1.json", "inputs": [{"label": "Initial input", "path": "prompt.txt"}]}}}, "workflow": {
            "sample": {"plan": ["outline.json"], "design": [], "reconstruct": [], "review": []},
        }}
        path = self.site / "showcases.json"
        path.write_text(json.dumps(index))
        BUILDER.validate()
        index["workflow"]["sample"]["review"] = ["outline.json"]
        path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "every retained artifact exactly once"):
            BUILDER.validate()
        index["workflow"]["sample"]["review"] = []
        index["workflow"]["sample"]["plan"] = []
        path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "every retained artifact exactly once"):
            BUILDER.validate()
        del index["workflow"]
        path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "Workflow configuration must cover"):
            BUILDER.validate()

    def attach_walkthrough(self):
        self.manifest["slides"][0]["evidence"] = "target.png"
        self.attach_object_documents()
        object_path = self.example / "s1-objects.json"
        objects = json.loads(object_path.read_text())
        objects["objects"] = [{"id": "p1-1", "name": "capacity", "kind": "chart", "chart": {
            "series": [{"categories": ["Research\nsynthesis"], "values": [1944]}],
        }}]
        object_path.write_text(json.dumps(objects))
        sources = {
            "intent.json": {"required_content": [{"role": "native_chart", "categories": ["Research synthesis"], "values": [1944]}]},
            "semantic.json": {"provenance": {"source_sha256": BUILDER.sha256(self.example / "target.png")}, "entities": [{
                "id": "capacity", "kind": "chart", "bbox_hint": [10, 10, 200, 100], "chart_structure": {
                    "categories": ["Research\nsynthesis"], "series": [{"values": [1944]}],
                },
            }]},
            "measurement.json": {"entities": [{"id": "capacity", "measurement": {"visible_bbox": {"px": [12, 12, 190, 95]}}}]},
        }
        for name, data in sources.items():
            (self.example / name).write_text(json.dumps(data))
        index = {"showcases": ["../../examples/sample/showcase.json"],
            "brief_sources": {"sample": "outline.json"},
            "planning_inputs": {"sample": {"s1": {"intent": "intent-s1.json", "inputs": [{"label": "Initial input", "path": "prompt.txt"}]}}},
                 "workflow": {"sample": {"plan": ["outline.json"], "design": [], "reconstruct": [], "review": []}},
                 "walkthrough": {
            "showcase_id": "sample", "slide_id": "s1", "entity_id": "capacity", "intent": "intent.json",
            "semantic": "semantic.json", "measurement": "measurement.json", "measurement_image": "target.png",
        }}
        (self.site / "showcases.json").write_text(json.dumps(index))

    def test_walkthrough_cannot_explain_different_data_from_the_powerpoint(self):
        self.attach_walkthrough()
        BUILDER.validate()
        path = self.example / "s1-objects.json"
        objects = json.loads(path.read_text())
        objects["objects"][0]["chart"]["series"][0]["values"] = [1620]
        path.write_text(json.dumps(objects))
        with self.assertRaisesRegex(ValueError, "chart data differs"):
            BUILDER.validate()

    def test_walkthrough_cannot_reuse_semantics_from_a_replaced_target(self):
        self.attach_walkthrough()
        BUILDER.validate()
        (self.example / "target.png").write_text("A different generated chart")
        with self.assertRaisesRegex(ValueError, "different target image"):
            BUILDER.validate()


if __name__ == "__main__":
    unittest.main()

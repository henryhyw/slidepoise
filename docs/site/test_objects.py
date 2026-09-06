"""Check native object exports against actual DrawingML geometry and relationships."""

import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("showcase_objects", Path(__file__).with_name("extract_objects.py"))
OBJECTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OBJECTS)

NAMESPACES = " ".join(f'xmlns:{key}="{value}"' for key, value in OBJECTS.NS.items())


def native_package(slide_body, chart=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as package:
        package.writestr("ppt/presentation.xml", f'<p:presentation {NAMESPACES}><p:sldIdLst><p:sldId id="256" r:id="page"/></p:sldIdLst><p:sldSz cx="1000" cy="500"/></p:presentation>')
        package.writestr("ppt/_rels/presentation.xml.rels", f'<Relationships xmlns="{OBJECTS.NS["pr"]}"><Relationship Id="page" Target="slides/slide1.xml"/></Relationships>')
        package.writestr("ppt/slides/slide1.xml", f'<p:sld {NAMESPACES}><p:cSld><p:spTree>{slide_body}</p:spTree></p:cSld></p:sld>')
        if chart:
            package.writestr("ppt/slides/_rels/slide1.xml.rels", f'<Relationships xmlns="{OBJECTS.NS["pr"]}"><Relationship Id="actual-chart" Target="../charts/chart7.xml"/></Relationships>')
            package.writestr("ppt/charts/chart7.xml", f'<c:chartSpace {NAMESPACES}>{chart}</c:chartSpace>')
    stream.seek(0)
    return stream


class NativeObjectTests(unittest.TestCase):
    def test_reused_native_ids_preserve_distinct_browser_objects(self):
        source = native_package('''
          <p:sp><p:nvSpPr><p:cNvPr id="3" name="Rule"/></p:nvSpPr>
            <p:spPr><a:xfrm><a:off x="10" y="20"/><a:ext cx="700" cy="10"/></a:xfrm></p:spPr>
          </p:sp>
          <p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="3" name="Assumptions"/></p:nvGraphicFramePr>
            <p:xfrm><a:off x="10" y="100"/><a:ext cx="700" cy="300"/></p:xfrm>
            <a:graphic><a:graphicData><a:tbl><a:tr><a:tc><a:txBody><a:p><a:r><a:t>Research</a:t></a:r></a:p></a:txBody></a:tc></a:tr></a:tbl></a:graphicData></a:graphic>
          </p:graphicFrame>''')
        with zipfile.ZipFile(source) as package:
            first = OBJECTS.extract_slide(package, "ppt/slides/slide1.xml", (1000, 500), 1)
            repeated = OBJECTS.extract_slide(package, "ppt/slides/slide1.xml", (1000, 500), 1)
        self.assertEqual(first, repeated)
        self.assertEqual(len({item["id"] for item in first}), 2)
        self.assertEqual([item["native_id"] for item in first], ["3", "3"])
        self.assertEqual([item["kind"] for item in first], ["shape", "table"])
        self.assertEqual(first[1]["rows"], [["Research"]])
        self.assertEqual(first[1]["polygon"], [[.01, .2], [.71, .2], [.71, .8], [.01, .8]])

    def test_selection_uses_powerpoint_group_transform_and_text_breaks(self):
        source = native_package('''
          <p:grpSp><p:grpSpPr><a:xfrm>
            <a:off x="100" y="50"/><a:ext cx="400" cy="200"/>
            <a:chOff x="0" y="0"/><a:chExt cx="200" cy="100"/>
          </a:xfrm></p:grpSpPr>
            <p:sp><p:nvSpPr><p:cNvPr id="4" name="Recommendation"/></p:nvSpPr>
              <p:spPr><a:xfrm><a:off x="10" y="20"/><a:ext cx="50" cy="20"/></a:xfrm></p:spPr>
              <p:txBody><a:p><a:r><a:rPr sz="1800"><a:latin typeface="Arial"/></a:rPr><a:t>First line</a:t></a:r><a:br/><a:r><a:t>Second line</a:t></a:r></a:p></p:txBody>
            </p:sp>
          </p:grpSp>''')
        with zipfile.ZipFile(source) as package:
            [item] = OBJECTS.extract_slide(package, "ppt/slides/slide1.xml", (1000, 500), 1)
        self.assertEqual(item["polygon"], [[.12, .18], [.22, .18], [.22, .26], [.12, .26]])
        self.assertEqual(item["text"], "First line\nSecond line")
        self.assertEqual(item["typography"], [{"family": "Arial", "size_pt": 18}])

    def test_chart_values_follow_actual_relationship_and_preserve_empty_points(self):
        source = native_package('''
          <p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="8" name="Opportunity"/></p:nvGraphicFramePr>
            <p:xfrm><a:off x="10" y="20"/><a:ext cx="700" cy="400"/></p:xfrm>
            <a:graphic><a:graphicData><c:chart r:id="actual-chart"/></a:graphicData></a:graphic>
          </p:graphicFrame>''', '''
          <c:chart><c:plotArea><c:barChart><c:ser>
            <c:tx><c:strRef><c:f>Sheet1!B1</c:f><c:strCache><c:pt idx="0"><c:v>Hours</c:v></c:pt></c:strCache></c:strRef></c:tx>
            <c:cat><c:strRef><c:strCache><c:pt idx="0"><c:v>Research</c:v></c:pt><c:pt idx="1"><c:v>Proposal</c:v></c:pt><c:pt idx="2"><c:v>Retrieval</c:v></c:pt></c:strCache></c:strRef></c:cat>
            <c:val><c:numRef><c:numCache><c:pt idx="0"><c:v>12</c:v></c:pt><c:pt idx="2"><c:v>5</c:v></c:pt></c:numCache></c:numRef></c:val>
          </c:ser></c:barChart></c:plotArea></c:chart>''')
        with zipfile.ZipFile(source) as package:
            [item] = OBJECTS.extract_slide(package, "ppt/slides/slide1.xml", (1000, 500), 1)
        self.assertEqual(item["kind"], "chart")
        self.assertEqual(item["chart"]["series"], [{"name": "Hours", "categories": ["Research", "Proposal", "Retrieval"], "values": [12, None, 5]}])

    def test_export_binds_final_files_and_failed_replacement_preserves_manifest(self):
        source = native_package('''
          <p:sp><p:nvSpPr><p:cNvPr id="3" name="Native title"/></p:nvSpPr>
          <p:spPr><a:xfrm rot="5400000"><a:off x="100" y="100"/><a:ext cx="200" cy="100"/></a:xfrm></p:spPr>
          <p:txBody><a:p><a:r><a:t>A real title</a:t></a:r></a:p></p:txBody></p:sp>''')
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / "deck.pptx").write_bytes(source.getvalue())
            (base / "render.png").write_bytes(b"reviewed preview fixture")
            manifest = base / "showcase.json"
            data = {"downloads": {"pptx": "deck.pptx"}, "slides": [{"id": "s1", "render": "render.png"}]}
            manifest.write_text(json.dumps(data))
            OBJECTS.export(manifest)
            artifact = json.loads((base / "assets/s1-objects.json").read_text())
            self.assertEqual(artifact["source"]["pptx"]["sha256"], OBJECTS.sha256(base / "deck.pptx"))
            self.assertEqual(artifact["source"]["render"]["sha256"], OBJECTS.sha256(base / "render.png"))
            self.assertEqual(artifact["objects"][0]["polygon"], [[.25, .1], [.25, .5], [.15, .5], [.15, .1]])
            data["slides"].append({"id": "s2", "render": "render.png"})
            manifest.write_text(json.dumps(data))
            previous = manifest.read_bytes()
            with self.assertRaisesRegex(ValueError, "page counts differ"):
                OBJECTS.export(manifest)
            self.assertEqual(manifest.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()

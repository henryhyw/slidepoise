"""User-facing artifact contracts that survive relocation, failure and multi-page work."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/scripts"))

import slidepoise_runtime as runtime
from slidepoise.artifacts import ArtifactError, bundle_deck, load_deck, resolve_scene_paths, verify_bundle


def source_deck(root: Path) -> Path:
    root.mkdir()
    image = root / "original.png"
    Image.new("RGB", (80, 40), "#12A378").save(image)
    lineage = {"measurement": {"engine": "OpenCV", "opencv": "test"},
               "input_bindings": {key: "a" * 64 for key in (
                   "measured_scene_sha256", "reconstruction_contract_sha256", "resolved_design_sha256")}}
    for identity in ("opening", "closing"):
        runtime.write(root / f"{identity}.json", {"slide_id": identity, "dimensions_px": [1600, 900],
                      "compiler_report": lineage, "objects": [
                          {"id": "art", "kind": "image", "source_path": str(image), "bbox_px": [100, 100, 800, 400]},
                          {"id": "label", "kind": "textbox", "text": identity, "bbox_px": [100, 550, 800, 100],
                           "style": {"font_family": "Arial", "font_size_pt": 24}}]})
    manifest = root / "deck-scenes.json"
    runtime.write(manifest, {"title": "A portable deck", "slides": [
        {"slide_id": "closing", "scene": "closing.json"}, {"slide_id": "opening", "scene": "opening.json"}]})
    return manifest


def test_bundle_relocates_and_renders_without_original_files(tmp_path):
    source = tmp_path / "authoring"
    manifest = source_deck(source)
    evidence = source / "work"
    evidence.mkdir()
    runtime.write(evidence / "semantic-map.json", {"entities": [{"id": "art", "kind": "image"}]})
    runtime.write(evidence / "bundle.json", {"notes": "This source record also needs a content binding"})
    original = (source / "closing.json").read_bytes()
    output = tmp_path / "bundle"
    bundle_deck(manifest, output, [evidence])
    assert (source / "closing.json").read_bytes() == original
    assert len(list((output / "assets").iterdir())) == 1
    moved = tmp_path / "downloaded" / "case"
    moved.parent.mkdir()
    output.rename(moved)
    shutil.rmtree(source)
    facts = verify_bundle(moved)
    assert facts["slide_ids"] == ["closing", "opening"]
    assert facts["verified_files"] == 6
    final = tmp_path / "presentation.pptx"
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/slidepoise_runtime.py"), "render-deck",
                             "--manifest", str(moved / "deck-scenes.json"), "--output", str(final)],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(final) as package:
        assert "ppt/slides/slide2.xml" in package.namelist()
        assert "closing" in package.read("ppt/slides/slide1.xml").decode()
        assert "opening" in package.read("ppt/slides/slide2.xml").decode()
        media = [package.read(name) for name in package.namelist() if name.startswith("ppt/media/")]
        assert next((moved / "assets").iterdir()).read_bytes() in media
    (moved / "evidence/work/bundle.json").write_text("{}")
    with pytest.raises(ArtifactError, match="missing or changed"):
        verify_bundle(moved)


def test_bundle_detects_tampering_and_preserves_existing_output(tmp_path):
    manifest = source_deck(tmp_path / "source")
    bundle = tmp_path / "bundle"
    bundle_deck(manifest, bundle)
    record = (bundle / "bundle.json").read_bytes()
    with pytest.raises(ArtifactError, match="already exists"):
        bundle_deck(manifest, bundle)
    assert (bundle / "bundle.json").read_bytes() == record
    asset = next((bundle / "assets").iterdir())
    content = bytearray(asset.read_bytes())
    content[-1] ^= 1
    asset.write_bytes(content)
    with pytest.raises(ArtifactError, match="missing or changed"):
        verify_bundle(bundle)


def test_bundle_rejects_external_bindings_even_when_hashes_match(tmp_path):
    manifest = source_deck(tmp_path / "source")
    bundle = tmp_path / "bundle"
    bundle_deck(manifest, bundle)
    outside = tmp_path / "external.json"
    outside.write_text("{}")
    record = runtime.read(bundle / "bundle.json")
    record["files"].append({"path": "../external.json", "sha256": runtime.file_hash(outside), "bytes": 2})
    runtime.write(bundle / "bundle.json", record)
    with pytest.raises(ArtifactError, match="escapes"):
        verify_bundle(bundle)


def test_scene_resolution_has_no_implicit_cwd_or_ambiguous_fallback(tmp_path):
    local = tmp_path / "scenes"
    local.mkdir()
    for directory in (tmp_path, local):
        (directory / "art.png").write_bytes(b"image")
    scene = {"objects": [{"id": "art", "kind": "image", "source_path": "art.png"}]}
    with pytest.raises(ArtifactError, match="ambiguous"):
        resolve_scene_paths(scene, local / "scene.json")
    scene["asset_path_base"] = "scene"
    resolved = resolve_scene_paths(scene, local / "scene.json")
    assert resolved["objects"][0]["source_path"] == str(local / "art.png")
    assert scene["objects"][0]["source_path"] == "art.png"
    scene["objects"][0]["source_path"] = str(tmp_path / "missing.png")
    with pytest.raises(ArtifactError, match="does not exist"):
        resolve_scene_paths(scene, local / "scene.json")


@pytest.mark.parametrize("damage", ["duplicate_slide", "duplicate_object", "different_dimensions", "non_finite"])
def test_deck_input_errors_stop_before_rendering(tmp_path, damage):
    manifest_path = source_deck(tmp_path / "source")
    manifest = runtime.read(manifest_path)
    scene_path = manifest_path.parent / "opening.json"
    scene = runtime.read(scene_path)
    if damage == "duplicate_slide":
        manifest["slides"].append(manifest["slides"][0])
    elif damage == "duplicate_object":
        scene["objects"].append(scene["objects"][0])
    elif damage == "different_dimensions":
        scene["dimensions_px"][0] = 900
    else:
        scene["dimensions_px"][0] = float("nan")
    runtime.write(manifest_path, manifest)
    scene_path.write_text(json.dumps(scene))
    with pytest.raises(ArtifactError):
        load_deck(manifest_path)


def preview_source(root: Path, pages: int) -> Path:
    path = root / "deck.pptx"
    with zipfile.ZipFile(path, "w") as package:
        ids = "".join(f'<p:sldId id="{256 + page}"/>' for page in range(pages))
        package.writestr("ppt/presentation.xml",
                         '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                         f"<p:sldIdLst>{ids}</p:sldIdLst></p:presentation>")
    return path


@pytest.mark.parametrize("rendered_pages", [1, 2])
def test_deck_preview_publishes_only_complete_page_sets(tmp_path, monkeypatch, rendered_pages):
    source = preview_source(tmp_path, 2)
    output = tmp_path / "preview"
    args = runtime.parser().parse_args(["render-deck-preview", "--pptx", str(source), "--output-dir", str(output)])
    monkeypatch.setattr(runtime.shutil, "which", lambda name: name)
    calls = []

    def renderer(command, *, env=None):
        calls.append(command)
        if "--outdir" in command:
            (Path(command[command.index("--outdir") + 1]) / "deck.pdf").write_bytes(b"pdf")
        else:
            for page in range(1, rendered_pages + 1):
                Image.new("RGB", (160, 90), "#D2E8DE").save(f"{command[-1]}-{page}.png")

    monkeypatch.setattr(runtime, "run_checked", renderer)
    monkeypatch.setattr("slidepoise.rendered_text.collect_rendered_table_text",
                        lambda pptx, pdf: {"available": True, "cells": [], "discrepancies": []})
    if rendered_pages == 1:
        with pytest.raises(ArtifactError, match="produced 1 pages"):
            runtime.command_render_deck_preview(args)
        assert not output.exists()
    else:
        runtime.command_render_deck_preview(args)
        record = runtime.read(output / "preview-manifest.json")
        assert len(record["slides"]) == 2
        for page in record["slides"]:
            assert page["sha256"] == runtime.file_hash(output / page["render"])
        assert (output / "presentation.pdf").read_bytes() == b"pdf"
        with Image.open(output / "contact-sheet.png") as contact_sheet:
            assert contact_sheet.width > contact_sheet.height
    assert len([command for command in calls if "--convert-to" in command]) == 1


def test_native_xml_transform_preserves_namespace_geometry_and_signed_tracking(tmp_path):
    sys.path.insert(0, str(ROOT / "slidepoise/runtime/scripts"))
    import postprocess_pptx as native
    from lxml import etree

    xml = f'''<x:sld xmlns:x="{native.NS['p']}" xmlns:d="{native.NS['a']}"><x:cSld><x:spTree>
      <x:sp><x:nvSpPr><x:cNvPr name="title &amp; note" id="2"/><x:cNvSpPr txBox="1"/><x:nvPr/></x:nvSpPr>
      <x:spPr><d:prstGeom prst="roundRect"><d:avLst/></d:prstGeom></x:spPr>
      <x:txBody><d:bodyPr wrap="square"/><d:lstStyle/><d:p><d:r><d:rPr sz="7000"/><d:t>Condensed title</d:t></d:r></d:p></x:txBody></x:sp>
      <x:sp><x:nvSpPr><x:cNvPr name="SC_CONNECTOR__route" id="3"/><x:cNvSpPr txBox="0"/><x:nvPr/></x:nvSpPr>
      <x:spPr><d:custGeom><d:avLst/><d:pathLst><d:path w="100" h="100"/></d:pathLst></d:custGeom>
      <d:ln w="12700"><d:solidFill><d:srgbClr val="222222"/></d:solidFill><d:tailEnd type="triangle" w="sm" len="sm"/></d:ln></x:spPr></x:sp>
      </x:spTree></x:cSld></x:sld>'''
    output, converted, text, rounding = native.process_xml(xml, {"title & note": 12345}, {"title & note": -333})
    assert (converted, text, rounding) == (1, 1, 1)
    result = etree.fromstring(output.encode())
    assert result.nsmap == {"x": native.NS["p"], "d": native.NS["a"]}
    assert result.find('.//a:rPr', native.NS).get("spc") == "-333"
    assert result.find('.//a:defRPr', native.NS).get("spc") == "-333"
    assert result.find('.//a:gd', native.NS).get("fmla") == "val 12345"
    connector = result.find('.//p:cxnSp', native.NS)
    assert connector.find('p:nvCxnSpPr/p:cNvCxnSpPr', native.NS) is not None
    assert connector.find('p:spPr/a:custGeom/a:pathLst/a:path', native.NS).attrib == {"w": "100", "h": "100"}
    assert connector.find('.//a:tailEnd', native.NS).attrib == {"type": "triangle", "w": "sm", "len": "sm"}
    assert connector.find('.//a:round', native.NS) is not None
    repeated = native.process_xml(output, {"title & note": 12345}, {"title & note": -333})
    assert repeated[1:] == (0, 0, 0)


def test_native_xml_failure_keeps_the_previous_archive(tmp_path):
    sys.path.insert(0, str(ROOT / "slidepoise/runtime/scripts"))
    import postprocess_pptx as native

    path = tmp_path / "presentation.pptx"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("ppt/slides/slide1.xml", "<broken")
        package.writestr("ppt/media/image.png", b"original media")
    before = path.read_bytes()
    with pytest.raises(Exception, match="Start tag expected|Couldn't find end of Start Tag"):
        native.postprocess(path)
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_chart_label_treatment_follows_named_slide_relationship_and_is_idempotent(tmp_path):
    from lxml import etree
    sys.path.insert(0, str(ROOT / "slidepoise/runtime/scripts"))
    import postprocess_pptx as native

    slide = f'''<p:sld xmlns:p="{native.NS['p']}" xmlns:a="{native.NS['a']}"
      xmlns:c="{native.NS['c']}" xmlns:r="{native.NS['r']}"><p:cSld><p:spTree>
      <p:graphicFrame><p:nvGraphicFramePr><p:cNvPr name="hours &amp; cost"/></p:nvGraphicFramePr>
      <a:graphic><a:graphicData><c:chart r:id="chart-id"/></a:graphicData></a:graphic>
      </p:graphicFrame></p:spTree></p:cSld></p:sld>'''
    chart = f'''<c:chartSpace xmlns:c="{native.NS['c']}" xmlns:a="{native.NS['a']}">
      <c:chart><c:plotArea><c:barChart><c:dLbls><c:numFmt formatCode="0.0" sourceLinked="1"/>
      <c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1650">
      <a:solidFill><a:srgbClr val="123456"/></a:solidFill><a:latin typeface="Arial"/>
      </a:defRPr></a:pPr></a:p></c:txPr><c:showVal val="1"/>
      </c:dLbls></c:barChart></c:plotArea></c:chart></c:chartSpace>'''
    path = tmp_path / "presentation.pptx"
    with zipfile.ZipFile(path, "w") as package:
        for index in (1, 2):
            package.writestr(f"ppt/slides/slide{index}.xml", slide)
            package.writestr(f"ppt/slides/_rels/slide{index}.xml.rels",
                f'<Relationships xmlns="{native.NS["pr"]}"><Relationship Id="chart-id" '
                f'Type="{native.NS["r"]}/chart" Target="../charts/chart{index}.xml"/></Relationships>')
            package.writestr(f"ppt/charts/chart{index}.xml", chart)
        package.writestr("ppt/embeddings/workbook.xlsx", b"unchanged workbook values")
    metadata = {"slides": {"ppt/slides/slide2.xml": {"chart_label_treatments": {
        "hours & cost": {"position": "outEnd", "colors": ["#FD5108", "000000"]}}}}}
    assert native.postprocess(path, metadata)["chartLabelTreatmentsApplied"] == 1
    with zipfile.ZipFile(path) as package:
        assert package.read("ppt/charts/chart1.xml") == chart.encode()
        assert package.read("ppt/embeddings/workbook.xlsx") == b"unchanged workbook values"
        edited = etree.fromstring(package.read("ppt/charts/chart2.xml"))
    labels = edited.find(".//c:dLbls", native.NS)
    assert labels.find("c:dLblPos", native.NS).get("val") == "outEnd"
    assert labels.find("c:numFmt", native.NS).attrib == {"formatCode": "0.0", "sourceLinked": "1"}
    assert labels.find("c:txPr//a:srgbClr", native.NS).get("val") == "123456"
    for index, point in enumerate(labels.findall("c:dLbl", native.NS)):
        assert point.find("c:idx", native.NS).get("val") == str(index)
        assert point.find(".//a:defRPr", native.NS).get("sz") == "1650"
        assert point.find(".//a:latin", native.NS).get("typeface") == "Arial"
        assert point.find(".//a:srgbClr", native.NS).get("val") == ["FD5108", "000000"][index]
        assert point.find("c:tx", native.NS) is None
    assert native.postprocess(path, metadata)["chartLabelTreatmentsApplied"] == 0
    before = path.read_bytes()
    metadata["slides"]["ppt/slides/slide2.xml"]["chart_label_treatments"]["missing"] = {"position": "outEnd"}
    with pytest.raises(ValueError, match="missing chart objects"):
        native.postprocess(path, metadata)
    assert path.read_bytes() == before


def test_opencv_search_window_does_not_move_the_authored_textbox(tmp_path):
    from PIL import ImageDraw

    target = Image.new("RGB", (100, 100), "white")
    ImageDraw.Draw(target).rectangle((20, 50, 50, 56), fill="black")
    image = tmp_path / "target.png"
    target.save(image)
    semantic = tmp_path / "semantic.json"
    runtime.write(semantic, {"entities": [{"id": "title", "kind": "text", "text": "Source ink",
                  "bbox_hint": [2, 2, 80, 70], "search_bbox_hint": [10, 40, 60, 25], "geometry_policy": "agent_logical"}]})
    config = tmp_path / "config.json"
    runtime.write(config, {"measurement": {"sam": {"enabled": False}}})
    command = [sys.executable, str(ROOT / "slidepoise/runtime/scripts/measure_visual_scene.py"), str(image),
               "--semantic-map", str(semantic), "--config", str(config), "--output-dir", str(tmp_path / "measurement"),
               "--sam", "never"]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    measured = runtime.read(tmp_path / "measurement/slide_entities.json")["entities"][0]["measurement"]
    assert measured["layout_bbox"]["px"] == [2, 2, 80, 70]
    assert measured["search_bbox"]["px"] == [10, 40, 60, 25]
    assert measured["visible_bbox"]["px"][1] >= 50
    broken = runtime.read(semantic)
    broken["entities"][0]["search_bbox_hint"] = [200, 200, 20, 20]
    runtime.write(semantic, broken)
    failed = subprocess.run(command, capture_output=True, text=True)
    assert failed.returncode != 0 and "no pixels inside" in failed.stderr

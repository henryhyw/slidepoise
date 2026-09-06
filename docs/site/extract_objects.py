#!/usr/bin/env python3
"""Export read-only selection geometry and content from the delivered PowerPoint.

The browser displays the reviewed render. Its selection regions come from actual
DrawingML objects, including group transforms, and are bound to both final files.
This is an inspector export, not a second slide renderer or a PowerPoint editor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import posixpath
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml(package: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(package.read(name))


def relationships(package: zipfile.ZipFile, part: str) -> dict[str, str]:
    rel_path = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if rel_path not in package.namelist():
        return {}
    result = {}
    for rel in xml(package, rel_path):
        if rel.get("TargetMode") == "External":
            continue
        target = rel.attrib["Target"]
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(part), target)).lstrip("/")
        if resolved.startswith("../") or resolved not in package.namelist():
            raise ValueError(f"Missing internal PowerPoint relationship in {part}")
        result[rel.attrib["Id"]] = resolved
    return result


def multiply(left: tuple, right: tuple) -> tuple:
    a, b, c, d, e, f = left
    g, h, i, j, k, l = right
    return (a * g + c * h, b * g + d * h, a * i + c * j,
            b * i + d * j, a * k + c * l + e, b * k + d * l + f)


def translation(x: float, y: float) -> tuple:
    return (1, 0, 0, 1, x, y)


def transform_point(matrix: tuple, x: float, y: float) -> list[float]:
    a, b, c, d, e, f = matrix
    return [a * x + c * y + e, b * x + d * y + f]


def transform_values(xfrm: ET.Element) -> tuple:
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        raise ValueError("A selectable PowerPoint object is missing its transform")
    values = tuple(float(node.attrib[key]) for node, key in
                   ((off, "x"), (off, "y"), (ext, "cx"), (ext, "cy")))
    if not all(math.isfinite(value) for value in values) or min(values[2:]) < 0:
        raise ValueError("PowerPoint geometry must be finite with nonnegative dimensions")
    return values


def rotation_flip(xfrm: ET.Element, cx: float, cy: float) -> tuple:
    angle = math.radians(float(xfrm.get("rot", "0")) / 60000)
    cosine, sine = math.cos(angle), math.sin(angle)
    rotation = (cosine, sine, -sine, cosine, 0, 0)
    flip = (-1 if xfrm.get("flipH") in ("1", "true") else 1, 0, 0,
            -1 if xfrm.get("flipV") in ("1", "true") else 1, 0, 0)
    return multiply(translation(cx, cy), multiply(rotation, multiply(flip, translation(-cx, -cy))))


def group_transform(xfrm: ET.Element) -> tuple:
    x, y, width, height = transform_values(xfrm)
    child_off, child_ext = xfrm.find("a:chOff", NS), xfrm.find("a:chExt", NS)
    if child_off is None or child_ext is None:
        raise ValueError("PowerPoint group is missing its child coordinate space")
    child_width, child_height = float(child_ext.attrib["cx"]), float(child_ext.attrib["cy"])
    if child_width <= 0 or child_height <= 0:
        raise ValueError("PowerPoint group has an empty child coordinate space")
    scaling = (width / child_width, 0, 0, height / child_height, 0, 0)
    offset = translation(-float(child_off.attrib["x"]), -float(child_off.attrib["y"]))
    placed = multiply(translation(x, y), multiply(scaling, offset))
    return multiply(rotation_flip(xfrm, x + width / 2, y + height / 2), placed)


def text_content(node: ET.Element) -> str:
    paragraphs = []
    for paragraph in node.findall(".//a:p", NS):
        fragments = []
        for child in paragraph:
            if child.tag == f"{{{NS['a']}}}br":
                fragments.append("\n")
            else:
                fragments.extend(text.text or "" for text in child.findall(".//a:t", NS))
        paragraphs.append("".join(fragments))
    return "\n".join(paragraphs).strip()


def typography(node: ET.Element) -> list[dict]:
    styles = []
    for properties in node.findall(".//a:rPr", NS) + node.findall(".//a:defRPr", NS):
        style = {}
        family = properties.find("a:latin", NS)
        color = properties.find("a:solidFill/a:srgbClr", NS)
        if family is not None:
            style["family"] = family.get("typeface")
        if properties.get("sz"):
            style["size_pt"] = int(properties.get("sz")) / 100
        if color is not None:
            style["color"] = "#" + color.attrib["val"]
        for key, name in (("b", "bold"), ("i", "italic")):
            if properties.get(key) is not None:
                style[name] = properties.get(key) in ("1", "true")
        if style and style not in styles:
            styles.append(style)
    return styles


def chart_data(package: zipfile.ZipFile, part: str) -> dict:
    root = xml(package, part)
    plot = root.find("c:chart/c:plotArea", NS)
    if plot is None:
        raise ValueError("Native chart has no plot area")
    chart_types = [child.tag.split("}")[-1] for child in plot if child.tag.endswith("Chart")]
    series = []
    for item in plot.findall(".//c:ser", NS):
        name_node = item.find("c:tx", NS)
        name = " ".join(name_node.itertext()).strip() if name_node is not None else "Series"
        cached_name = item.find("c:tx/c:strRef/c:strCache/c:pt/c:v", NS)
        if cached_name is not None:
            name = cached_name.text or "Series"
        categories = item.findall("c:cat//c:pt", NS)
        values = item.findall("c:val//c:pt", NS)
        if not values:
            values = item.findall("c:yVal//c:pt", NS)
            categories = item.findall("c:xVal//c:pt", NS)
        value_map = {int(point.attrib["idx"]): float(point.findtext("c:v", namespaces=NS)) for point in values}
        category_map = {int(point.attrib["idx"]): point.findtext("c:v", default="", namespaces=NS) for point in categories}
        count = max([*value_map, *category_map], default=-1) + 1
        series.append({"name": name, "categories": [category_map.get(i, str(i + 1)) for i in range(count)],
                       "values": [value_map.get(i) for i in range(count)]})
    return {"types": chart_types, "series": series}


def human_name(name: str, kind: str, content: str) -> str:
    if kind == "text" and content:
        words = content.replace("\n", " ").split()
        return " ".join(words[:10]) + ("…" if len(words) > 10 else "")
    name = name.removeprefix("SC_CONNECTOR__").removeprefix("SC_FREEFORM__")
    words = name.replace("__", " ").replace("_", " ").replace("-", " ").strip().split()
    return " ".join(words).capitalize() or kind.capitalize()


def extract_slide(package: zipfile.ZipFile, part: str, size: tuple, page: int) -> list[dict]:
    root = xml(package, part)
    rels = relationships(package, part)
    objects = []

    def visit(parent: ET.Element, ancestor: tuple = IDENTITY) -> None:
        for node in parent:
            tag = node.tag.split("}")[-1]
            if tag == "grpSp":
                xfrm = node.find("p:grpSpPr/a:xfrm", NS)
                if xfrm is None:
                    raise ValueError("PowerPoint group is missing a transform")
                visit(node, multiply(ancestor, group_transform(xfrm)))
                continue
            if tag not in ("sp", "pic", "cxnSp", "graphicFrame"):
                continue
            native = node.find(".//p:cNvPr", NS)
            if native is None or native.get("hidden") in ("1", "true"):
                continue
            xfrm = node.find("p:spPr/a:xfrm", NS)
            if xfrm is None:
                xfrm = node.find("p:xfrm", NS)
            if xfrm is None:
                raise ValueError(f"Object {native.get('name')} has no explicit selection geometry")
            x, y, width, height = transform_values(xfrm)
            matrix = multiply(ancestor, rotation_flip(xfrm, x + width / 2, y + height / 2))
            corners = [transform_point(matrix, *point) for point in
                       ((x, y), (x + width, y), (x + width, y + height), (x, y + height))]
            polygon = [[round(px / size[0], 9), round(py / size[1], 9)] for px, py in corners]
            kind = {"pic": "image", "cxnSp": "connector"}.get(tag, "shape")
            content = text_content(node)
            chart = node.find(".//c:chart", NS)
            table = node.find(".//a:tbl", NS)
            if chart is not None:
                kind = "chart"
            elif table is not None:
                kind = "table"
            elif content:
                kind = "text"
            name = native.get("name", "")
            # Reader-visible objects can carry reused cNvPr IDs in a source file.
            # The export is bound to that exact file, so traversal order provides
            # a unique browser identity while native_id preserves the source fact.
            item = {"id": f"p{page}-object-{len(objects) + 1}", "native_id": native.attrib["id"],
                    "name": name, "label": human_name(name, kind, content), "kind": kind,
                    "polygon": polygon, "stack": len(objects)}
            if content and kind == "text":
                item.update(text=content, typography=typography(node))
            if chart is not None:
                relationship = chart.attrib[f"{{{NS['r']}}}id"]
                if relationship not in rels:
                    raise ValueError("Native chart relationship is missing")
                item["chart"] = chart_data(package, rels[relationship])
            if table is not None:
                item["rows"] = [[text_content(cell) for cell in row.findall("a:tc", NS)] for row in table.findall("a:tr", NS)]
            if tag == "cxnSp":
                item["line"] = [polygon[0], polygon[2]]
                item["arrows"] = {end: element.attrib for end in ("headEnd", "tailEnd")
                                  if (element := node.find(f"p:spPr/a:ln/a:{end}", NS)) is not None}
            objects.append(item)

    tree = root.find("p:cSld/p:spTree", NS)
    if tree is None:
        raise ValueError("PowerPoint slide has no shape tree")
    visit(tree)
    return objects


def local_file(base: Path, value: str) -> Path:
    path = (base / value).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError(f"Expected an existing file inside the example directory, received {value!r}")
    return path


def export(manifest: Path) -> dict:
    manifest = manifest.resolve()
    data = json.loads(manifest.read_text())
    base = manifest.parent
    pptx = local_file(base, data["downloads"]["pptx"])
    source_hash = sha256(pptx)
    outputs = []
    with zipfile.ZipFile(pptx) as package:
        presentation = xml(package, "ppt/presentation.xml")
        dimensions = presentation.find("p:sldSz", NS)
        size = (int(dimensions.attrib["cx"]), int(dimensions.attrib["cy"]))
        rels = relationships(package, "ppt/presentation.xml")
        slide_parts = [rels[node.attrib[f"{{{NS['r']}}}id"]] for node in presentation.findall("p:sldIdLst/p:sldId", NS)]
        if len(slide_parts) != len(data["slides"]):
            raise ValueError("Showcase and PowerPoint page counts differ")
        for page, (slide, part) in enumerate(zip(data["slides"], slide_parts), 1):
            render = local_file(base, slide["render"])
            # Reuse the declared slide id without permitting paths outside assets.
            slide_id = slide["id"]
            if not isinstance(slide_id, str) or not slide_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for character in slide_id):
                raise ValueError("Slide ids must be safe filename identifiers")
            relative = f"assets/{slide_id}-objects.json"
            result = {"schema_version": 1, "slide_id": slide_id, "page_number": page,
                      "size": {"width": size[0], "height": size[1], "unit": "emu"},
                      "source": {"pptx": {"path": data["downloads"]["pptx"], "sha256": source_hash},
                                 "render": {"path": slide["render"], "sha256": sha256(render)}},
                      "objects": extract_slide(package, part, size, page)}
            outputs.append((relative, result))
            slide["objects"] = relative
    if sha256(pptx) != source_hash:
        raise ValueError("The PowerPoint changed during object extraction. Run the export again.")
    # Publish only after every page has been read successfully.
    for relative, result in outputs:
        output = base / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as temporary:
            json.dump(result, temporary, ensure_ascii=False, indent=2, allow_nan=False)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        temporary_path.replace(output)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=base, delete=False) as temporary:
        json.dump(data, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(manifest)
    return {"manifest": str(manifest), "pptx_sha256": source_hash,
            "slides": [{"path": path, "objects": len(result["objects"])} for path, result in outputs]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    print(json.dumps(export(parser.parse_args().manifest), indent=2))

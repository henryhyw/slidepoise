"""Deterministic weight treatment for generic 24-unit line artwork.

The returned facts describe geometry. The host inspects the derived artwork and
decides whether it suits the slide. This module never selects an icon or variant.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from importlib.metadata import version

from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path
from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

FINE_INSET = 0.35
FLATTENING_TOLERANCE = 0.001
MAX_POINTS = 100_000


class IconGeometryError(ValueError):
    """The source cannot be transformed without an unsupported assumption."""


class _FlattenPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.rings = []
        self.points = []
        self.point_count = 0

    def _append(self, point):
        if not all(math.isfinite(v) for v in point):
            raise IconGeometryError("Icon coordinates must be finite")
        self.point_count += 1
        if self.point_count > MAX_POINTS:
            raise IconGeometryError("Icon exceeds the vector subdivision limit")
        self.points.append(tuple(point))

    def _moveTo(self, point):
        if self.points:
            self._closePath()
        self._append(point)

    def _lineTo(self, point):
        self._append(point)

    def _closePath(self):
        if self.points:
            if self.points[-1] != self.points[0]:
                self._append(self.points[0])
            if len(self.points) >= 4:
                self.rings.append(self.points)
            self.points = []

    def _endPath(self):
        # SVG fills implicitly close open subpaths.
        self._closePath()

    def _curveToOne(self, p1, p2, p3):
        def midpoint(a, b):
            return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

        def distance(point, a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length_squared = dx * dx + dy * dy
            if not length_squared:
                return math.dist(point, a)
            t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length_squared))
            return math.dist(point, (a[0] + t * dx, a[1] + t * dy))

        def subdivide(a, b, c, d, depth=0):
            if max(distance(b, a, d), distance(c, a, d)) <= FLATTENING_TOLERANCE:
                self._append(d)
                return
            if depth >= 20:
                raise IconGeometryError("Icon curve exceeds the subdivision depth limit")
            ab, bc, cd = midpoint(a, b), midpoint(b, c), midpoint(c, d)
            abc, bcd = midpoint(ab, bc), midpoint(bc, cd)
            middle = midpoint(abc, bcd)
            subdivide(a, ab, abc, middle, depth + 1)
            subdivide(middle, bcd, cd, d, depth + 1)

        subdivide(self._getCurrentPoint(), p1, p2, p3)

    def _qCurveToOne(self, control, end):
        start = self._getCurrentPoint()
        self._curveToOne(
            tuple(start[i] + 2 * (control[i] - start[i]) / 3 for i in (0, 1)),
            tuple(end[i] + 2 * (control[i] - end[i]) / 3 for i in (0, 1)),
            end,
        )


def _winding(point, ring):
    result = 0
    x, y = point.x, point.y
    for a, b in zip(ring, ring[1:]):
        cross = (b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1])
        if a[1] <= y < b[1] and cross > 0:
            result += 1
        elif b[1] <= y < a[1] and cross < 0:
            result -= 1
    return result


def _filled_path(data, fill_rule):
    pen = _FlattenPen()
    parse_path(data, pen)
    pen._endPath()
    rings = pen.rings
    cells = polygonize(unary_union([LineString(ring) for ring in rings]))
    visible = []
    for cell in cells:
        point = cell.representative_point()
        winding = sum(_winding(point, ring) for ring in rings)
        filled = abs(winding) % 2 == 1 if fill_rule == "evenodd" else winding != 0
        if filled:
            visible.append(cell)
    return unary_union(visible)


def _geometry(data: bytes):
    root = ET.fromstring(data)
    if root.tag.split("}")[-1] != "svg":
        raise IconGeometryError("Fine requires an SVG source")
    box = [float(v) for v in root.get("viewBox", "").replace(",", " ").split()]
    if box != [0, 0, 24, 24]:
        raise IconGeometryError("Fine requires a 0 0 24 24 source grid")
    geometries = []
    for element in root.iter():
        tag = element.tag.split("}")[-1]
        if tag not in {"svg", "path"}:
            raise IconGeometryError(f"Fine does not support SVG element {tag!r}")
        allowed = {"viewBox", "width", "height", "id", "d", "fill", "fill-rule", "stroke"}
        if set(element.attrib) - allowed or element.get("stroke", "none") != "none":
            raise IconGeometryError("Fine requires plain filled paths without transforms, styles or strokes")
        if tag == "svg":
            continue
        fill = element.get("fill", root.get("fill", "black"))
        if fill == "none":
            continue
        if fill.lower() not in {"currentcolor", "black", "#000", "#000000"}:
            raise IconGeometryError("Fine requires monochrome generic artwork")
        fill_rule = element.get("fill-rule", root.get("fill-rule", "nonzero"))
        if fill_rule not in {"nonzero", "evenodd"}:
            raise IconGeometryError("Unsupported SVG fill rule")
        geometries.append(_filled_path(element.get("d", ""), fill_rule))
    result = unary_union(geometries)
    if result.is_empty or not result.is_valid or result.geom_type not in {"Polygon", "MultiPolygon"}:
        raise IconGeometryError("Icon has no valid filled geometry")
    return result


def _facts(geometry):
    polygons = [geometry] if isinstance(geometry, Polygon) else list(geometry.geoms)
    return {
        "bounds": [round(value, 8) for value in geometry.bounds],
        "ink_area": round(geometry.area, 8),
        "connected_regions": len(polygons),
        "enclosed_holes": sum(len(polygon.interiors) for polygon in polygons),
    }


def _svg(geometry):
    # Normalize ring order, start points and orientation for stable serialization.
    normalized = geometry.normalize()
    polygons = [normalized] if isinstance(normalized, Polygon) else normalized.geoms
    commands = []
    for polygon in polygons:
        for ring in (polygon.exterior, *polygon.interiors):
            commands.append("M" + " ".join(f"{x:.6f},{y:.6f}" for x, y in ring.coords) + "Z")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<path fill="currentColor" fill-rule="evenodd" d="' + " ".join(commands) + '"/></svg>\n'
    ).encode("utf-8")


def _fine_svg(data: bytes, recipe_id: str) -> tuple[bytes, dict]:
    """Apply the reviewed Fine recipe and return derived SVG bytes and facts.

    Call only for generic line icons. Exact artwork and Remix's Logos category
    stay on their original geometry. Errors require an explicit source choice.
    """
    original = _geometry(data)
    derived = original.buffer(-FINE_INSET, join_style="mitre", mitre_limit=2)
    if derived.is_empty or not derived.is_valid:
        raise IconGeometryError("Fine removed all ink or produced invalid geometry")
    left, top, right, bottom = original.bounds
    dl, dt, dr, db = derived.bounds
    factor = max(right - left, bottom - top) / max(dr - dl, db - dt)
    centre = ((dl + dr) / 2, (dt + db) / 2)
    derived = affinity.scale(derived, xfact=factor, yfact=factor, origin=centre)
    derived = affinity.translate(derived, xoff=(left + right) / 2 - centre[0], yoff=(top + bottom) / 2 - centre[1])
    return _svg(derived), {
        "id": recipe_id,
        "line_weight": "fine",
        "inset_source_units": FINE_INSET,
        "flattening_tolerance_source_units": FLATTENING_TOLERANCE,
        "join_style": "mitre",
        "mitre_limit": 2,
        "restore_visible_extent_scale": factor,
        "curve_representation": "bounded_polyline_approximation",
        "source_geometry": _facts(original),
        "derived_geometry": _facts(derived),
        "engines": {name: version(name) for name in ("shapely", "fonttools")},
    }


def fine_remix_svg(data: bytes) -> tuple[bytes, dict]:
    return _fine_svg(data, "remix-fine-v1")


def fine_mdi_svg(data: bytes) -> tuple[bytes, dict]:
    """Prepare Fine MDI outlines on the 24-unit grid."""
    return _fine_svg(data, "mdi-fine-v1")

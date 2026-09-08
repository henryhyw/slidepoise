from slidepoise.reconstruction.conformance import _chart_structure_failures, _structural_boundary_collisions


def test_text_crossing_thin_separator_is_reported():
    objects = [
        {"id": "detail", "kind": "textbox", "bbox_px": [100, 80, 240, 32]},
        {"id": "divider", "kind": "shape", "shape": "rectangle", "structural_boundary": True, "bbox_px": [320, 40, 1, 180]},
    ]

    assert _structural_boundary_collisions(objects) == [
        {
            "text": "detail",
            "separator": "divider",
            "text_bbox_px": [100, 80, 240, 32],
            "separator_bbox_px": [320, 40, 1, 180],
        }
    ]


def test_text_clear_of_thin_separator_passes():
    objects = [
        {"id": "detail", "kind": "textbox", "bbox_px": [100, 80, 200, 32]},
        {"id": "divider", "kind": "shape", "shape": "rectangle", "structural_boundary": True, "bbox_px": [320, 40, 1, 180]},
    ]

    assert _structural_boundary_collisions(objects) == []


def test_intentional_text_rule_composition_can_be_declared():
    objects = [
        {"id": "label", "kind": "textbox", "bbox_px": [100, 80, 240, 32]},
        {"id": "rule", "kind": "shape", "shape": "rectangle", "structural_boundary": True, "bbox_px": [320, 40, 1, 180], "allow_text_crossing": True},
    ]

    assert _structural_boundary_collisions(objects) == []


def test_chart_structure_requires_explicit_orientation_and_matching_data():
    objects = [
        {"id": "implicit", "kind": "chart", "structure": {"categories": ["A"], "series": [{"values": [1]}]}},
        {"id": "uneven", "kind": "chart", "structure": {"type": "column", "categories": ["A", "B"], "series": [{"values": [1]}]}},
    ]

    assert _chart_structure_failures(objects) == [
        {"chart": "implicit", "reason": "chart_type_must_be_explicit", "type": ""},
        {"chart": "uneven", "reason": "chart_series_category_length_mismatch", "series_index": 0, "categories": 2, "values": 1},
    ]


def test_a_decorative_rule_does_not_become_a_boundary_by_shape_alone():
    objects = [
        {"id": "folio", "kind": "textbox", "bbox_px": [90, 868, 300, 38]},
        {"id": "rule", "kind": "shape", "shape": "rectangle", "bbox_px": [357, 883, 101, 1]},
    ]
    assert _structural_boundary_collisions(objects) == []

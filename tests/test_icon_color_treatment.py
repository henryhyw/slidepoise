"""Selected profile colours survive canonical icon reconstruction."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'slidepoise/runtime/src'))
from slidepoise.canvas import reconstruction_geometry
from slidepoise.reconstruction.scene import build_reconstruction_scene

@pytest.mark.parametrize('color_key', ['glyph_color', 'glyph'])
def test_profile_icon_colour_survives_scene_compilation(tmp_path, color_key):
    source = tmp_path / 'search.svg'
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" fill="none" stroke="currentColor"/></svg>')
    design = {'full_slide_px': [1600, 900], 'profile_hard_rules': {'icons': {'proxy_treatments': [{'id': 'sage', color_key: '#526A60'}]}}}
    measured = {'source': {'width_px': 1600, 'height_px': 900}, 'entities': [{
        'id': 'search', 'kind': 'icon', 'z': 1, 'icon_treatment_group': 'workflow', 'icon_treatment': 'sage',
        'style_hint': {'icon_inset_fraction': 0}, 'measurement': {'layout_bbox': {'px': [40, 40, 48, 48]}}}]}
    contract = {**reconstruction_geometry(design, [1600, 900]), 'canonical_asset_mappings': [{
        'entity_id': 'search', 'selected_asset_path': str(source), 'selected_asset_id': 'remix-search-line',
        'treatment_recolorable': True, 'recolor_mode': 'current_color'}]}
    scene = build_reconstruction_scene(measured_scene=measured, contract=contract, design=design, slide_id='icons')
    icon = scene['objects'][0]
    assert icon['recolor'] == '#526A60'
    assert icon['recolor_mode'] == 'current_color'
    assert icon['bbox_px'] == [40, 40, 48, 48]

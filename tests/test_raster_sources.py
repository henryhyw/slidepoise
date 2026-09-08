"""Artwork source contracts from an image edit to measured placement and PPTX media."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'slidepoise/scripts'))
sys.path.insert(0, str(ROOT / 'slidepoise/runtime/scripts'))
from apply_illustration_sources import apply_sources
from extract_refined_illustrations import extract
from raster_sources import image_facts, validate_background, validate_canvas


def fixture(tmp_path):
    # Hidden magenta must not leak into either alpha bounds or the rendered slide.
    image = Image.new('RGBA', (120, 100), (255, 0, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 25, 79, 74), fill=(230, 90, 40, 128))
    draw.rectangle((30, 35, 69, 64), fill=(230, 90, 40, 255))
    path = tmp_path / 'returned.png'
    image.save(path)
    target = tmp_path / 'target.png'
    background = Image.new('RGBA', (300, 200), 'white')
    background.alpha_composite(image, (40, 50))
    background.convert('RGB').save(target)
    manifest = {'source_image_sha256': image_facts(target)['sha256'], 'items': [
        {'entity_id': 'art', 'source_bbox_px': [40, 50, 120, 100], 'source_crop_sha256': 'fixture-crop', 'background': 'transparent'}]}
    semantic = {'entities': [{'id': 'art', 'kind': 'image', 'visual_source_class': 'novel_illustration',
        'bbox_hint': [40, 50, 120, 100], 'geometry_policy': 'agent_logical',
        'raster_decision': {'action': 'refine', 'background': 'transparent',
            'reviewed_by': 'host_agent_visual_reasoning', 'reason': 'Fixture isolates a paper layer.'}}]}
    return path, target, manifest, semantic


def test_registered_asset_preserves_alpha_and_full_canvas(tmp_path):
    path, target, manifest, semantic = fixture(tmp_path)
    original = copy.deepcopy(semantic)
    mapping = extract(path, manifest, 'art', tmp_path / 'assets')
    result, ids = apply_sources(semantic, mapping)
    assert semantic == original
    assert ids == ['art']
    entity = result['entities'][0]
    assert entity['bbox_hint'] == [40, 50, 120, 100]
    assert entity['raster_fit'] == 'fill'
    assert Image.open(entity['raster_source_override']).tobytes() == Image.open(path).tobytes()
    assert entity['raster_source']['alpha'] == {
        'transparent_pixels': 9000, 'partial_pixels': 1800, 'opaque_pixels': 1200,
        'visible_bbox_px': [20, 25, 60, 50]}
    sem_path = tmp_path / 'semantic.json'
    sem_path.write_text(json.dumps(result))
    command = [sys.executable, str(ROOT / 'slidepoise/runtime/scripts/measure_visual_scene.py'), str(target),
               '--semantic-map', str(sem_path), '--config', str(ROOT / 'framework/defaults/slidepoise-config.json'),
               '--output-dir', str(tmp_path / 'measurement')]
    run = subprocess.run(command, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    measured = json.loads((tmp_path / 'measurement/slide_entities.json').read_text())
    measurement = measured['entities'][0]['measurement']
    assert measurement['layout_bbox']['px'] == [40, 50, 120, 100]
    assert measurement['image_object']['raster_source_facts']['alpha']['visible_bbox_px'] == [20, 25, 60, 50]
    Image.new('RGB', (300, 200), 'gray').save(target)
    run = subprocess.run(command, text=True, capture_output=True)
    assert run.returncode != 0 and 'different slide image' in run.stderr


@pytest.mark.parametrize('mode,color', [('RGB', 'gray'), ('RGBA', (30, 40, 50, 255)), ('RGBA', (0, 0, 0, 0))])
def test_invalid_transparency_cannot_replace_an_asset(tmp_path, mode, color):
    path, _, manifest, _ = fixture(tmp_path)
    Image.new(mode, (120, 100), color).save(path)
    output = tmp_path / 'assets'
    output.mkdir()
    existing = output / 'art.png'
    existing.write_bytes(b'previous artwork')
    with pytest.raises(ValueError, match='transparent'):
        extract(path, manifest, 'art', output)
    assert existing.read_bytes() == b'previous artwork'


def test_palette_transparency_is_measured_without_discarding_alpha(tmp_path):
    image = Image.new('P', (8, 8), 0)
    image.putpalette([255, 255, 255, 0, 0, 0] + [0] * 762)
    image.putpixel((4, 4), 1)
    path = tmp_path / 'palette.png'
    image.save(path, transparency=0)
    facts = image_facts(path)
    validate_background(facts, 'transparent')
    assert facts['alpha']['transparent_pixels'] == 63
    assert facts['alpha']['visible_bbox_px'] == [4, 4, 1, 1]


def test_no_automatic_stretch_or_crop_when_model_changes_canvas(tmp_path):
    path, _, manifest, _ = fixture(tmp_path)
    Image.new('RGBA', (200, 200), (255, 0, 0, 128)).save(path)
    # Semi-transparent content alone does not establish a transparent backdrop.
    image = Image.open(path)
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(path)
    with pytest.raises(ValueError, match='aspect ratio'):
        extract(path, manifest, 'art', tmp_path / 'assets')
    validate_canvas([240, 200], [120, 100])
    validate_canvas([241, 200], [120, 100])


def test_changed_source_or_placement_cannot_be_applied(tmp_path):
    path, _, manifest, semantic = fixture(tmp_path)
    mapping = extract(path, manifest, 'art', tmp_path / 'assets')
    changed = copy.deepcopy(semantic)
    changed['entities'][0]['bbox_hint'][0] += 1
    with pytest.raises(ValueError, match='placement changed'):
        apply_sources(changed, mapping)
    Image.new('RGBA', (120, 100), 'red').save(mapping['items'][0]['refined_raster'])
    with pytest.raises(ValueError, match='changed after inspection'):
        apply_sources(semantic, mapping)
    assert 'raster_source_override' not in semantic['entities'][0]


def test_mapping_cannot_overwrite_canonical_assets_or_duplicate_entities(tmp_path):
    path, _, manifest, semantic = fixture(tmp_path)
    mapping = extract(path, manifest, 'art', tmp_path / 'assets')
    canonical = copy.deepcopy(semantic)
    canonical['entities'][0]['visual_source_class'] = 'canonical_asset'
    with pytest.raises(ValueError, match='not selected'):
        apply_sources(canonical, mapping)
    mapping['items'] *= 2
    with pytest.raises(ValueError, match='duplicate'):
        apply_sources(semantic, mapping)
    assert 'raster_source_override' not in semantic['entities'][0]


def test_powerpoint_embeds_alpha_and_rejects_changed_source(tmp_path):
    path, _, manifest, semantic = fixture(tmp_path)
    mapping = extract(path, manifest, 'art', tmp_path / 'assets')
    raster = mapping['items'][0]
    spec = {'slide': {'dimensions_px': [300, 200], 'objects': [
        {'id': 'art', 'kind': 'image', 'bbox_px': [40, 50, 120, 100],
         'source_path': raster['refined_raster'], 'source_sha256': raster['raster_source']['sha256']}]}}
    scene = tmp_path / 'scene.json'
    scene.write_text(json.dumps(spec))
    pptx = tmp_path / 'slide.pptx'
    command = ['node', str(ROOT / 'slidepoise/runtime/js/scene_to_pptx.mjs'), '--input', str(scene), '--output', str(pptx)]
    run = subprocess.run(command, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    with zipfile.ZipFile(pptx) as archive:
        media = [p for p in archive.namelist() if p.startswith('ppt/media/') and p.endswith('.png')]
        images = [Image.open(io.BytesIO(archive.read(p))).convert('RGBA') for p in media]
    assert any(image.tobytes() == Image.open(path).tobytes() for image in images)
    before = hashlib.sha256(pptx.read_bytes()).hexdigest()
    Image.new('RGB', (120, 100), 'red').save(raster['refined_raster'])
    run = subprocess.run(command, text=True, capture_output=True)
    assert run.returncode != 0 and 'changed after scene compilation' in run.stderr
    assert hashlib.sha256(pptx.read_bytes()).hexdigest() == before


def test_review_previews_composite_nearly_invisible_pixels(tmp_path):
    path, _, manifest, _ = fixture(tmp_path)
    image = Image.open(path)
    image.putpixel((4, 4), (255, 255, 255, 1))
    image.save(path)
    record = extract(path, manifest, 'art', tmp_path / 'assets')['items'][0]
    with Image.open(record['review_previews']['dark']) as preview:
        assert preview.mode == 'RGB'
        assert max(abs(a - b) for a, b in zip(preview.getpixel((4, 4)), (32, 38, 48))) <= 1
    with Image.open(record['refined_raster']) as stored:
        assert stored.getpixel((4, 4)) == (255, 255, 255, 1)


def test_registered_canvas_requires_logical_geometry(tmp_path):
    path, _, manifest, semantic = fixture(tmp_path)
    mapping = extract(path, manifest, 'art', tmp_path / 'assets')
    semantic['entities'][0]['geometry_policy'] = 'opencv_visible'
    with pytest.raises(ValueError, match='agent_logical'):
        apply_sources(semantic, mapping)


def test_reuse_original_disables_a_previous_override(tmp_path):
    path, target, manifest, semantic = fixture(tmp_path)
    mapping = extract(path, manifest, 'art', tmp_path / 'assets')
    result, _ = apply_sources(semantic, mapping)
    result['entities'][0]['raster_decision']['action'] = 'reuse_original'
    Path(result['entities'][0]['raster_source_override']).unlink()
    sem_path = tmp_path / 'semantic.json'
    sem_path.write_text(json.dumps(result))
    run = subprocess.run([sys.executable, str(ROOT / 'slidepoise/runtime/scripts/measure_visual_scene.py'), str(target),
        '--semantic-map', str(sem_path), '--config', str(ROOT / 'framework/defaults/slidepoise-config.json'),
        '--output-dir', str(tmp_path / 'measurement')], text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    measured = json.loads((tmp_path / 'measurement/slide_entities.json').read_text())
    assert measured['entities'][0]['measurement']['image_object']['source_kind'] == 'accepted_slide_crop'


def test_relative_asset_survives_moving_the_authoring_directory(tmp_path):
    import shutil
    root = tmp_path / 'original'
    root.mkdir()
    path, target, manifest, semantic = fixture(root)
    mapping = extract(path, manifest, 'art', root / 'artwork')
    sem_path, map_path = root / 'semantic.json', root / 'mapping.json'
    sem_path.write_text(json.dumps(semantic))
    map_path.write_text(json.dumps(mapping))
    run = subprocess.run([sys.executable, str(ROOT / 'slidepoise/scripts/apply_illustration_sources.py'),
        '--semantic-map', str(sem_path), '--mapping', str(map_path), '--output', str(sem_path)], text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    assert not Path(json.loads(sem_path.read_text())['entities'][0]['raster_source_override']).is_absolute()
    moved = tmp_path / 'moved'
    shutil.move(root, moved)
    run = subprocess.run([sys.executable, str(ROOT / 'slidepoise/runtime/scripts/measure_visual_scene.py'), str(moved / 'target.png'),
        '--semantic-map', str(moved / 'semantic.json'), '--config', str(ROOT / 'framework/defaults/slidepoise-config.json'),
        '--output-dir', str(moved / 'measurement')], cwd=tmp_path, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr

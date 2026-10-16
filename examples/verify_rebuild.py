#!/usr/bin/env python3
"""Compare a rebuilt example with recorded native pages in the same renderer.

Pixel equality establishes reproduction of these inputs, never visual acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(reference, rebuilt):
    source = json.loads((rebuilt / 'rebuild.json').read_text())
    pages = []
    bindings = []
    for entry in source['input_files']:
        relative = Path(entry['path']).relative_to('run')
        current = reference / relative
        bindings.append({'path': str(relative), 'sha256': sha(current),
                         'matches_rebuild_input': sha(current) == entry['sha256']})
    before = sorted((reference / 'preview').glob('slide-*.png'))
    after = sorted((rebuilt / 'preview').glob('slide-*.png'))
    if not before or [p.name for p in before] != [p.name for p in after]:
        raise ValueError('Reference and rebuilt previews must contain the same nonempty page set')
    for left, right in zip(before, after):
        with Image.open(left) as a, Image.open(right) as b:
            same = a.size == b.size and ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox() is None
        pages.append({'page': left.name, 'reference_sha256': sha(left),
                      'rebuilt_sha256': sha(right), 'pixels_identical': same})
    return {'evidence_type': 'frozen_input_reproduction',
            'source_pptx_sha256': sha(reference / 'deliverables/presentation.pptx'),
            'rebuilt_pptx_sha256': sha(rebuilt / 'deliverables/presentation.pptx'),
            'frozen_input_bindings': bindings, 'render_comparisons': pages,
            'all_inputs_current': all(b['matches_rebuild_input'] for b in bindings),
            'all_pages_pixel_identical': all(p['pixels_identical'] for p in pages),
            'scope': 'Frozen reconstruction inputs in the recorded renderer, fonts and DPI. Image generation and visual acceptance remain Agent decisions.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--rebuilt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.reference_run, args.rebuilt)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('all_inputs_current', 'all_pages_pixel_identical')}))
    raise SystemExit(0 if result['all_inputs_current'] and result['all_pages_pixel_identical'] else 1)

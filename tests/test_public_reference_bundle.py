"""Published references remain portable, traceable and separate from private libraries."""
import hashlib
import json
from pathlib import Path

from slidepoise.reference_retrieval import retrieve

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'profiles/pwc-public'
CATALOG = PROFILE / 'libraries/visual_references/catalog.json'


def test_bundled_references_have_public_provenance_and_portable_verified_sources():
    items = json.loads(CATALOG.read_text())['items']
    assert len(items) >= 35
    for entry in items.values():
        assert entry['provenance']['source_type'] == 'published_document'
        assert entry['provenance']['generated_reference'] is False
        assert entry['source_url'].startswith('https://www.pwc.')
        assert entry['source_page'] > 0
        assert entry['visibility'] == 'public_reference'
        image = (CATALOG.parent / entry['path']).resolve()
        pdf = (CATALOG.parent / entry['source_document_path']).resolve()
        assert image.is_relative_to(PROFILE.resolve())
        assert pdf.is_relative_to(PROFILE.resolve())
        assert hashlib.sha256(image.read_bytes()).hexdigest() == entry['image_sha256']
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == entry['source_pdf_sha256']
    metadata = CATALOG.read_text()
    assert '/Users/' not in metadata
    assert 'user_private_document' not in metadata
    assert 'codex-clipboard' not in metadata


def test_complete_primary_deck_and_default_retrieval_respect_editorial_eligibility(tmp_path):
    items = json.loads(CATALOG.read_text())['items']
    primary = [e for e in items.values() if e['source_filename'] == 'strategyand-b2b-saas-2024.pdf']
    assert sorted(e['source_page'] for e in primary) == list(range(1, 31))
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'resolved_profile': {'profile_id': 'pwc-public'},
                                 'libraries': {'visual_references': {'catalog': str(CATALOG)}}}))
    intent = tmp_path / 'intent.json'
    intent.write_text(json.dumps({'communication_job': 'explain staged roadmap',
                                 'information_structure': {'type': 'roadmap'},
                                 'semantic_relationships': ['sequence', 'stages']}))
    result = retrieve(config, intent, tmp_path / 'candidates.json', tmp_path / 'candidates.png')
    assert result['candidates']
    assert all(e['metadata'].get('retrieval_eligible') is not False for e in result['candidates'])
    assert any(e['metadata']['source_page'] == 26 and e['metadata']['source_filename'] == 'strategyand-b2b-saas-2024.pdf'
               for e in result['candidates'])
    assert 'selected_visual_references' not in result

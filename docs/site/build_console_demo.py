"""Package the real Console UI with isolated, in-memory sample data."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent / 'console-demo'
BASE = 'http://127.0.0.1:8766'


def get(path):
    with urllib.request.urlopen(BASE + path) as response:
        return json.load(response)


def main():
    DEST.mkdir(exist_ok=True)
    overview = get('/api/overview')
    data = {'overview': overview, 'profiles': {}, 'designs': {}, 'references': {}, 'sets': {},
            'libraries': get('/api/library-sets'), 'health': get('/api/health'), 'settings': get('/api/settings')}
    for profile in overview['profiles']:
        key = profile['id']
        data['profiles'][key] = get('/api/profile?profile=' + quote(key))
        data['designs'][key] = get('/api/design?profile=' + quote(key))
        data['references'][key] = get('/api/library?kind=visual_references&profile=' + quote(key))
    for item in data['libraries']['sets']:
        data['sets'][item['id']] = get('/api/library-set?set_id=' + quote(item['id']))
    def clean(value):
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if key not in {'framework_home', 'skill_path', 'root', 'source_path', 'catalog_path'}}
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, str):
            if value.startswith('/api/library-file') or value.startswith('/api/library-set-file'):
                with urllib.request.urlopen(BASE + value) as response:
                    content = response.read()
                    extension = '.svg' if 'svg' in response.headers.get('Content-Type', '') else '.png'
                name = 'asset-' + hashlib.sha256(content).hexdigest()[:16] + extension
                (DEST/name).write_bytes(content)
                return name
            if value.startswith(('/Users/', '/private/', '/opt/')):
                return 'Sample installation'
        return value
    data = clean(data)
    for item in data['health']:
        item['available'] = True
        item['detail'] = 'Illustrative installation. This demo does not inspect your computer.'
    if not any(item['name'] == 'Poppler' for item in data['health']):
        data['health'].append({'name': 'Poppler', 'available': True, 'detail': 'Illustrative installation.'})
    (DEST/'fixtures.js').write_text('window.consoleFixtures = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    for name in ['styles.css', 'mark.svg', 'authoring.js', 'components.js']:
        shutil.copy2(ROOT/'webapp/console'/name, DEST/name)
    shutil.copy2(ROOT/'webapp/ui/dialog-dismiss.js', DEST/'dialog-dismiss.js')
    app = (ROOT/'webapp/console/app.js').read_text()
    begin = app.index('async function api(path, body) {')
    end = app.index('\nlet toastTimer;', begin)
    app = app[:begin] + 'async function api(path, body) { return window.consoleDemoAPI(path, body); }\n' + app[end:]
    app = app.replace('On this computer', 'Demo data').replace('Tools installed on this computer.', 'Sample tool status. Your computer is not inspected.')
    (DEST/'app.js').write_text(app)
    html = (ROOT/'webapp/console/index.html').read_text().replace('/console/', '').replace('/dialog-dismiss.js', 'dialog-dismiss.js')
    html = html.replace('<head>', '<head>\n<meta http-equiv="Content-Security-Policy" content="default-src \'self\' data:; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: blob:; connect-src \'none\'; form-action \'none\'; object-src \'none\'; base-uri \'none\'">')
    html = html.replace('<script src="app.js">', '<script src="fixtures.js"></script><script src="adapter.js"></script><script src="app.js">')
    html = html.replace('<div class="sidebar-footer"><span class="status-dot"></span><div><strong>On this computer</strong></div></div>', '')
    html = html.replace('</div></header>', '</div><span class="demo-badge">Demo</span></header>', 1)
    html = html.replace('On this computer', 'Interactive demo').replace('<title>SlidePoise Console</title>', '<title>SlidePoise Console demo</title>')
    html = html.replace('</head>', '<link rel="stylesheet" href="demo.css"></head>')
    (DEST/'index.html').write_text(html)
    print(json.dumps({'files': len(list(DEST.iterdir())), 'profiles': len(data['profiles']), 'sets': len(data['sets'])}))

if __name__ == '__main__':
    main()

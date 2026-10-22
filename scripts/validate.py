#!/usr/bin/env python3
"""Validate published data offline; never modify files or infer medical claims."""
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.datetime.now(dt.timezone.utc).date()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def date(value, label, nullable=False):
    if nullable and value is None:
        return
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), f'{label}: expected YYYY-MM-DD')
    require(dt.date.fromisoformat(value) <= TODAY, f'{label}: future date')

def nct(value):
    require(isinstance(value, str) and re.fullmatch(r'NCT\d{8}', value), f'invalid NCT: {value}')

def https(value):
    u = urlparse(value)
    require(u.scheme == 'https' and bool(u.netloc), f'Expected HTTPS source: {value}')

def main():
    for name in ['index.html', 'styles.css', 'app.js', '.nojekyll', 'README.md']:
        require((ROOT / name).is_file(), f'missing {name}')
    updates = json.loads((ROOT / 'data/updates.json').read_text())
    registry = json.loads((ROOT / 'data/trials.json').read_text())
    changes = json.loads((ROOT / 'data/changelog.json').read_text())
    require(updates['schemaVersion'] == registry['schemaVersion'] == changes['schemaVersion'] == 1, 'schema version')
    date(updates['lastUpdated'], 'lastUpdated')
    require(bool(updates.get('coverage')), 'coverage required')
    seen = set()
    require(len(updates['items']) > 0, 'no curated records')
    for x in updates['items']:
        for field in ['id','drug','category','phase','regulatoryStatus','findings','evidenceType','checkedAt','caveat']:
            require(isinstance(x.get(field), str) and x[field].strip(), f'missing {field}: {x.get("id")}')
        require(x['id'] not in seen, f'duplicate item {x["id"]}')
        seen.add(x['id'])
        require(x['category'] in ['pipeline','regulatory'], 'invalid category')
        date(x['checkedAt'], x['id'] + ' checkedAt')
        require(x['checkedAt'] <= updates['lastUpdated'], 'checkedAt later than lastUpdated')
        date(x['sourceDate'], x['id'] + ' sourceDate', nullable=True)
        require(isinstance(x['nctIds'], list), 'nctIds must be list')
        for v in x['nctIds']:
            nct(v)
        require(len(x['sources']) > 0, 'missing sources')
        for s in x['sources']:
            require(bool(s['title']), 'source title required')
            https(s['url'])
    retrieved = dt.datetime.fromisoformat(registry['retrievedAt'].replace('Z','+00:00'))
    require(retrieved.tzinfo is not None, 'retrievedAt requires timezone')
    require(retrieved <= dt.datetime.now(dt.timezone.utc), 'future registry read time')
    require(bool(registry['scope']), 'registry scope required')
    seen = set()
    require(len(registry['trials']) > 0, 'no trials')
    for x in registry['trials']:
        nct(x['nctId'])
        require(x['nctId'] not in seen, 'duplicate trial')
        seen.add(x['nctId'])
        require(bool(x['title']) and bool(x['status']), 'missing trial title/status')
        require(x['studyType'] == 'INTERVENTIONAL', 'noninterventional entry')
        require(isinstance(x['phase'], list) and isinstance(x['interventions'], list) and bool(x['interventions']), 'trial arrays')
        require(isinstance(x['hasResults'], bool), 'hasResults must be boolean')
        date(x['lastUpdatePosted'], x['nctId'] + ' lastUpdatePosted')
        https(x['sourceUrl'])
        require(x['sourceUrl'] == 'https://clinicaltrials.gov/study/' + x['nctId'], 'trial source mismatch')
    require(bool(changes['entries']), 'changelog empty')
    for change in changes['entries']:
        date(change['date'], 'changelog date')
        require(bool(change['summary']), 'changelog summary empty')
    print(f'OK: {len(updates["items"])} curated records; {len(registry["trials"])} registered trials; {len(changes["entries"])} update entries.')

if __name__ == '__main__':
    main()

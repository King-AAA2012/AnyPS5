import json

with open('raw_issues.json', encoding='utf-16') as f:
    data = json.load(f)

rows = []
for i in data:
    comments = i.get('comments') or []
    labels = i.get('labels') or []
    rows.append({
        'number': i['number'],
        'title': i['title'],
        'comments': len(comments),
        'comment_bodies': [c.get('body', '') for c in comments if isinstance(c, dict)],
        'author': (i.get('author') or {}).get('login', ''),
        'labels': [l.get('name', '') for l in labels],
        'url': f'https://github.com/boykopovar/AnyPS5/issues/{i["number"]}',
        'body': i.get('body', ''),
    })

with open('candidates.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print('wrote', len(rows), 'issues to candidates.json')

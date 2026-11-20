import json

with open('candidates.json', encoding='utf-8') as f:
    rows = json.load(f)

# Sort by number descending (most recent first)
rows.sort(key=lambda r: r['number'], reverse=True)

with open('tasks.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print('wrote', len(rows), 'task records to tasks.json')

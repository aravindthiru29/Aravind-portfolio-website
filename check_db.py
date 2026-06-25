import sqlite3, json

db = sqlite3.connect('db.sqlite3')
db.row_factory = sqlite3.Row
rows = db.execute('SELECT section_key, content FROM portfolio_content').fetchall()
for r in rows:
    key = r['section_key']
    data = json.loads(r['content'])
    if key in ('mini_projects', 'projects', 'blog_posts', 'hero'):
        print(f'=== {key} ===')
        if isinstance(data, list):
            for i, item in enumerate(data):
                img = item.get('image', 'N/A')
                print(f'  [{i}] title: {item.get("title","")}  image: {img}')
                for g in item.get('gallery_images', []):
                    print(f'       gallery: {g}')
        else:
            print('  image:', data.get('image', 'N/A'))
db.close()

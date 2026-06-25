"""
update_images.py — Run locally to update image paths in db.sqlite3.
Usage: python update_images.py

After running, commit the updated db.sqlite3 and redeploy to Vercel.
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

# ─── Set your Cloudinary URLs here ───────────────────────────────────────
# Copy the FULL https://res.cloudinary.com/... URL from your Cloudinary dashboard
# Leave empty '' to keep the current value unchanged

CLOUDINARY_IMAGES = {
    'mini_projects': [
        # Index 0: ARTS OF CHEMISTRY
        '',   # e.g. 'https://res.cloudinary.com/dyyihitaz/image/upload/v.../game1.png'
        # Index 1: MATHS QUEST
        '',
        # Index 2: SCIENCE GAME
        '',
        # Index 3: BRAIN GAME
        '',
    ],
    'projects': [
        # Index 0: FLIPBOOK WEB APP
        '',
        # Index 1: STUDENT SCORE ANALYSIS
        '',
        # Index 2: YOLOV8 OBJECT DETECTION
        '',
    ],
    'hero_image': '',   # Hero section profile image Cloudinary URL
}

# ─── Apply fallback placeholder for broken local paths ───────────────────
# img/gallery/img-6.png is the only remaining gallery image
FALLBACK = 'img/gallery/img-6.png'

BROKEN_PATHS = {
    'img/gallery/game-1.png': FALLBACK,
    'img/gallery/game-2.png': FALLBACK,
    'img/gallery/game-3.png': FALLBACK,
    'img/gallery/game-4.png': FALLBACK,
    'img/gallery/img-4.png':  FALLBACK,
    'img/gallery/img-9.png':  FALLBACK,
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def get(key):
    row = conn.execute('SELECT content FROM portfolio_content WHERE section_key = ?', (key,)).fetchone()
    return json.loads(row['content']) if row else None

def save(key, data):
    json_data = json.dumps(data, ensure_ascii=False)
    conn.execute('''
        INSERT INTO portfolio_content (section_key, content, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(section_key) DO UPDATE SET content = EXCLUDED.content, updated_at = CURRENT_TIMESTAMP
    ''', (key, json_data))
    conn.commit()
    print(f'  ✓ saved {key}')

print('\n=== Updating mini_projects ===')
items = get('mini_projects') or []
for i, item in enumerate(items):
    cloud_url = CLOUDINARY_IMAGES['mini_projects'][i] if i < len(CLOUDINARY_IMAGES['mini_projects']) else ''
    if cloud_url:
        items[i]['image'] = cloud_url
        print(f'  [{i}] {item["title"]}: set to Cloudinary URL')
    elif item.get('image', '') in BROKEN_PATHS:
        items[i]['image'] = BROKEN_PATHS[item['image']]
        print(f'  [{i}] {item["title"]}: fixed broken path -> {FALLBACK}')
    else:
        print(f'  [{i}] {item["title"]}: unchanged ({item.get("image", "")})')
save('mini_projects', items)

print('\n=== Updating projects ===')
projs = get('projects') or []
for i, proj in enumerate(projs):
    cloud_url = CLOUDINARY_IMAGES['projects'][i] if i < len(CLOUDINARY_IMAGES['projects']) else ''
    if cloud_url:
        projs[i]['image'] = cloud_url
        print(f'  [{i}] {proj["title"]}: set to Cloudinary URL')
    elif proj.get('image', '') in BROKEN_PATHS:
        projs[i]['image'] = BROKEN_PATHS[proj['image']]
        print(f'  [{i}] {proj["title"]}: fixed broken path → {FALLBACK}')
    else:
        print(f'  [{i}] {proj["title"]}: unchanged ({proj.get("image", "")})')
save('projects', projs)

print('\n=== Updating hero ===')
hero = get('hero') or {}
cloud_url = CLOUDINARY_IMAGES['hero_image']
if cloud_url:
    hero['image'] = cloud_url
    print(f'  hero image: set to Cloudinary URL')
else:
    print(f'  hero image: unchanged ({hero.get("image", "")})')
save('hero', hero)

conn.close()
print('\n✅ Done! Now commit db.sqlite3 and push to GitHub to deploy.\n')

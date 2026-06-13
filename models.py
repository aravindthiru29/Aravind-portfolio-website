"""
models.py — Portfolio Content Database Models
Uses SQLite to store all portfolio content as structured JSON,
plus admin user authentication with hashed passwords.
"""
import sqlite3
import json
import hashlib
import secrets
import os
import shutil

DB_FILENAME = 'db.sqlite3'
LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)

if os.environ.get('VERCEL') == '1':
    # On Vercel, the root is read-only. We must copy the bundled DB to /tmp to read/write.
    DB_PATH = os.path.join('/tmp', DB_FILENAME)
    if not os.path.exists(DB_PATH) and os.path.exists(LOCAL_DB_PATH):
        shutil.copy2(LOCAL_DB_PATH, DB_PATH)
else:
    DB_PATH = LOCAL_DB_PATH


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database tables and seed default data."""
    conn = get_db()
    cursor = conn.cursor()

    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Portfolio content table — stores each section as a JSON blob
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_key TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Seed default admin if none exists
    existing = cursor.execute('SELECT id FROM admin_users LIMIT 1').fetchone()
    if not existing:
        admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin@1234')
        create_admin(admin_user, admin_pass)

    # Seed default content if none exists
    existing_content = cursor.execute('SELECT id FROM portfolio_content LIMIT 1').fetchone()
    if not existing_content:
        seed_default_content()

    conn.close()


def hash_password(password, salt=None):
    """Hash a password with a salt using SHA-256."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt


def create_admin(username, password):
    """Create a new admin user."""
    conn = get_db()
    hashed, salt = hash_password(password)
    try:
        conn.execute(
            'INSERT INTO admin_users (username, password_hash, salt) VALUES (?, ?, ?)',
            (username, hashed, salt)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_admin(username, password):
    """Verify admin credentials. Returns True/False."""
    conn = get_db()
    user = conn.execute(
        'SELECT password_hash, salt FROM admin_users WHERE username = ?',
        (username,)
    ).fetchone()
    conn.close()
    if not user:
        return False
    hashed, _ = hash_password(password, user['salt'])
    return hashed == user['password_hash']


def change_admin_password(username, new_password):
    """Change admin password."""
    conn = get_db()
    hashed, salt = hash_password(new_password)
    conn.execute(
        'UPDATE admin_users SET password_hash = ?, salt = ? WHERE username = ?',
        (hashed, salt, username)
    )
    conn.commit()
    conn.close()


# ─── Content CRUD ───

def get_content(section_key):
    """Get content for a section as a Python dict/list."""
    conn = get_db()
    row = conn.execute(
        'SELECT content FROM portfolio_content WHERE section_key = ?',
        (section_key,)
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row['content'])
    return None


def set_content(section_key, data):
    """Set content for a section (upsert)."""
    conn = get_db()
    json_data = json.dumps(data, ensure_ascii=False)
    conn.execute('''
        INSERT INTO portfolio_content (section_key, content, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(section_key) DO UPDATE SET content = ?, updated_at = CURRENT_TIMESTAMP
    ''', (section_key, json_data, json_data))
    conn.commit()
    conn.close()


def get_all_content():
    """Get all content sections as a dictionary."""
    conn = get_db()
    rows = conn.execute('SELECT section_key, content FROM portfolio_content').fetchall()
    conn.close()
    return {row['section_key']: json.loads(row['content']) for row in rows}


# ─── Default Content Seed ───────────────────────────────────────

def seed_default_content():
    """Seed the database with current portfolio content."""

    # Hero section
    set_content('hero', {
        'badge': 'FINAL YEAR STUDENT',
        'title_line1': 'ENGINEERING THE',
        'title_highlight': 'FUTURE',
        'title_line2': 'WITH AI',
        'description': 'I am an Artificial Intelligence and Data Science student focusing on building a solid foundation in data-driven decision-making and computational techniques.',
        'cta_primary': 'BOOK A CALL',
        'cta_secondary': 'VIEW WORK',
        'image': 'img/hero/author-thumb-2.jpg'
    })

    # About section (on homepage)
    set_content('about_brief', {
        'title': 'ABOUT ME.',
        'subtitle': "Hello, I'm Aravind. I focus on building a solid foundation in data-driven decision-making, logical reasoning, and computational techniques.",
        'description': 'Currently pursuing B.Tech in AI & Data Science. I bridge the gap between complex algorithms and real-world applications.',
        'cta_text': 'READ MORE'
    })

    # About page full
    set_content('about_full', {
        'page_title_1': 'MY',
        'page_title_2': 'JOURNEY.',
        'subtitle': 'AI ENGINEER • DEVELOPER • DATA SCIENTIST',
        'years_exp': '01+ YEARS',
        'years_label': 'OF PRACTICAL EXPERIENCE',
        'section_title': 'DRIVEN BY INNOVATION',
        'section_subtitle': 'I bridge the gap between complex data algorithms and user-centric applications.',
        'paragraphs': [
            'My journey in Artificial Intelligence and Data Science started with a simple question: How can we make data work for us? This curiosity led me to pursue my B.Tech, where I delve deep into machine learning, neural networks, and computational logic.',
            "During my time at Adhi College of Engineering, I've focused on not just the theory, but the practical application of AI. Whether it's building object detection systems with YOLOv8 or creating intuitive web interfaces, I strive for excellence in every line of code.",
            'My internship at Book Buddy Library & Organization was a turning point, where I learned the critical importance of data organization and systematic workflows in a professional environment. It taught me that behind every great AI model is a foundation of well-structured data.'
        ],
        'vision': 'To engineer AI solutions that simplify complex real-world challenges and empower decision-makers.',
        'mission': 'Leveraging cutting-edge technology and clean code to build scalable, data-driven applications.',
        'quote': '"THE BEST WAY TO PREDICT THE FUTURE IS TO CREATE IT."',
        'quote_author': '— PETER DRUCKER'
    })

    # Education
    set_content('education', [
        {
            'period': '2023 - 2027',
            'type': 'BACHELORS',
            'title': 'B.TECH AI & DATA SCIENCE',
            'institution': 'Adhi College of Engineering and Technology',
            'description': 'Core focus on Machine Learning, Big Data Analytics, Deep Learning, and Algorithm Design. Maintaining a strong academic record while building practical projects.'
        },
        {
            'period': '2022 - 2023',
            'type': 'SCHOOLING',
            'title': 'HSC BIO-MATHS',
            'institution': 'Government Boys HSS, Odugathur',
            'description': 'Focused on Physics, Chemistry, Biology, and Advanced Mathematics, providing a strong scientific foundation for engineering.'
        }
    ])

    # Experience
    set_content('experience', [
        {
            'period': '2026 - PRESENT',
            'type': 'INTERNSHIP',
            'title': 'FULL STACK INTERN',
            'company': 'Book Buddy Library & Organization',
            'description': 'Specialized in managing operational workflows and handling structured data systems. Focused on accuracy and process-oriented development.'
        }
    ])

    # Skills / Toolkit
    set_content('skills', [
        {'name': 'PYTHON', 'icon': 'fab fa-python'},
        {'name': 'FLASK', 'icon': 'fas fa-leaf'},
        {'name': 'JAVA', 'icon': 'fab fa-java'},
        {'name': 'GIT', 'icon': 'fab fa-git-alt'},
        {'name': 'GITHUB', 'icon': 'fab fa-github'},
        {'name': 'LEETCODE', 'icon': 'fas fa-terminal'},
        {'name': 'SQL', 'icon': 'fas fa-database'},
        {'name': 'HTML5', 'icon': 'fab fa-html5'},
        {'name': 'CSS3', 'icon': 'fab fa-css3-alt'}
    ])

    # Projects (main)
    set_content('projects', [
        {
            'title': 'FLIPBOOK WEB APP',
            'category': 'WEB APP',
            'description': 'It converts your boring PDF into an amazing real book experience with smooth pageturn animations.',
            'image': 'img/gallery/img-6.png',
            'link': '/project-details.html',
            'homepage_desc': 'CONVERT PDF TO REAL BOOK EXPERIENCE'
        },
        {
            'title': 'STUDENT SCORE ANALYSIS',
            'category': 'DATA SCIENCE',
            'description': 'Comprehensive analysis of student performance using Python and data visualization libraries.',
            'image': 'img/gallery/img-4.png',
            'link': '/project-details.html',
            'homepage_desc': 'DATA-DRIVEN REPORTS'
        },
        {
            'title': 'YOLOV8 OBJECT DETECTION',
            'category': 'AI / ML',
            'description': 'Real-time object detection and classification using the state-of-the-art YOLOv8 architecture.',
            'image': 'img/gallery/img-9.png',
            'link': '/project-details.html',
            'homepage_desc': 'COMPUTER VISION APPLICATION'
        }
    ])

    # Mini projects
    set_content('mini_projects', [
        {
            'title': 'ARTS OF CHEMISTRY',
            'category': 'AI GAME',
            'image': 'img/gallery/game-1.png',
            'link': 'https://arts-of-chemistry.vercel.app'
        },
        {
            'title': 'MATHS QUEST',
            'category': 'AI GAME',
            'image': 'img/gallery/game-2.png',
            'link': 'https://maths-quest.vercel.app'
        },
        {
            'title': 'SCIENCE GAME',
            'category': 'AI GAME',
            'image': 'img/gallery/game-3.png',
            'link': 'https://science-game-theta.vercel.app'
        },
        {
            'title': 'BRAIN GAME',
            'category': 'AI GAME',
            'image': 'img/gallery/game-4.png',
            'link': 'https://brain-game-sable.vercel.app'
        }
    ])

    # Stats
    set_content('stats', {
        'projects_count': '08+',
        'projects_label': 'COMPLETED PROJECTS',
        'experience_count': '01+',
        'experience_label': 'YEARS EXPERIENCE',
        'dedication_count': '100%',
        'dedication_label': 'DEDICATION'
    })

    # Contact info
    set_content('contact', {
        'location': 'Odugathur, Vellore, Tamil Nadu',
        'phone': '+91 86102 67200',
        'email': 'aravthiru131@example.com'
    })

    # Social links
    set_content('social_links', {
        'github': 'https://github.com/aravindthiru29',
        'linkedin': 'https://www.linkedin.com/in/aravind-t-b724012b4/',
        'leetcode': 'https://leetcode.com/u/aravindthiru/',
        'instagram': 'https://www.instagram.com/arav45_'
    })

    # Blog posts
    set_content('blog_posts', [
        {
            'title': 'THE FUTURE OF GENERATIVE AI IN 2026',
            'category': 'AI ENGINEERING',
            'date': 'APRIL 20, 2026',
            'excerpt': 'Exploring how transformer models are evolving to handle multimodal data more efficiently than ever before...',
            'image': 'img/gallery/img-6.png',
            'link': '/blog-details.html'
        },
        {
            'title': 'SCALABLE ARCHITECTURES FOR PERSONAL PROJECTS',
            'category': 'DEVELOPMENT',
            'date': 'MARCH 15, 2026',
            'excerpt': 'Why choosing the right foundation is critical for long-term maintainability of your portfolio...',
            'image': 'img/gallery/img-6.png',
            'link': '/blog-details.html'
        }
    ])

    # CTA section
    set_content('cta', {
        'title': 'WANT TO START A PROJECT?',
        'button_text': 'GET IN TOUCH'
    })

    # SEO / Site metadata
    set_content('site_meta', {
        'site_name': 'ARAVIND.T',
        'copyright': '© 2026 ARAVIND. ALL RIGHTS RESERVED.',
        'footer_title': "LET'S CONNECT"
    })

import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
from functools import wraps
from werkzeug.utils import secure_filename
import os
import uuid

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-for-portfolio')

# File upload config
if os.environ.get('VERCEL') == '1':
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img', 'uploads')

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    pass # On Vercel, this might fail if we try to write to a protected path

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB max

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Robust Mail Configuration
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# Configuration for Flask-Mail
app.config.update(
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_USE_TLS=MAIL_USE_TLS,
    MAIL_USE_SSL=MAIL_USE_SSL,
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER=MAIL_USERNAME
)
mail = Mail(app)

# Diagnostic Logging (Safe for Production)
print(f"--- MAIL INITIALIZED ---")
print(f"Server: {MAIL_SERVER}:{MAIL_PORT}")
print(f"Security: TLS={MAIL_USE_TLS}, SSL={MAIL_USE_SSL}")
print(f"User Set: {'Yes' if MAIL_USERNAME else 'No'}")
print(f"Pass Set: {'Yes' if MAIL_PASSWORD else 'No'}")
print(f"------------------------")

# ─── Initialize Database ───────────────────────────────────
from models import init_db, verify_admin, change_admin_password as db_change_password, change_admin_username as db_change_username
from models import get_all_content, get_content, set_content

init_db()
print("--- DATABASE INITIALIZED ---")


# ─── Auth Decorator ────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ─── Public Routes ─────────────────────────────────────────
@app.route('/')
def index():
    content = get_all_content()
    return render_template('index.html', c=content)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        # Create and send the email
        receiver = os.environ.get('MAIL_RECEIVER') or MAIL_USERNAME
        if not MAIL_USERNAME or not MAIL_PASSWORD:
            print("CRITICAL: Mail credentials missing!")
            flash('ERROR! CONFIGURATION ISSUE. PLEASE TRY AGAIN LATER.', 'danger')
            return redirect(url_for('contact'))
        msg = Message(
            subject=f"Portfolio Contact: {subject}",
            recipients=[receiver],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            sender=MAIL_USERNAME
        )
        try:
            mail.send(msg)
            print(f"Mail sent successfully to {receiver}")
            flash('SUCCESS! YOUR MESSAGE HAS BEEN SENT.', 'success')
        except Exception as e:
            print(f"MAIL ERROR: {str(e)}")
            flash('ERROR! UNABLE TO SEND MESSAGE AT THIS TIME.', 'danger')  
        return redirect(url_for('contact'))
    content = get_all_content()
    return render_template('contact.html', c=content)


# ─── Admin Routes ──────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if verify_admin(username, password):
            session['admin_logged_in'] = True
            session['admin_user'] = username
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    content = get_all_content()
    return render_template('admin_dashboard.html', content=content)

@app.route('/admin/save/<section>', methods=['POST'])
@admin_required
def admin_save(section):
    form = request.form

    if section == 'hero':
        set_content('hero', {
            'badge': form.get('badge', ''),
            'title_line1': form.get('title_line1', ''),
            'title_highlight': form.get('title_highlight', ''),
            'title_line2': form.get('title_line2', ''),
            'description': form.get('description', ''),
            'cta_primary': form.get('cta_primary', ''),
            'cta_secondary': form.get('cta_secondary', 'VIEW WORK'),
            'image': form.get('image', '')
        })

    elif section == 'about_brief':
        set_content('about_brief', {
            'title': form.get('title', ''),
            'subtitle': form.get('subtitle', ''),
            'description': form.get('description', ''),
            'cta_text': form.get('cta_text', '')
        })

    elif section == 'about_full':
        paragraphs = form.getlist('paragraphs')
        set_content('about_full', {
            'page_title_1': 'MY',
            'page_title_2': 'JOURNEY.',
            'subtitle': form.get('subtitle', ''),
            'years_exp': form.get('years_exp', ''),
            'years_label': form.get('years_label', ''),
            'section_title': form.get('section_title', ''),
            'section_subtitle': form.get('section_subtitle', ''),
            'paragraphs': paragraphs,
            'vision': form.get('vision', ''),
            'mission': form.get('mission', ''),
            'quote': form.get('quote', ''),
            'quote_author': form.get('quote_author', '')
        })

    elif section == 'education':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            items.append({
                'period': form.get(f'period_{i}', ''),
                'type': form.get(f'type_{i}', ''),
                'title': form.get(f'title_{i}', ''),
                'institution': form.get(f'institution_{i}', ''),
                'description': form.get(f'description_{i}', '')
            })
        set_content('education', items)

    elif section == 'experience':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            items.append({
                'period': form.get(f'period_{i}', ''),
                'type': form.get(f'type_{i}', ''),
                'title': form.get(f'title_{i}', ''),
                'company': form.get(f'company_{i}', ''),
                'description': form.get(f'description_{i}', '')
            })
        set_content('experience', items)

    elif section == 'skills':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            items.append({
                'name': form.get(f'name_{i}', ''),
                'icon': form.get(f'icon_{i}', '')
            })
        set_content('skills', items)

    elif section == 'projects':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            # Collect gallery images (up to 4)
            gallery = []
            for g in range(4):
                img = form.get(f'gallery_{i}_{g}', '').strip()
                if img:
                    gallery.append(img)
            items.append({
                'title': form.get(f'title_{i}', ''),
                'category': form.get(f'category_{i}', ''),
                'description': form.get(f'description_{i}', ''),
                'image': form.get(f'image_{i}', ''),
                'link': form.get(f'link_{i}', ''),
                'homepage_desc': form.get(f'homepage_desc_{i}', ''),
                'github_link': form.get(f'github_link_{i}', ''),
                'website_link': form.get(f'website_link_{i}', ''),
                'tech_stack': form.get(f'tech_stack_{i}', ''),
                'date': form.get(f'date_{i}', ''),
                'client': form.get(f'client_{i}', ''),
                'overview': form.get(f'overview_{i}', ''),
                'challenge': form.get(f'challenge_{i}', ''),
                'solution': form.get(f'solution_{i}', ''),
                'gallery_images': gallery
            })
        set_content('projects', items)

    elif section == 'mini_projects':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            items.append({
                'title': form.get(f'title_{i}', ''),
                'category': form.get(f'category_{i}', ''),
                'image': form.get(f'image_{i}', ''),
                'link': form.get(f'link_{i}', '')
            })
        set_content('mini_projects', items)

    elif section == 'blog_posts':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            items.append({
                'title': form.get(f'title_{i}', ''),
                'category': form.get(f'category_{i}', ''),
                'date': form.get(f'date_{i}', ''),
                'excerpt': form.get(f'excerpt_{i}', ''),
                'body': form.get(f'body_{i}', ''),
                'image': form.get(f'image_{i}', ''),
                'image2': form.get(f'image2_{i}', ''),
                'link': f'/blog/{i}'
            })
        set_content('blog_posts', items)

    elif section == 'certifications':
        count = int(form.get('count', 0))
        items = []
        for i in range(count):
            items.append({
                'title': form.get(f'title_{i}', ''),
                'image': form.get(f'image_{i}', ''),
                'link': form.get(f'link_{i}', '')
            })
        set_content('certifications', items)

    elif section == 'contact':
        set_content('contact', {
            'location': form.get('location', ''),
            'phone': form.get('phone', ''),
            'email': form.get('email', '')
        })

    elif section == 'social_links':
        set_content('social_links', {
            'github': form.get('github', ''),
            'linkedin': form.get('linkedin', ''),
            'leetcode': form.get('leetcode', ''),
            'instagram': form.get('instagram', '')
        })

    elif section == 'stats':
        set_content('stats', {
            'projects_count': form.get('projects_count', ''),
            'projects_label': form.get('projects_label', ''),
            'experience_count': form.get('experience_count', ''),
            'experience_label': form.get('experience_label', ''),
            'dedication_count': form.get('dedication_count', ''),
            'dedication_label': form.get('dedication_label', '')
        })

    elif section == 'site_meta':
        set_content('site_meta', {
            'site_name': form.get('site_name', ''),
            'copyright': form.get('copyright', ''),
            'footer_title': form.get('footer_title', '')
        })

    elif section == 'cta':
        set_content('cta', {
            'title': form.get('title', ''),
            'button_text': form.get('button_text', '')
        })

    flash(f'{section.replace("_", " ").title()} saved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/upload', methods=['POST'])
@admin_required
def admin_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        if os.environ.get('CLOUDINARY_URL'):
            import cloudinary
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(file)
            return jsonify({'path': upload_result['secure_url'], 'filename': file.filename})
        else:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{secrets.token_hex(6)}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            return jsonify({'path': f"/uploads/{filename}", 'filename': filename})
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def serve_upload(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/admin/add/<section>', methods=['POST'])
@admin_required
def admin_add_item(section):
    """Add a new blank item to a list-based section."""
    data = get_content(section)
    if data is None:
        data = []

    templates = {
        'projects': {'title': 'NEW PROJECT', 'category': 'CATEGORY', 'description': 'Project description...', 'image': 'img/gallery/img-6.png', 'link': '#', 'homepage_desc': 'SHORT DESCRIPTION', 'github_link': '', 'website_link': '', 'tech_stack': '', 'date': '', 'client': 'PERSONAL PROJECT', 'overview': '', 'challenge': '', 'solution': '', 'gallery_images': []},
        'mini_projects': {'title': 'NEW MINI PROJECT', 'category': 'AI GAME', 'image': 'img/gallery/img-6.png', 'link': '#'},
        'education': {'period': '2024 - 2025', 'type': 'DEGREE', 'title': 'NEW DEGREE', 'institution': 'Institution Name', 'description': 'Description...'},
        'experience': {'period': '2024 - PRESENT', 'type': 'JOB', 'title': 'NEW ROLE', 'company': 'Company Name', 'description': 'Description...'},
        'skills': {'name': 'NEW SKILL', 'icon': 'fas fa-star'},
        'certifications': {'title': 'NEW CERTIFICATION', 'image': '', 'link': '#'},
        'blog_posts': {'title': 'NEW BLOG POST', 'category': 'CATEGORY', 'date': 'JUNE 2026', 'excerpt': 'Blog excerpt...', 'body': 'Blog body content...', 'image': 'img/gallery/img-6.png', 'image2': '', 'link': '/blog-details.html'},
    }

    if section in templates:
        data.append(templates[section])
        set_content(section, data)
        flash(f'New {section.replace("_", " ").rstrip("s")} added!', 'success')
    else:
        flash('Invalid section.', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<section>/<int:index>', methods=['POST'])
@admin_required
def admin_delete_item(section, index):
    """Delete an item from a list-based section by index."""
    data = get_content(section)
    if data and 0 <= index < len(data):
        removed = data.pop(index)
        set_content(section, data)
        flash(f'Deleted "{removed.get("title", "item")}" successfully.', 'success')
    else:
        flash('Item not found.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/password', methods=['POST'])
@admin_required
def admin_change_password():
    current = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    username = session.get('admin_user', 'admin')

    if not verify_admin(username, current):
        flash('Current password is incorrect.', 'danger')
    elif new_pw != confirm:
        flash('New passwords do not match.', 'danger')
    elif len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'danger')
    else:
        db_change_password(username, new_pw)
        flash('Password changed successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/username', methods=['POST'])
@admin_required
def admin_change_username():
    current_password = request.form.get('current_password', '')
    new_username = request.form.get('new_username', '').strip()
    username = session.get('admin_user', 'admin')

    if not verify_admin(username, current_password):
        flash('Current password is incorrect.', 'danger')
    elif not new_username:
        flash('New username cannot be empty.', 'danger')
    elif len(new_username) < 3:
        flash('Username must be at least 3 characters.', 'danger')
    else:
        success = db_change_username(username, new_username)
        if success:
            session['admin_user'] = new_username
            flash(f'Username changed to "{new_username}" successfully!', 'success')
        else:
            flash('That username is already taken.', 'danger')
    return redirect(url_for('admin_dashboard'))

# ─── Individual Project Detail ─────────────────────────────
@app.route('/project/<int:index>')
def project_detail(index):
    content = get_all_content()
    projects = content.get('projects', [])
    if 0 <= index < len(projects):
        return render_template('project-details.html', c=content, project=projects[index], project_index=index)
    return redirect(url_for('index'))

# ─── Individual Blog Detail ─────────────────────────────
@app.route('/blog/<int:index>')
def blog_detail(index):
    content = get_all_content()
    posts = content.get('blog_posts', [])
    if 0 <= index < len(posts):
        return render_template('blog-details.html', c=content, post=posts[index], post_index=index)
    return redirect(url_for('admins_views', page='blog-list'))

# ─── Admin: Export DB ──────
@app.route('/admin/export-db')
@admin_required
def admin_export_db():
    """Download the current live database file so it can be committed and redeployed."""
    from flask import send_file
    from models import DB_PATH
    try:
        return send_file(
            DB_PATH,
            as_attachment=True,
            download_name='db.sqlite3',
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


# ─── Dynamic Page Route ─────
@app.route('/<page>')
def admins_views(page):  
    try:
        # Check if the page has an extension; if not, try adding .html
        template_name = page
        if '.' not in page:
            template_name = f"{page}.html"
        content = get_all_content()
        return render_template(template_name, c=content)
    except:
        return render_template('index.html', c=get_all_content())

@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html", c=get_all_content()), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')


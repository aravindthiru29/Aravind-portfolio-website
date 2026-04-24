from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-for-portfolio')

# Robust Mail Configuration
# Priority: Environment Variables > Hardcoded Fallbacks (for Gmail)
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

@app.route('/')
def index():
    return render_template('index.html')

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
        
    return render_template('contact.html')

@app.route('/<page>')
def admins_views(page):  
    try:
        # Check if the page has an extension; if not, try adding .html
        template_name = page
        if '.' not in page:
            template_name = f"{page}.html"
            
        return render_template(template_name)
    except:
        return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html"), 404
    
if __name__ == '__main__':
    app.run(debug=True)

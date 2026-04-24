from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-for-portfolio')

# Mail configuration with Robust Defaults
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
# Auto-configure TLS/SSL based on Port for Gmail compatibility
if MAIL_PORT == 465:
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
else:
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

app.config.update(
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_USE_TLS=MAIL_USE_TLS,
    MAIL_USE_SSL=MAIL_USE_SSL,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))
)

# Debug: Print configuration to Vercel Logs (Hidden Password)
print(f"--- Mail Config Loaded ---")
print(f"Server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
print(f"TLS: {app.config['MAIL_USE_TLS']}, SSL: {app.config['MAIL_USE_SSL']}")
print(f"User: {app.config['MAIL_USERNAME']}")
print(f"Password Set: {'Yes' if app.config['MAIL_PASSWORD'] else 'No'}")
print(f"--------------------------")

mail = Mail(app)

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
        msg = Message(
            subject=f"Portfolio Contact: {subject}",
            recipients=[os.environ.get('MAIL_RECEIVER', os.environ.get('MAIL_USERNAME'))],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        )
        
        try:
            with app.app_context():
                mail.send(msg)
            print("Mail sent successfully!")
            flash('SUCCESS! YOUR MESSAGE HAS BEEN SENT.', 'success')
        except Exception as e:
            import traceback
            print(f"CRITICAL ERROR: {str(e)}")
            print(traceback.format_exc())
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

from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-portfolio' # In production, use an environment variable

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
        
        # Here you would typically send an email or save to a database
        print(f"Message from {name} ({email}): {subject} - {message}")
        
        flash('SUCCESS! YOUR MESSAGE HAS BEEN SENT.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/<page>')
def admins_views(page):  
    try:
        # Prevent trying to render template for common missing files or paths with dots to avoid issues
        if '.' in page and not page.endswith('.html'):
            return "File not found", 404
        return render_template(f"{page}")
    except:
        return render_template('index.html') # Fallback to home instead of crashing

@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html"), 404
    
if __name__ == '__main__':
    app.run(debug=True)

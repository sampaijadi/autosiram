import os
import yaml
import markdown
import subprocess
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

CONTENT_DIR = 'content'
TEMPLATES_DIR = 'templates'

# HTML Template with Pico.css and custom styles
ADMIN_HTM = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <title>CMS Admin Panel</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.purple.min.css">
    <style>
        :root { --font-family: 'Inter', sans-serif; }
        body { background: #0b0e14; }
        .container { max-width: 1000px; padding: 2rem 0; }
        .post-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); }
        .editor-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        textarea { height: 400px; font-family: 'Fira Code', monospace; }
        .btn-group { display: flex; gap: 1rem; }
        .label-text { font-weight: bold; margin-bottom: 0.5rem; display: block; }
        .alert { padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
        .success { background: rgba(56, 189, 248, 0.1); border: 1px solid #38bdf8; color: #38bdf8; }
    </style>
</head>
<body class="container">

    <nav>
        <ul><li><strong><a href="/">CMS EDITOR</a></strong></li></ul>
        <ul>
            <li><a href="/" class="secondary">DASHBOARD</a></li>
            <li><a href="/new" role="button" class="outline">NEW POST +</a></li>
        </ul>
    </nav>

    {% if message %}
    <div class="alert success">{{ message }}</div>
    {% endif %}

    {% if page == 'dashboard' %}
    <header class="editor-header">
        <h1>Dashboard. <span style="opacity: 0.5;">Manage your content.</span></h1>
        <div class="btn-group">
            <a href="/build" role="button" class="contrast">REBUILD SITE</a>
            <a href="/publish" role="button">PUBLISH LIVE 🚀</a>
        </div>
    </header>

    <div class="grid">
        {% for post in posts %}
        <article class="post-card">
            <h3>{{ post.title }}</h3>
            <p><small class="secondary">{{ post.date }}</small></p>
            <p>{{ post.summary }}</p>
            <footer>
                <a href="/edit/{{ post.filename }}" role="button" class="secondary outline">EDIT</a>
            </footer>
        </article>
        {% endfor %}
    </div>
    {% endif %}

    {% if page == 'editor' %}
    <header class="editor-header">
        <h1>Editing: <span style="opacity: 0.5;">{{ filename or 'New Post' }}</span></h1>
        <a href="/" class="secondary">BACK &larr;</a>
    </header>

    <form method="POST">
        <label>
            <span class="label-text">Title</span>
            <input type="text" name="title" value="{{ frontmatter.title or '' }}" required placeholder="Post Title">
        </label>

        <div class="grid">
            <label>
                <span class="label-text">Date</span>
                <input type="date" name="date" value="{{ frontmatter.date or '2026-04-06' }}">
            </label>
            <label>
                <span class="label-text">Summary</span>
                <input type="text" name="summary" value="{{ frontmatter.summary or '' }}" placeholder="Small excerpt">
            </label>
        </div>

        <label>
            <span class="label-text">Content (Markdown)</span>
            <textarea name="content" placeholder="Write your story here...">{{ content or '' }}</textarea>
        </label>

        <button type="submit" class="primary">SAVE CHANGES</button>
    </form>
    {% endif %}

</body>
</html>
"""

def get_posts():
    posts = []
    if not os.path.exists(CONTENT_DIR): os.makedirs(CONTENT_DIR)
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.md'):
            with open(os.path.join(CONTENT_DIR, filename), 'r', encoding='utf-8') as f:
                raw = f.read()
            parts = raw.split('---', 2)
            fm = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
            posts.append({
                'title': fm.get('title', 'Untitled'),
                'date': fm.get('date', ''),
                'summary': fm.get('summary', ''),
                'filename': filename
            })
    return sorted(posts, key=lambda x: x['date'], reverse=True)

@app.route('/')
def dashboard():
    msg = request.args.get('msg')
    return render_template_string(ADMIN_HTM, page='dashboard', posts=get_posts(), message=msg)

@app.route('/edit/<filename>', methods=['GET', 'POST'])
@app.route('/new', methods=['GET', 'POST'])
def edit_post(filename=None):
    filepath = os.path.join(CONTENT_DIR, filename) if filename else None
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        summary = request.form['summary']
        content = request.form['content']
        
        # New filename from title if not existing
        if not filename:
            filename = title.lower().replace(' ', ' ').strip().replace(' ', '-').replace(':', '') + '.md'
            filepath = os.path.join(CONTENT_DIR, filename)

        file_content = f"""---
title: "{title}"
date: "{date}"
summary: "{summary}"
---

{content}"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        return redirect(url_for('dashboard', msg=f"Post '{title}' saved successfully!"))

    # GET
    fm = {}
    content = ""
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = f.read()
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1])
            content = parts[2].strip()
            
    return render_template_string(ADMIN_HTM, page='editor', filename=filename, frontmatter=fm, content=content)

@app.route('/build')
def build_site():
    import cms
    cms.build()
    return redirect(url_for('dashboard', msg="Site rebuilt locally in 'public/' folder!"))

@app.route('/publish')
def publish_site():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Published from CMS Editor"], check=True)
        subprocess.run(["git", "push"], check=True)
        return redirect(url_for('dashboard', msg="Site pushed to GitHub! It will be live soon."))
    except Exception as e:
        return redirect(url_for('dashboard', msg=f"Push failed: {str(e)}"))

if __name__ == "__main__":
    app.run(port=5000, debug=True)

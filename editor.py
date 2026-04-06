import os
import yaml
import markdown
import subprocess
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

CONTENT_DIR = 'content'
TEMPLATES_DIR = 'templates'

# HTML Template with Pico.css and Theme Toggle
ADMIN_HTM = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <title>CMS Admin Panel</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.purple.min.css">
    <style>
        :root { --font-family: 'Inter', sans-serif; }
        .container { max-width: 1000px; padding: 2rem 0; }
        .post-card { border-radius: 1rem !important; }
        textarea { height: 450px; font-family: 'Fira Code', monospace; }
        .btn-group { display: flex; gap: 1rem; }
    </style>
    <script>
        const theme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        function toggleTheme() {
            const tgt = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', tgt);
            localStorage.setItem('theme', tgt);
        }
    </script>
</head>
<body class="container">
    <nav>
        <ul><li><strong><a href="/" class="secondary">PYTHON CMS EDITOR</a></strong></li></ul>
        <ul>
            <li><button class="outline secondary" onclick="toggleTheme()" style="border:none; box-shadow:none;">🌓</button></li>
            <li><a href="/settings" class="secondary">SETTINGS</a></li>
            <li><a href="/new" role="button" class="outline">NEW POST +</a></li>
        </ul>
    </nav>

    {% if message %}
    <div style="background:rgba(139,92,246,0.1); border:1px solid #8b5cf6; padding:1rem; border-radius:10px; margin-bottom:2rem; color:#8b5cf6;">
        {{ message }}
    </div>
    {% endif %}

    {% if page == 'settings' %}
    <header style="margin-bottom:2rem;">
        <h1>Site Settings.</h1>
        <p class="secondary">Manage your hero text and footer globally.</p>
    </header>
    <form method="POST">
        <label>Global Site Name (Browser Tab Name) <input type="text" name="site_name" value="{{ settings.site_name or '' }}"></label>
        <div class="grid">
            <label>Hero Title <input type="text" name="hero_title" value="{{ settings.hero_title or '' }}"></label>
            <label>Title Weight
                <select name="hero_title_weight">
                    <option value="400" {% if settings.hero_title_weight == '400' %}selected{% endif %}>400 - Regular</option>
                    <option value="500" {% if settings.hero_title_weight == '500' %}selected{% endif %}>500 - Medium</option>
                    <option value="600" {% if settings.hero_title_weight == '600' %}selected{% endif %}>600 - Semi-Bold</option>
                    <option value="700" {% if settings.hero_title_weight == '700' %}selected{% endif %}>700 - Bold</option>
                    <option value="800" {% if settings.hero_title_weight == '800' %}selected{% endif %}>800 - Extra Bold</option>
                </select>
            </label>
        </div>
        <div class="grid">
            <label>Hero Subtitle <input type="text" name="hero_subtitle" value="{{ settings.hero_subtitle or '' }}"></label>
            <label>Subtitle Weight
                <select name="hero_subtitle_weight">
                    <option value="400" {% if settings.hero_subtitle_weight == '400' %}selected{% endif %}>400 - Regular</option>
                    <option value="500" {% if settings.hero_subtitle_weight == '500' %}selected{% endif %}>500 - Medium</option>
                    <option value="600" {% if settings.hero_subtitle_weight == '600' %}selected{% endif %}>600 - Semi-Bold</option>
                    <option value="700" {% if settings.hero_subtitle_weight == '700' %}selected{% endif %}>700 - Bold</option>
                    <option value="800" {% if settings.hero_subtitle_weight == '800' %}selected{% endif %}>800 - Extra Bold</option>
                </select>
            </label>
        </div>
        <label>Site Description <textarea name="site_description">{{ settings.site_description or '' }}</textarea></label>
        <label>Footer Text (HTML allowed) <input type="text" name="footer_text" value="{{ settings.footer_text or '' }}"></label>
        <button type="submit" class="primary">SAVE ALL SETTINGS</button>
    </form>
    {% endif %}

    {% if page == 'dashboard' %}
    <header style="margin-bottom:3rem;">
        <h1>Your Dashboard.</h1>
        <p class="secondary">Manage your content across GitHub.</p>
        <div class="btn-group">
            <a href="/build" role="button" class="contrast">REBUILD LOCAL</a>
            <a href="/publish" role="button">PUBLISH LIVE 🚀</a>
        </div>
    </header>

    <div class="grid">
        {% for post in posts %}
        <article class="post-card">
            <header>
                <strong>{{ post.title }}</strong>
                <div style="font-size:0.8rem; opacity:0.6;">{{ post.date }}</div>
            </header>
            <p style="font-size:0.9rem;">{{ post.summary }}</p>
            <footer>
                <a href="/edit/{{ post.filename }}" role="button" class="secondary outline full-width">EDIT POST</a>
            </footer>
        </article>
        {% endfor %}
    </div>
    {% endif %}

    {% if page == 'editor' %}
    <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
        <h2>{{ filename or 'Crafting New Story' }}</h2>
        <a href="/" class="secondary">&larr; Dashboard</a>
    </header>

    <form method="POST">
        <label>Post Title <input type="text" name="title" value="{{ frontmatter.title or '' }}" required></label>
        <div class="grid">
            <label>Date <input type="date" name="date" value="{{ frontmatter.date or '2026-04-06' }}"></label>
            <label>Summary <input type="text" name="summary" value="{{ frontmatter.summary or '' }}"></label>
        </div>
        <label>Markdown Content <textarea name="content" required>{{ content or '' }}</textarea></label>
        <button type="submit">SAVE TO CONTENT FOLDER</button>
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

@app.route('/settings', methods=['GET', 'POST'])
def manage_settings():
    filepath = 'settings.yaml'
    settings = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f) or {}

    if request.method == 'POST':
        # Update settings dictionary
        fields = ['site_name', 'hero_title', 'hero_title_weight', 'hero_subtitle', 'hero_subtitle_weight', 'site_description', 'footer_text']
        for key in fields:
            settings[key] = request.form.get(key, '')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(settings, f)
        return redirect(url_for('dashboard', msg="Site settings updated successfully!"))

    return render_template_string(ADMIN_HTM, page='settings', settings=settings)

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

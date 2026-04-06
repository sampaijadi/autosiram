import os
import shutil
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Settings
CONTENT_DIR = 'content'
TEMPLATE_DIR = 'templates'
OUTPUT_DIR = 'public'
ASSETS_DIR = 'assets'

def build():
    # Make sure output directory is clean
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    index_template = env.get_template('index.html')
    post_template = env.get_template('post.html')

    posts = []

    # 1. Process all markdown files in content/
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(CONTENT_DIR, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Split frontmatter from content
            # Expects --- at start and end of frontmatter
            parts = raw_content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                md_content = parts[2]
            else:
                frontmatter = {}
                md_content = raw_content

            # Meta data
            title = frontmatter.get('title', filename.replace('.md', '').replace('-', ' ').title())
            date = frontmatter.get('date', datetime.now().strftime('%Y-%m-%d'))
            summary = frontmatter.get('summary', '') or md_content[:150] + '...'
            
            # Convert MD to HTML
            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'codehilite', 'tables'])
            
            slug = filename.replace('.md', '.html')
            
            posts.append({
                'title': title,
                'date': date,
                'summary': summary,
                'url': slug,
                'content': html_content,
                'slug': slug
            })

    # Sort posts by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)

    # 2. Render individual post pages
    for post in posts:
        output_post_path = os.path.join(OUTPUT_DIR, post['slug'])
        rendered_post = post_template.render(
            title=post['title'],
            date=post['date'],
            content=post['content']
        )
        with open(output_post_path, 'w', encoding='utf-8') as f:
            f.write(rendered_post)
            
    # 3. Render the index page
    rendered_index = index_template.render(
        title="Home",
        posts=posts
    )
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(rendered_index)

    # 4. Copy assets
    if os.path.exists(ASSETS_DIR):
        shutil.copytree(ASSETS_DIR, os.path.join(OUTPUT_DIR, 'assets'))
        
    print(f"Successfully generated {len(posts)} posts and home page in '{OUTPUT_DIR}/'.")

if __name__ == "__main__":
    build()

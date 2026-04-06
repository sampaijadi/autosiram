# 🚀 Python-Pico Static CMS

A premium, minimalist static site generator powered by **Python**, **Pico.css**, and **GitHub Actions**.

## 🎨 Features
- **Pico.css Stylings**: Clean, semantic, and modern design.
- **Glassmorphism**: Elegant depth and vibrant backgrounds.
- **Python-Powered**: Simple markdown-to-html conversion.
- **GitHub Ready**: Hosting-optimized with build folder structure.

## 🛠️ How to Use

### 1. Write Content
Create a new `.md` file in the `content/` folder with YAML frontmatter:
```markdown
---
title: "My Amazing Post"
date: "2026-04-06"
summary: "Short excerpt of my thoughts."
---
Write your content here!
```

### 2. Build the Site
Run the CMS script via terminal:
```bash
python cms.py
```
This generates your website inside the `public/` directory.

### 3. Preview Locally
Preview your site instantly:
```bash
python preview.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

## 🌍 Hosting on GitHub
1.  **Create a New Repo** on GitHub.
2.  **Push your code** (including `public/`).
3.  **Go to Settings** -> **Pages**.
4.  Set **Build and deployment** -> **Source** to **Deploy from a branch**.
5.  Set **Branch** to `main` and **Folder** to `/public`.
6.  Click **Save**. Your site will be live soon!

---
*Built with love by Antigravity.*

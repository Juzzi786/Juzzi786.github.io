# Zuzer Chathiwala — Portfolio

Personal portfolio site for bioinformatics, computational biology and applied machine learning.

Live at **[juzzi786.github.io](https://juzzi786.github.io)**

---

## Stack

Static HTML generated from a single `content.json` file via `build.py`. No framework, no package manager, no build toolchain — only Python 3.9+ required.

- **Content** → `content.json`
- **Styles** → `assets/styles.css` (design tokens, 12-column grid, type scale)
- **JS** → `assets/main.js` (6 KB, progressive enhancement only — mobile drawer, scroll-spy, copy-email, footer year)
- **Renderer** → `build.py` (one function per component)

The site works fully with JavaScript disabled. Project write-ups are native `<details>` elements, smooth scrolling is CSS, and every link is a real anchor.

---

## Run locally

```bash
python build.py --serve
```

Opens at `http://localhost:8000`. To build without serving:

```bash
python build.py
```

Outputs: `index.html`, `404.html`, `assets/favicon.svg`, `assets/og-image.svg`.

The build validates content on every run and warns on: duplicate project IDs, a publication pointing at a nonexistent project, a broken nav anchor, or a missing CV file.

---

## Project structure

```
content.json          ← all site content; the only file you normally edit
build.py              ← static renderer
assets/
  styles.css          ← design system and layout
  main.js             ← progressive enhancements
  favicon.svg         ← generated
  og-image.svg        ← generated share card
  Zuzer_Chathiwala_Resume.pdf
index.html            ← generated (do not edit directly)
404.html              ← generated (do not edit directly)
```

---

## Editing content

All text on the site lives in `content.json`. Edit it and re-run `python build.py`.

### Add a project

Append to `projects.items`:

```json
{
  "id": "unique-slug",
  "title": "Project title",
  "kind": "Research project",
  "period": "2026",
  "status": "Published — IEEE …",
  "domain": "Cancer genomics",
  "summary": "Two or three sentences.",
  "problem": "What was hard and why it mattered.",
  "contribution": "What you personally did.",
  "pipeline": ["Stage 1", "Stage 2", "Final stage"],
  "tools": ["Python", "DESeq2"],
  "outputs": [
    { "label": "Paper title", "venue": "IEEE …", "status": "Published" }
  ]
}
```

`pipeline` renders as a numbered workflow diagram — no image needed. Project order on the page follows array order.

### Add a publication

Add to the matching group in `publications.groups`:

```json
{
  "title": "Exact published title",
  "venue": "2026 IEEE Conference on Something (ABC)",
  "year": "2026",
  "status": "Published",
  "authors": ["First Author", "Zuzer Chathiwala"],
  "doi": "10.1109/…",
  "project": "project-id"
}
```

Author entries matching `profile.name` are highlighted automatically. Set `doi` for a **View paper** link. Set `project` to link the publication to a project card.

### Replace the CV

Drop the new PDF into `assets/` and update `profile.cv.file`, then rebuild. The build fails if the file is missing.

---

## Design tokens

Defined at the top of `assets/styles.css`:

| Token | Value | Use |
|---|---|---|
| `--bg` | `#fafaf7` | Page background |
| `--bg-sunk` | `#f4f0f0` | Alternating sections |
| `--ink-strong` | `#0d1b33` | Headings |
| `--ink` | `#172b4d` | Body text |
| `--ink-muted` | `#4f5a67` | Secondary text |
| `--accent` | `#0d9488` | Rules, dots, decorative marks |
| `--accent-deep` | `#0f766e` | Accent-coloured text (WCAG AA) |

Type: Inter (interface) + IBM Plex Mono (labels, metadata, numerals) via Google Fonts.  
Layout: 12-column grid, 1320px max width, breakpoints at 40rem / 48rem / 62rem.

---

## Deploy

The output is static files — any static host works.

### GitHub Pages

1. Ensure the repository is named **`Juzzi786.github.io`** (must match your username for the root URL).
2. Push or upload `index.html`, `404.html` and the `assets/` folder to `main`.
3. **Settings → Pages → Source: Deploy from a branch → `main` / `(root)` → Save.**
4. Live at `https://juzzi786.github.io` within a minute or two.

### Other options

- **Netlify Drop** — drag the output folder to [app.netlify.com/drop](https://app.netlify.com/drop), live immediately.
- **Cloudflare Pages / Vercel** — connect the repo, framework preset "None", build command empty, output directory `.`.

If the deploy URL differs from `https://juzzi786.github.io`, update `site.url` in `content.json` and rebuild — it drives the canonical link and link preview metadata.

---

## License

Content © Zuzer Chathiwala. Code is MIT.

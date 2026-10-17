# Zuzer Chathiwala — portfolio

A personal research and engineering portfolio for bioinformatics, computational
biology and applied machine learning. Swiss Modernist layout, light scientific
palette, one page plus a 404.

Everything the site says lives in **`content.json`**. `build.py` renders it into
static HTML. There is no framework, no package manager and no build toolchain —
the only requirement is Python 3.9+, which is already on this machine.

---

## Why not React / Vite

The original brief asked for React + TypeScript + Vite. This machine has no
Node.js, npm, bun or deno installed, so a Vite project could have been written
but never installed, type-checked, built or run — and an unverified build is
worth less than a working site. The stack here was chosen so that every claim
below could actually be tested in a browser.

The content layer is deliberately framework-agnostic: `content.json` ports to a
React app unchanged if you install Node later. See *Porting to React* at the end.

---

## Run it

```bash
python build.py --serve
```

Then open <http://localhost:8000>.

To build without serving:

```bash
python build.py
```

That writes `index.html`, `404.html`, `assets/favicon.svg` and
`assets/og-image.svg`. `build.py` also validates the content and prints a
warning for a duplicate project id, a publication pointing at a project that
does not exist, a nav link that is not an in-page anchor, or a missing CV file.

---

## Project structure

```
content.json      ← every word on the site; the only file you normally edit
build.py          ← renderer; one function per component
index.html        ← generated — do not edit by hand
404.html          ← generated
assets/
  styles.css      ← design system: tokens, grid, type scale, components
  main.js         ← progressive enhancement only (see below)
  favicon.svg     ← generated
  og-image.svg    ← generated share card
  Zuzer_Chathiwala_Resume.pdf   ← the file the CV buttons download
.claude/launch.json             ← dev-server config for the Claude Code browser pane
```

`index.html`, `404.html`, `favicon.svg` and `og-image.svg` are build output.
Edit `content.json`, `styles.css` or `build.py` instead and re-run the build.

### What JavaScript does and does not do

`assets/main.js` is 6 KB and purely additive: the mobile drawer, active-section
highlighting in the nav, a copy-email button and the footer year. With
JavaScript disabled the whole site still works — the project write-ups are
native `<details>` elements, smooth scrolling is CSS, and every link is a real
link. The copy-email button removes itself when the Clipboard API is
unavailable rather than sitting there doing nothing.

---

## Editing the content

### Add or change a project

Append an object to `projects.items` in `content.json`:

```json
{
  "id": "unique-slug",               // also the in-page anchor: /#unique-slug
  "title": "Project title",
  "kind": "Research project",
  "period": "2026",
  "status": "Completed",             // "Published — …" / "Accepted — …" /
                                     // "In progress" drive the status dot colour
  "domain": "Cancer genomics",
  "summary": "Two or three sentences.",
  "problem": "What was hard and why it mattered.",
  "contribution": "What you personally did.",
  "pipeline": ["Stage 1", "Stage 2", "Final stage"],
  "tools": ["Python", "PyTorch"],
  "outputs": [
    { "label": "Paper title", "venue": "IEEE …", "status": "Published" }
  ]
}
```

`pipeline` renders as the numbered workflow diagram on the card — it is built
from your text in CSS, so there is no image to produce. `outputs` may be `[]`;
the card then shows "No associated publication." Each project gets a stable
4×4 geometric mark derived from its `id`, so changing the id changes the mark.

Project order on the page is the order in the array. Put the strongest first.

### Add a publication

Add to the matching group in `publications.groups` (`Journal articles` or
`Conference papers`):

```json
{
  "title": "Exact published title",
  "venue": "2026 IEEE Conference on Something (ABC)",
  "year": "2026",
  "status": "Published",
  "authors": ["First Author", "Zuzer Chathiwala", "Third Author"],
  "doi": "10.1109/…",
  "url": "",
  "project": "sleep-apnea"
}
```

`authors` is an array in published order; any entry matching `profile.name`
is automatically highlighted. A `doi` (or a `url`, which wins) renders a
**View paper** link to `https://doi.org/<doi>` plus the printed DOI; without
either, the entry shows "DOI not recorded". `project` is optional — set it to a
project `id` to render a "See the project" link.

The quickest way to fill in a new entry correctly is to let Crossref give you
the registered record rather than typing it from memory:

```bash
curl -s "https://api.crossref.org/works/10.1109/YOUR.DOI"
```

That returns the exact title, venue, year and author order as registered.

### Add a profile link

Add to `profile.links`:

```json
{ "label": "GitHub", "handle": "yourhandle", "url": "https://github.com/yourhandle" }
```

It appears in the hero, the contact panel and the footer, and is added to the
`sameAs` list in the page's structured data. There is currently no GitHub,
ORCID, Google Scholar or personal-site link because none appears on the resume.

### Replace the CV

Drop the new PDF into `assets/` and point `profile.cv.file` at it, then rebuild.
The build fails loudly if the file is missing, so the download button can never
point at nothing.

### Show your phone number

`profile.phone` is empty by default so a personal number is not published.
Set it to `"+91 93276 01140"` to add a `tel:` row to the contact panel.

### Set the production URL

Set `site.url` to your real origin (e.g. `https://zuzerchathiwala.com`). That
switches on the canonical link, `og:url` and the `og:image` tags, which stay off
while the URL is unknown so nothing points at a non-existent address.

---

## Design system

Tokens live at the top of `assets/styles.css` and drive everything:

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#fafaf7` | page |
| `--bg-sunk` | `#f4f4f0` | alternating sections |
| `--ink-strong` | `#0d1b33` | headings |
| `--ink` | `#172b4d` | body |
| `--ink-muted` | `#4f5a67` | secondary text |
| `--ink-faint` | `#5b6878` | metadata |
| `--accent` | `#0d9488` | rules, dots, non-text marks |
| `--accent-deep` | `#0f766e` | accent-coloured **text** |
| `--rule` | `#e2e8f0` | hairlines |

Both secondary inks and `--accent-deep` were chosen to clear WCAG AA (4.5:1) on
every light surface in the palette; `--accent` itself does not, which is why
accent-coloured text uses `--accent-deep`. Keep that split if you retune colours.

Type is Inter (interface) and IBM Plex Mono (labels, metadata, numerals), loaded
from Google Fonts with a system fallback stack. To self-host, drop the woff2
files in `assets/fonts/`, replace the `<link>` in `render_head()` with `@font-face`
rules, and the rest of the stylesheet needs no change.

Layout is a 12-column grid at a 1320px max width with fluid gutters. Breakpoints
are 40rem, 48rem and 62rem.

---

## Deploy

The output is static files, so any static host works. There is no build step to
configure on the host — run `python build.py` locally and upload the result.

**`site.url` must match wherever you deploy.** It drives the canonical link,
`og:url` and `og:image`. It is currently set to `https://juzzi786.github.io`,
which assumes a GitHub Pages repository named `Juzzi786.github.io`. Change it
and rebuild if you deploy anywhere else — if it is wrong, link previews break.

### GitHub Pages (recommended, no Git required)

Git is not installed on this machine, so use GitHub's web uploader.

1. Create a **public** repository named exactly **`Juzzi786.github.io`**
   (the name must match your username to get the clean root URL).
2. On the empty repo page choose **uploading an existing file**, then drag in
   `index.html`, `404.html` and the whole `assets` folder. The uploader keeps
   the folder structure. `build.py`, `content.json` and `README.md` are
   optional — upload them so you can edit the site later from any machine.
3. Commit directly to `main`.
4. **Settings → Pages → Source: Deploy from a branch → `main` / `(root)` → Save.**
5. Wait one to two minutes. The site is live at <https://juzzi786.github.io>.
   `404.html` is picked up automatically.

To update later: rebuild locally, then re-upload the changed files (the
uploader overwrites by path). Installing Git makes this a one-line
`git add -A && git commit -m "update" && git push` instead.

If you name the repository something else, say `portfolio`, the URL becomes
`https://juzzi786.github.io/portfolio` — set `site.url` to that exact value,
including the path, and rebuild.

### Alternatives

- **Netlify Drop** (<https://app.netlify.com/drop>) — drag the folder in, live
  in seconds, no account needed to start. The URL is random until you rename
  the site in Site settings; set `site.url` to the final one and re-upload.
- **Cloudflare Pages / Vercel** — connect the GitHub repo, framework preset
  "None"/"Other", build command empty, output directory `.`.

### Check the link preview before sharing

The share card is `assets/og-image.png` (1200×630, regenerated by `build.py`
from your name and headline). Once the site is live, run the URL through:

- LinkedIn — <https://www.linkedin.com/post-inspector/>
- X — <https://cards-dev.twitter.com/validator>
- Facebook / WhatsApp — <https://developers.facebook.com/tools/debug/>

LinkedIn caches previews for about a week, so if you change the card or the
description, use Post Inspector to force a re-scrape rather than waiting.

---

## What was verified

Checked in a real browser against the built site:

- Build runs clean; content validation reports no problems.
- No console errors or warnings on load.
- No horizontal overflow at 320, 390, 768, 1280 and 1440 px.
- Mobile drawer: opens, moves focus to the first link, traps Tab, closes on
  Escape and returns focus to the toggle, closes on link selection, locks body
  scroll, and is removed entirely at desktop widths.
- Active-section highlighting tracks the section actually in view, with exactly
  one link marked at a time.
- Every in-page anchor resolves to an existing element; none is broken.
- One `<h1>`; no skipped heading levels anywhere on the page.
- Every `<svg>` is either `aria-hidden` or has an `aria-label`.
- Every `target="_blank"` link carries `rel="noopener"`.
- No button is unlabelled.
- Contrast: all 542 text elements measured against their actual composited
  background pass WCAG AA — zero failures.
- All six publication titles, venues, years and author orders were taken from
  the registered Crossref records for their DOIs, not transcribed by hand.
- All six DOIs resolve to live publisher pages (Elsevier / IEEE Xplore).
- CV link serves a real 142 KB `application/pdf` (HTTP 200).
- `404.html` and `assets/og-image.svg` both serve (HTTP 200).
- Project write-ups expand and collapse, and work with JavaScript disabled.

Not verified, because the tooling is not on this machine: no Node-based linter,
bundler, type-checker or Lighthouse run. There are no TypeScript types because
there is no TypeScript.

---

## Information still needed from you

Nothing on the site is invented — where the resume is silent, the site stays
silent. These are the gaps worth filling:

1. **Two publications have no project write-up.** The norovirus surveillance
   review and the hypothyroid ensemble paper appear under Publications but have
   no card under Projects, because there is no description of the problem, your
   contribution or the method to write one from. Both are worth adding —
   especially the journal review, which is the only non-IEEE item and the only
   pathogen-genomics work on the site.
2. **Quantitative results.** No accuracy, sensitivity or AUC figures appear
   anywhere on the site, because none were supplied. The papers are linked, so a
   reader can go and find them — but pulling two or three headline numbers into
   each project write-up is still the single strongest improvement available.
3. **Which city to show.** The contact panel says Rajkot, Gujarat (from the
   resume) while the Elmentoz role says Hyderabad, on-site. If you have moved,
   change `profile.location`.
4. **Elmentoz detail.** The three bullets are a close paraphrase of what you
   told me. Named pipelines, organisms, data types or scale would make the entry
   much more concrete — it is currently the thinnest section on the page.
5. **Per-project GitHub repos.** Your profile is linked, but no repository is
   linked from any individual project. If the code for any of the six is public,
   those links carry real weight with technical reviewers.
6. **Project dates.** The resume dates the hepatocellular carcinoma minor
   project "2026-2027" and the single-cell project "April 2026". Both are
   reproduced verbatim; confirm they are right.
7. **ORCID.** Not supplied. GitHub, Google Scholar and LinkedIn are linked.
8. **Production domain.** Needed for `site.url`.
9. **Phone number.** Omitted by default; say the word and it goes in.
10. **Photograph.** None supplied, and the hero is designed to work without one.

---

## Porting to React

If you install Node later:

```bash
npm create vite@latest portfolio -- --template react-ts
```

Copy `content.json` in as-is and type it with an interface mirroring its shape.
Each `render_*` function in `build.py` maps one-to-one onto a component — the
class names and markup are already the ones the stylesheet expects, so
`assets/styles.css` can be imported unchanged. `assets/main.js` becomes three
small hooks (drawer, scroll-spy, copy) or is dropped in favour of component
state. The `<details>` elements, the semantic landmarks and the metadata in
`render_head()` should carry over verbatim.

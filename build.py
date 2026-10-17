#!/usr/bin/env python3
"""
Static site generator for the Zuzer Chathiwala portfolio.

Reads content.json (the single source of truth for every word on the site) and
writes index.html, 404.html and assets/favicon.svg. No third-party packages:
the standard library is the only dependency.

    python build.py            # build
    python build.py --serve    # build, then serve on http://localhost:8000

Each render_* function below is one component. Markup is semantic HTML; all
styling lives in assets/styles.css and is driven by CSS custom properties.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content.json"
ASSETS = ROOT / "assets"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def esc(value: Any) -> str:
    """Escape a value for use in HTML text or a double-quoted attribute."""
    return html.escape(str(value if value is not None else ""), quote=True)


def join(parts: Iterable[str]) -> str:
    return "\n".join(p for p in parts if p)


def tag(text: str) -> str:
    """One metadata tag. Items ending in '— exposure' render as such."""
    if text.lower().endswith("exposure"):
        body = text.rsplit("—", 1)[0].strip()
        return (
            f'<li class="tag tag--exposure" title="Introductory-level exposure">'
            f"{esc(body)} · exposure</li>"
        )
    return f'<li class="tag">{esc(text)}</li>'


def tags(items: Iterable[str], extra_class: str = "") -> str:
    items = list(items)
    if not items:
        return ""
    cls = f"tags {extra_class}".strip()
    return f'<ul class="{cls}">' + "".join(tag(i) for i in items) + "</ul>"


def status_class(status: str) -> str:
    s = status.lower()
    if "published" in s:
        return "status status--published"
    if "accepted" in s:
        return "status status--accepted"
    if "progress" in s:
        return "status status--progress"
    return "status"


def arrow_svg() -> str:
    return (
        '<svg class="arrow" viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
        '<path d="M2 8h11M9 4l4 4-4 4" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="square"/></svg>'
    )


# --------------------------------------------------------------------------- #
# Deterministic geometry — abstract marks, never a depiction of data
# --------------------------------------------------------------------------- #


def lcg(seed: int):
    """Small deterministic generator so every build produces identical art."""
    state = seed & 0xFFFFFFFF

    def nxt() -> float:
        nonlocal state
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF

    return nxt


def seed_of(text: str) -> int:
    value = 2166136261
    for ch in text:
        value = ((value ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return value


def glyph(identifier: str) -> str:
    """
    A 4x4 mark giving each project a stable visual identity.
    Purely typographic/geometric — it encodes nothing and claims nothing.
    """
    rnd = lcg(seed_of(identifier))
    cells = []
    accent_at = int(rnd() * 16)
    for index in range(16):
        roll = rnd()
        if index == accent_at:
            cells.append('<i class="hi"></i>')
        elif roll > 0.52:
            cells.append('<i class="on"></i>')
        else:
            cells.append("<i></i>")
    return f'<span class="glyph" aria-hidden="true">{"".join(cells)}</span>'


def hero_figure() -> str:
    """
    Abstract Swiss composition: an alignment-grid motif over a tick track.
    Decorative and deterministic. It is not plotted from any dataset, and the
    caption says so.
    """
    rnd = lcg(20260117)
    parts: list[str] = []

    # Registration rules, top
    parts.append(
        '<g stroke="#e2e8f0" stroke-width="1">'
        '<path d="M0 28h480"/><path d="M0 44h480"/>'
        "</g>"
    )
    parts.append(
        '<g fill="#94a3b8" font-family="monospace" font-size="9" '
        'letter-spacing="1.6">'
        '<text x="0" y="20">GRID</text>'
        '<text x="432" y="20">01</text>'
        "</g>"
    )

    # Alignment-grid motif: 16 x 18 matrix
    cols, rows = 16, 18
    cell, gap = 26, 4
    top = 72
    for row in range(rows):
        for col in range(cols):
            roll = rnd()
            x = col * (cell + gap) * (480 / (cols * (cell + gap)))
            w = (480 / cols) - 2.4
            y = top + row * 15.5
            if roll > 0.955:
                fill, opacity = "#0d9488", 1.0
            elif roll > 0.72:
                fill, opacity = "#172b4d", 0.9
            elif roll > 0.44:
                fill, opacity = "#172b4d", 0.22
            else:
                continue
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.1f}" width="{w:.2f}" height="8.5" '
                f'fill="{fill}" opacity="{opacity}"/>'
            )

    # Tick track, bottom
    base = top + rows * 15.5 + 34
    parts.append(f'<path d="M0 {base}h480" stroke="#172b4d" stroke-width="1"/>')
    for index in range(96):
        x = index * (480 / 96) + 1.2
        tick = 4 + rnd() * 22
        colour = "#0d9488" if index % 17 == 3 else "#64748b"
        parts.append(
            f'<path d="M{x:.2f} {base}v-{tick:.1f}" stroke="{colour}" '
            f'stroke-width="1.6" opacity="0.85"/>'
        )
    parts.append(
        '<g fill="#94a3b8" font-family="monospace" font-size="9" '
        f'letter-spacing="1.6"><text x="0" y="{base + 22}">ABSTRACT COMPOSITION</text></g>'
    )

    # Trim the canvas to the drawn content so the panel carries no dead space.
    height = base + 30

    return f"""<figure class="hero__figure">
  <svg viewBox="0 0 480 {height:.0f}" role="img"
       aria-label="Abstract geometric composition: a grid of small bars above a row of vertical ticks, in navy and teal."
       xmlns="http://www.w3.org/2000/svg">
    {join(parts)}
  </svg>
  <figcaption>Decorative composition · alignment-grid motif · not plotted from data</figcaption>
</figure>"""


def wordmark_svg() -> str:
    return (
        '<svg class="wordmark__mark" viewBox="0 0 24 24" aria-hidden="true" '
        'focusable="false" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="24" height="24" rx="2" fill="#172b4d"/>'
        '<rect x="5" y="5" width="6" height="6" fill="#0d9488"/>'
        '<rect x="13" y="5" width="6" height="6" fill="#ffffff" opacity="0.35"/>'
        '<rect x="5" y="13" width="6" height="6" fill="#ffffff" opacity="0.35"/>'
        '<rect x="13" y="13" width="6" height="6" fill="#ffffff" opacity="0.8"/>'
        "</svg>"
    )


def favicon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="3" fill="#172b4d"/>
  <rect x="7" y="7" width="8" height="8" fill="#0d9488"/>
  <rect x="17" y="7" width="8" height="8" fill="#ffffff" opacity="0.35"/>
  <rect x="7" y="17" width="8" height="8" fill="#ffffff" opacity="0.35"/>
  <rect x="17" y="17" width="8" height="8" fill="#ffffff" opacity="0.85"/>
</svg>
"""


def _font(size: int, weight: str = "regular"):
    """
    Find a reasonable UI font for the share card. Inter is not normally
    installed system-wide, so fall back through the platform defaults.
    """
    from PIL import ImageFont

    candidates = {
        "bold": [
            "Inter-SemiBold.ttf",
            r"C:\Windows\Fonts\seguisb.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "regular": [
            "Inter-Regular.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "mono": [
            r"C:\Windows\Fonts\consola.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ],
    }[weight]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def og_image_png(profile: dict, out: Path) -> bool:
    """
    Raster share card for link previews. Social platforms (LinkedIn, X,
    Facebook, WhatsApp, Slack) do not render SVG for og:image, so the PNG is
    the one actually referenced in the metadata.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#fafaf7")
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 8], fill="#0d9488")

    f_label = _font(21, "mono")
    f_name = _font(84, "bold")
    f_head = _font(35, "bold")
    f_sub = _font(22, "regular")

    d.text((80, 128), "P O R T F O L I O", font=f_label, fill="#4f5a67")

    name = profile["name"].upper()
    d.text((80, 182), name, font=f_name, fill="#0d1b33")

    y = 310
    for line in _wrap(d, profile["headline"], f_head, W - 160)[:2]:
        d.text((80, y), line, font=f_head, fill="#172b4d")
        y += 46

    y += 14
    for line in _wrap(d, profile["subheadline"], f_sub, W - 160)[:2]:
        d.text((80, y), line, font=f_sub, fill="#4f5a67")
        y += 30

    # Tick track, matching the hero motif.
    rnd = lcg(7781)
    base = 560
    d.line([(80, base), (W - 80, base)], fill="#172b4d", width=2)
    for i in range(120):
        x = 80 + i * 8.6
        tick = 6 + rnd() * 34
        colour = "#0d9488" if i % 13 == 5 else "#cbd5e1"
        d.line([(x, base), (x, base - tick)], fill=colour, width=2)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    return True


def og_image_svg(profile: dict) -> str:
    """1200x630 share card. SVG so it needs no image tooling to regenerate."""
    name = esc(profile["name"]).upper()
    headline = esc(profile["headline"])
    sub = esc(profile["subheadline"])
    rnd = lcg(7781)
    ticks = []
    for index in range(120):
        x = 80 + index * 8.6
        tick = 6 + rnd() * 34
        colour = "#0d9488" if index % 13 == 5 else "#cbd5e1"
        ticks.append(
            f'<path d="M{x:.1f} 560v-{tick:.1f}" stroke="{colour}" stroke-width="2.4"/>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <rect width="1200" height="630" fill="#fafaf7"/>
  <rect x="0" y="0" width="1200" height="8" fill="#0d9488"/>
  <g font-family="Inter, Helvetica, Arial, sans-serif">
    <text x="80" y="150" font-size="22" letter-spacing="6" fill="#64748b">PORTFOLIO</text>
    <text x="80" y="262" font-size="86" font-weight="600" letter-spacing="-3" fill="#0d1b33">{name}</text>
    <text x="80" y="340" font-size="34" font-weight="500" fill="#172b4d">{headline}</text>
    <text x="80" y="392" font-size="22" fill="#64748b">{sub}</text>
  </g>
  <path d="M80 560h1040" stroke="#172b4d" stroke-width="2"/>
  {join(ticks)}
</svg>
"""


# --------------------------------------------------------------------------- #
# Components
# --------------------------------------------------------------------------- #


def render_head(data: dict) -> str:
    site = data["site"]
    profile = data["profile"]
    url = (site.get("url") or "").rstrip("/")

    canonical = f'\n  <link rel="canonical" href="{esc(url + "/")}">' if url else ""
    og_url = f'\n  <meta property="og:url" content="{esc(url + "/")}">' if url else ""
    # Social platforms do not render SVG previews, so this must be the PNG, and
    # it must be an absolute URL — which is why it only appears once site.url
    # is set.
    og_image = (
        f'\n  <meta property="og:image" content="{esc(url)}/assets/og-image.png">'
        '\n  <meta property="og:image:type" content="image/png">'
        '\n  <meta property="og:image:width" content="1200">'
        '\n  <meta property="og:image:height" content="630">'
        f'\n  <meta property="og:image:alt" content="{esc(profile["name"])} — '
        f'{esc(profile["headline"])}">'
        f'\n  <meta name="twitter:image" content="{esc(url)}/assets/og-image.png">'
        if url
        else ""
    )

    # Structured data, limited to facts present in content.json.
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "jobTitle": "Data Analyst, Core R&D",
        "worksFor": {"@type": "Organization", "name": "Elmentoz Research Pvt. Ltd."},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Marwadi University"},
        "email": f"mailto:{profile['email']}",
        "address": {"@type": "PostalAddress", "addressLocality": profile["location"]},
        "knowsAbout": [
            "Bioinformatics",
            "Computational biology",
            "Machine learning",
            "Deep learning",
            "Transcriptomics",
            "Cancer genomics",
        ],
        "sameAs": [link["url"] for link in profile["links"] if link["url"].startswith("http")],
    }
    if url:
        person["url"] = url + "/"

    return f"""  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(site['title'])}</title>
  <meta name="description" content="{esc(site['description'])}">
  <meta name="author" content="{esc(profile['name'])}">
  <meta name="theme-color" content="{esc(site['themeColor'])}">{canonical}

  <meta property="og:type" content="profile">
  <meta property="og:title" content="{esc(site['title'])}">
  <meta property="og:description" content="{esc(site['description'])}">
  <meta property="og:locale" content="en_IN">{og_url}{og_image}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(site['title'])}">
  <meta name="twitter:description" content="{esc(site['description'])}">

  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="assets/styles.css">

  <script type="application/ld+json">{json.dumps(person, indent=2)}</script>"""


def render_nav(data: dict) -> str:
    profile = data["profile"]
    links = data["nav"]

    desktop = "".join(
        f'<li><a class="nav__link" data-nav-link href="{esc(item["href"])}">'
        f"{esc(item['label'])}</a></li>"
        for item in links
    )
    drawer = "".join(
        f'<a href="{esc(item["href"])}">{esc(item["label"])}'
        f'<span>{index + 1:02d}</span></a>'
        for index, item in enumerate(links)
    )

    return f"""<header class="nav">
  <div class="shell nav__inner">
    <a class="wordmark" href="#top" aria-label="{esc(profile['name'])} — back to top">
      {wordmark_svg()}
      <span>{esc(profile['wordmark'])}</span>
    </a>

    <nav aria-label="Sections">
      <ul class="nav__list">{desktop}</ul>
    </nav>

    <a class="btn btn--primary btn--sm nav__cta" href="#contact">Get in touch</a>

    <button class="nav__toggle" type="button" data-nav-toggle
            aria-expanded="false" aria-controls="nav-drawer">
      <span data-nav-toggle-text>Menu</span>
      <span class="nav__toggle-bars" aria-hidden="true">
        <span></span><span></span><span></span>
      </span>
    </button>
  </div>
</header>

<div class="drawer" id="nav-drawer" hidden>
  <nav aria-label="Sections, mobile">
    <div class="drawer__list">{drawer}</div>
  </nav>
  <div class="drawer__foot">
    <a class="btn btn--primary" href="mailto:{esc(profile['email'])}">Email me</a>
    <a class="btn btn--secondary" href="{esc(profile['cv']['file'])}" download>
      {esc(profile['cv']['label'])}
    </a>
  </div>
</div>"""


def render_hero(data: dict) -> str:
    profile = data["profile"]
    snap = data["snapshot"]

    intro = "".join(f"<p>{esc(p)}</p>" for p in profile["intro"])

    link_items = "".join(
        f'<a href="{esc(link["url"])}"'
        + (
            ' target="_blank" rel="noopener noreferrer"'
            if link["url"].startswith("http")
            else ""
        )
        + f'>{esc(link["label"])} <span class="mono muted">{esc(link["handle"])}</span></a>'
        for link in profile["links"]
    )

    snap_items = "".join(
        f"""<div class="snapshot__item">
      <span class="snapshot__key label">{esc(item['key'])}</span>
      <p class="snapshot__value">{esc(item['value'])}</p>
      <p class="snapshot__detail">{esc(item['detail'])}</p>
    </div>"""
        for item in snap["items"]
    )

    focus = "".join(f'<li class="tag tag--accent">{esc(f)}</li>' for f in snap["focus"])

    return f"""<section class="hero" id="top" aria-labelledby="hero-name">
  <div class="shell">
    <div class="hero__grid">
      <div class="hero__meta">
        <span class="label">{esc(profile['location'])}</span>
        <span class="badge-current">Open to research roles</span>
      </div>

      <div class="hero__main">
        <p class="label hero__name" id="hero-eyebrow">Bioinformatics · Machine learning</p>
        <h1 class="display" id="hero-name">{esc(profile['name'])}</h1>
        <p class="h2 hero__headline">{esc(profile['headline'])}</p>
        <p class="label" style="margin-bottom:var(--s-5)">{esc(profile['subheadline'])}</p>

        <div class="hero__intro prose">{intro}</div>

        <div class="hero__actions">
          <a class="btn btn--primary" href="#projects">Explore my work {arrow_svg()}</a>
          <a class="btn btn--secondary" href="#contact">Get in touch</a>
          <a class="btn btn--secondary" href="{esc(profile['cv']['file'])}" download>
            {esc(profile['cv']['label'])}
          </a>
        </div>

        <div class="hero__links">{link_items}</div>
      </div>

      <div class="hero__aside">{hero_figure()}</div>
    </div>

    <div style="margin-top:clamp(2.5rem,6vw,5rem)">
      <h2 class="label" id="snapshot-heading" style="margin-bottom:var(--s-4)">
        {esc(snap['label'])}
      </h2>
      <div class="snapshot" role="group" aria-labelledby="snapshot-heading">{snap_items}</div>
      <div class="focus-row">
        <span class="label">Focus areas</span>
        <ul class="tags">{focus}</ul>
      </div>
    </div>
  </div>
</section>"""


def render_about(data: dict) -> str:
    about = data["about"]
    body = "".join(f"<p>{esc(p)}</p>" for p in about["paragraphs"])
    return f"""<section class="section" id="about" aria-labelledby="about-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">01</span>
        <span class="label">{esc(about['label'])}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="about-heading">{esc(about['heading'])}</h2>
      </div>
    </header>
    <div class="about__grid">
      <div class="about__body prose">{body}</div>
    </div>
  </div>
</section>"""


def render_experience(data: dict) -> str:
    exp = data["experience"]
    entries = []

    for item in exp["items"]:
        bullets = "".join(f"<li>{esc(b)}</li>" for b in item["bullets"])
        note = (
            f'<p class="entry__note">{esc(item["note"])}</p>' if item.get("note") else ""
        )
        badge = (
            '<span class="badge-current">Current</span>' if item.get("current") else ""
        )
        where = (
            f'<span class="entry__type">{esc(item["location"])}</span>'
            if item.get("location")
            else ""
        )
        entries.append(
            f"""<article class="entry">
      <div class="entry__when">
        <span class="entry__period">{esc(item['period'])}</span>
        <span class="entry__type">{esc(item['type'])}</span>
        {where}
        {badge}
      </div>
      <div class="entry__what">
        <h3 class="h3 entry__role">{esc(item['role'])}</h3>
        <p class="entry__org">{esc(item['org'])}</p>
        <ul class="entry__bullets">{bullets}</ul>
        {tags(item.get('tools', []))}
        {note}
      </div>
    </article>"""
        )

    return f"""<section class="section section--sunk" id="experience"
         aria-labelledby="experience-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">02</span>
        <span class="label">{esc(exp['label'])}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="experience-heading">{esc(exp['heading'])}</h2>
      </div>
    </header>
    <div class="timeline">{join(entries)}</div>
  </div>
</section>"""


def render_pipeline(stages: list[str], title: str) -> str:
    items = "".join(
        f'<li class="pipeline__stage"><span>{esc(stage)}</span></li>' for stage in stages
    )
    return f"""<figure class="project__figure">
      <figcaption class="diagram-caption">Workflow</figcaption>
      <ol class="pipeline" aria-label="Workflow stages for {esc(title)}">{items}</ol>
    </figure>"""


def render_projects(data: dict) -> str:
    projects = data["projects"]
    cards = []

    for index, item in enumerate(projects["items"], start=1):
        outputs = item.get("outputs") or []
        if outputs:
            blocks = []
            for o in outputs:
                href = o.get("url") or (
                    f"https://doi.org/{o['doi']}" if o.get("doi") else ""
                )
                title = (
                    f'<a class="output__title link" href="{esc(href)}" target="_blank" '
                    f'rel="noopener noreferrer">{esc(o["label"])}</a>'
                    if href
                    else f'<p class="output__title">{esc(o["label"])}</p>'
                )
                blocks.append(
                    f"""<div class="output">
            {title}
            <p class="mono" style="font-size:var(--t-micro);color:var(--ink-muted)">
              {esc(o['venue'])} · {esc(o['status'])}
            </p>
          </div>"""
                )
            output_html = '<div class="outputs">' + "".join(blocks) + "</div>"
        else:
            output_html = (
                '<p class="muted" style="font-size:var(--t-small)">'
                "No associated publication.</p>"
            )

        cards.append(
            f"""<article class="project" id="{esc(item['id'])}">
      <div class="project__top">
        <div class="project__id">
          <span class="project__index">P{index:02d}</span>
          {glyph(item['id'])}
        </div>

        <div class="project__head">
          <div class="project__meta">
            <span class="project__kind">{esc(item['kind'])}</span>
            <span class="project__period">{esc(item['period'])}</span>
            <span class="{status_class(item['status'])}">{esc(item['status'])}</span>
          </div>
          <h3 class="h3 project__title">{esc(item['title'])}</h3>
          <p class="project__summary">{esc(item['summary'])}</p>
          {tags(item['tools'], 'project__tags')}
        </div>

        {render_pipeline(item['pipeline'], item['title'])}
      </div>

      <details class="project__details">
        <summary class="project__toggle">
          <span>Read the full write-up</span>
          <span class="project__toggle-icon" aria-hidden="true"></span>
        </summary>
        <div class="project__body">
          <div class="detail-block detail-block--wide">
            <span class="detail-block__label label">The problem</span>
            <p>{esc(item['problem'])}</p>
          </div>
          <div class="detail-block">
            <span class="detail-block__label label">My contribution</span>
            <p>{esc(item['contribution'])}</p>
          </div>
          <div class="detail-block">
            <span class="detail-block__label label">Domain</span>
            <p>{esc(item['domain'])}</p>
          </div>
          <div class="detail-block">
            <span class="detail-block__label label">Tools &amp; methods</span>
            {tags(item['tools'])}
          </div>
          <div class="detail-block">
            <span class="detail-block__label label">Research output</span>
            {output_html}
          </div>
        </div>
      </details>
    </article>"""
        )

    return f"""<section class="section" id="projects" aria-labelledby="projects-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">03</span>
        <span class="label">{esc(projects['label'])}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="projects-heading">{esc(projects['heading'])}</h2>
      </div>
    </header>
    <p class="note" style="margin-bottom:clamp(2rem,4vw,3rem)">{esc(projects['note'])}</p>
    <div class="projects">{join(cards)}</div>
  </div>
</section>"""


def render_authors(authors: list[str], me: str) -> str:
    """Author list in published order, with the site owner's name emphasised."""
    if not authors:
        return ""
    parts = [
        f'<strong class="pub__me">{esc(name)}</strong>' if name == me else esc(name)
        for name in authors
    ]
    return f'<p class="pub__authors">{", ".join(parts)}</p>'


def render_publications(data: dict) -> str:
    pubs = data["publications"]
    me = data["profile"]["name"]
    total = sum(len(group["items"]) for group in pubs["groups"])
    groups = []

    for group in pubs["groups"]:
        rows = []
        for item in group["items"]:
            meta = []
            authors = render_authors(item.get("authors") or [], me)
            if authors:
                meta.append(authors)
            href = item.get("url") or (
                f"https://doi.org/{item['doi']}" if item.get("doi") else ""
            )
            doi = (
                f'<a class="btn btn--ghost" href="{esc(href)}" '
                f'target="_blank" rel="noopener noreferrer">View paper {arrow_svg()}</a>'
                f'<span class="pub__doi mono">doi:{esc(item["doi"])}</span>'
                if href
                else '<span class="mono" style="font-size:var(--t-micro);'
                'color:var(--ink-faint)">DOI not recorded</span>'
            )
            project_link = (
                f'<a class="btn btn--ghost" href="#{esc(item["project"])}">'
                f"See the project {arrow_svg()}</a>"
                if item.get("project")
                else ""
            )
            rows.append(
                f"""<article class="pub">
        <p class="pub__year mono">{esc(item['year'])}</p>
        <div class="pub__body">
          <h4 class="pub__title">{esc(item['title'])}</h4>
          {join(meta)}
          <p class="pub__venue"><cite>{esc(item['venue'])}</cite></p>
          <div class="pub__foot">
            <span class="{status_class(item['status'])}">{esc(item['status'])}</span>
            {doi}
            {project_link}
          </div>
        </div>
      </article>"""
            )

        groups.append(
            f"""<div class="pub-group">
      <div class="pub-group__head">
        <h3 class="h3">{esc(group['name'])}</h3>
        <span class="pub-group__count">{len(group['items']):02d}</span>
      </div>
      {join(rows)}
    </div>"""
        )

    return f"""<section class="section section--sunk" id="publications"
         aria-labelledby="publications-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">04</span>
        <span class="label">{esc(pubs['label'])} · {total:02d}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="publications-heading">{esc(pubs['heading'])}</h2>
      </div>
    </header>
    {join(groups)}
    <p class="note" style="margin-top:clamp(2rem,4vw,3rem)">{esc(pubs['note'])}</p>
  </div>
</section>"""


def render_skills(data: dict) -> str:
    skills = data["skills"]
    groups = "".join(
        f"""<div class="skill-group">
      <h3 class="skill-group__name">{esc(group['name'])}</h3>
      <div class="skill-group__items">{tags(group['items'])}</div>
    </div>"""
        for group in skills["groups"]
    )
    return f"""<section class="section" id="skills" aria-labelledby="skills-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">05</span>
        <span class="label">{esc(skills['label'])}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="skills-heading">{esc(skills['heading'])}</h2>
      </div>
    </header>
    <div class="skills">{groups}</div>
    <p class="note" style="margin-top:clamp(1.5rem,3vw,2.5rem)">{esc(skills['note'])}</p>
  </div>
</section>"""


def render_interests(data: dict) -> str:
    interests = data["interests"]
    items = "".join(
        f"""<article class="interest">
      <h3 class="interest__name">{esc(item['name'])}</h3>
      <p class="interest__detail">{esc(item['detail'])}</p>
    </article>"""
        for item in interests["items"]
    )
    return f"""<section class="section section--sunk" id="interests"
         aria-labelledby="interests-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">06</span>
        <span class="label">{esc(interests['label'])}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="interests-heading">{esc(interests['heading'])}</h2>
      </div>
    </header>
    <div class="interests">{items}</div>
    <p class="note" style="margin-top:clamp(2rem,4vw,3rem)">{esc(interests['note'])}</p>
  </div>
</section>"""


def render_education(data: dict) -> str:
    edu = data["education"]

    degrees = "".join(
        f"""<div class="edu-item">
      <p class="edu-item__name">{esc(d['degree'])}</p>
      <p class="edu-item__org">{esc(d['org'])}</p>
      <p class="edu-item__detail">{esc(d['detail'])}</p>
      <span class="edu-item__period">{esc(d['period'])}</span>
    </div>"""
        for d in edu["degrees"]
    )

    certs = "".join(
        f"""<div class="edu-item">
      <p class="edu-item__name">{esc(c['name'])}</p>
      <p class="edu-item__org">{esc(c['org'])}</p>
      <span class="edu-item__period">{esc(c['period'])}</span>
    </div>"""
        for c in edu["certifications"]
    )

    return f"""<section class="section" id="education" aria-labelledby="education-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">07</span>
        <span class="label">{esc(edu['label'])}</span>
      </div>
      <div class="section-head__title">
        <h2 class="h2" id="education-heading">Degree, and the coursework around it.</h2>
      </div>
    </header>
    <div class="edu-grid">
      <div class="edu-col edu-col--degrees">
        <div class="edu-col__head"><h3 class="h3">Education</h3></div>
        {degrees}
      </div>
      <div class="edu-col edu-col--certs">
        <div class="edu-col__head"><h3 class="h3">Certifications</h3></div>
        {certs}
      </div>
    </div>
  </div>
</section>"""


def render_contact(data: dict) -> str:
    contact = data["contact"]
    profile = data["profile"]

    channels = [
        f"""<div class="channel">
      <span class="channel__key">Email</span>
      <a class="channel__val" href="mailto:{esc(profile['email'])}">{esc(profile['email'])}</a>
    </div>"""
    ]
    for link in profile["links"]:
        if link["label"].lower() == "email":
            continue
        channels.append(
            f"""<div class="channel">
      <span class="channel__key">{esc(link['label'])}</span>
      <a class="channel__val" href="{esc(link['url'])}" target="_blank"
         rel="noopener noreferrer">{esc(link['handle'])}</a>
    </div>"""
        )
    if profile.get("phone"):
        channels.append(
            f"""<div class="channel">
      <span class="channel__key">Phone</span>
      <a class="channel__val" href="tel:{esc(profile['phone'].replace(' ', ''))}">
        {esc(profile['phone'])}</a>
    </div>"""
        )
    channels.append(
        f"""<div class="channel">
      <span class="channel__key">Location</span>
      <span class="channel__val">{esc(profile['location'])}</span>
    </div>"""
    )
    channels.append(
        f"""<div class="channel">
      <span class="channel__key">CV</span>
      <a class="channel__val" href="{esc(profile['cv']['file'])}" download>PDF</a>
    </div>"""
    )

    return f"""<section class="contact" id="contact" aria-labelledby="contact-heading">
  <div class="shell">
    <header class="section-head">
      <div class="section-head__label">
        <span class="section-head__num">08</span>
        <span class="label">{esc(contact['label'])}</span>
      </div>
    </header>
    <div class="contact__grid">
      <div class="contact__main">
        <h2 class="contact__heading" id="contact-heading">{esc(contact['heading'])}</h2>
        <p class="contact__body">{esc(contact['body'])}</p>
        <div class="contact__actions">
          <a class="btn btn--primary" href="mailto:{esc(profile['email'])}">
            {esc(contact['cta'])} {arrow_svg()}
          </a>
          <button class="btn btn--secondary" type="button"
                  data-copy="{esc(profile['email'])}" data-copy-status="copy-status">
            Copy email address
          </button>
          <a class="btn btn--secondary" href="{esc(profile['cv']['file'])}" download>
            {esc(profile['cv']['label'])}
          </a>
        </div>
        <p class="copy-state" id="copy-status" role="status" aria-live="polite"></p>
      </div>
      <div class="contact__channels">{join(channels)}</div>
    </div>
  </div>
</section>"""


def render_footer(data: dict) -> str:
    profile = data["profile"]
    links = "".join(
        f'<a href="{esc(link["url"])}"'
        + (
            ' target="_blank" rel="noopener noreferrer"'
            if link["url"].startswith("http")
            else ""
        )
        + f">{esc(link['label'])}</a>"
        for link in profile["links"]
    )
    return f"""<footer class="footer">
  <div class="shell footer__inner">
    <p>&copy; <span data-year>2026</span> {esc(profile['name'])}</p>
    <div class="footer__links">
      {links}
      <a href="{esc(profile['cv']['file'])}" download>CV</a>
      <a href="#top">Back to top</a>
    </div>
  </div>
</footer>"""


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #


def render_index(data: dict) -> str:
    return f"""<!doctype html>
<html lang="{esc(data['site']['locale'])}">
<head>
{render_head(data)}
  <script src="assets/main.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
{render_nav(data)}
  <main id="main">
{render_hero(data)}
{render_about(data)}
{render_experience(data)}
{render_projects(data)}
{render_publications(data)}
{render_skills(data)}
{render_interests(data)}
{render_education(data)}
{render_contact(data)}
  </main>
{render_footer(data)}
</body>
</html>
"""


def render_404(data: dict) -> str:
    profile = data["profile"]
    return f"""<!doctype html>
<html lang="{esc(data['site']['locale'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page not found — {esc(profile['name'])}</title>
  <meta name="description" content="That page does not exist on {esc(profile['name'])}'s portfolio.">
  <meta name="robots" content="noindex">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <header class="nav">
    <div class="shell nav__inner">
      <a class="wordmark" href="index.html">
        {wordmark_svg()}
        <span>{esc(profile['wordmark'])}</span>
      </a>
      <a class="btn btn--primary btn--sm" href="index.html#contact">Get in touch</a>
    </div>
  </header>
  <main class="shell notfound">
    <p class="notfound__code">Error 404</p>
    <h1 class="h1 notfound__title">That page does not exist.</h1>
    <p class="lead notfound__body">
      The link may be out of date. Everything on this site lives on one page —
      start from the top, or jump straight to the projects.
    </p>
    <div class="hero__actions">
      <a class="btn btn--primary" href="index.html">Back to the homepage {arrow_svg()}</a>
      <a class="btn btn--secondary" href="index.html#projects">Projects</a>
    </div>
  </main>
{render_footer(data)}
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #


def check(data: dict) -> list[str]:
    """Light content validation so a typo in content.json fails loudly."""
    problems: list[str] = []
    ids = [p["id"] for p in data["projects"]["items"]]
    if len(ids) != len(set(ids)):
        problems.append("Duplicate project ids in content.json")
    for group in data["publications"]["groups"]:
        for item in group["items"]:
            ref = item.get("project")
            if ref and ref not in ids:
                problems.append(f"Publication references unknown project id: {ref}")
    for item in data["nav"]:
        if not item["href"].startswith("#"):
            problems.append(f"Nav href is not an in-page anchor: {item['href']}")
    cv = ROOT / data["profile"]["cv"]["file"]
    if not cv.exists():
        problems.append(f"CV file missing: {data['profile']['cv']['file']}")
    return problems


def build(serve: bool = False) -> int:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))

    problems = check(data)
    for problem in problems:
        print(f"  ! {problem}", file=sys.stderr)

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")
    (ASSETS / "og-image.svg").write_text(og_image_svg(data["profile"]), encoding="utf-8")
    png = og_image_png(data["profile"], ASSETS / "og-image.png")
    (ROOT / "index.html").write_text(render_index(data), encoding="utf-8")
    (ROOT / "404.html").write_text(render_404(data), encoding="utf-8")

    size = (ROOT / "index.html").stat().st_size
    print(f"  built index.html  ({size / 1024:.1f} KB)")
    print("  built 404.html")
    print("  built assets/favicon.svg, assets/og-image.svg")
    if png:
        kb = (ASSETS / "og-image.png").stat().st_size / 1024
        print(f"  built assets/og-image.png  ({kb:.0f} KB)")
    else:
        print("  ! Pillow not installed — assets/og-image.png not regenerated.")

    if not data["site"].get("url"):
        print(
            "\n  ! site.url is empty in content.json.\n"
            "    Canonical, og:url and og:image are omitted until you set it,\n"
            "    so shared links will show no preview card. Set it to your\n"
            "    live origin and rebuild before deploying."
        )
    if problems:
        print(f"\n  {len(problems)} content problem(s) above — site still written.")
        return 1

    if serve:
        import http.server
        import socketserver

        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("127.0.0.1", 8000), handler) as httpd:
            print("\n  serving http://localhost:8000  (Ctrl+C to stop)")
            httpd.serve_forever()

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the portfolio site.")
    parser.add_argument("--serve", action="store_true", help="serve on :8000 after building")
    args = parser.parse_args()
    raise SystemExit(build(serve=args.serve))

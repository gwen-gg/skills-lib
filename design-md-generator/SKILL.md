---
name: design-md-generator
description: Crawl a website URL and generate a DESIGN.md file that conforms to the Google Stitch DESIGN.md specification. The output captures a brand's design language — colors, typography, spacing, border-radius, components, layout principles, and do's/don'ts — extracted by inspecting the live site's CSS and markup. Use this skill whenever the user wants to create a DESIGN.md from a website, reverse-engineer a brand's design system, generate a Stitch-compatible design spec, extract a site's visual language, or when they mention "DESIGN.md", "design spec from URL", "brand design tokens", "Stitch design file", or "crawl a website for design". Even if the user just pastes a URL and mentions design or theming, trigger this skill.
---

# DESIGN.md Generator

Crawl a website and produce a fully-structured `DESIGN.md` file following the [Google Stitch specification](https://stitch.withgoogle.com/docs/design-md/specification/).

## Overview

The process has 4 phases:
1. **Crawl** — fetch HTML + computed CSS from the target URL
2. **Extract** — identify design tokens (colors, type, spacing, radii)
3. **Map** — derive components and their token references
4. **Write** — output a spec-compliant DESIGN.md

Always read `references/spec-guide.md` before writing the output for exact field names, token syntax (`{colors.x}`), and YAML structure rules.

---

## Phase 1 — Crawl

Fetch the page with `web_fetch` using `html_extraction_method: markdown`. If the page is JS-rendered and returns little CSS, also try fetching the raw HTML and look for `<style>` tags or `<link rel="stylesheet">` hrefs to fetch separately.

```python
# Pseudo-approach in bash:
# 1. web_fetch the homepage URL
# 2. If CSS links found, web_fetch up to 3 stylesheets
# 3. Optionally web_fetch /about or /pricing to widen component coverage
```

**Key things to capture:**
- `background-color`, `color`, `border-color` values on major elements
- `font-family`, `font-size`, `font-weight`, `line-height`, `letter-spacing` for headings, body, captions, buttons
- `border-radius` values across buttons, cards, inputs
- `padding` and `margin` patterns that recur (→ spacing scale)
- Box-shadow values for elevation hints

If inline CSS is sparse (modern frameworks use utility classes), look for:
- Tailwind config hints (class names like `text-[#hex]`, `bg-[#hex]`)
- CSS custom properties (`--color-*`, `--font-*`)
- Google Fonts or font `@import` statements for font family names

---

## Phase 2 — Extract Design Tokens

### Colors
Collect all unique hex/rgb values. Cluster by role:
- **Primary / Brand** — dominant dark or brand-colored buttons, wordmark
- **Canvas** — page background (usually `#fff` or a near-white)
- **On-primary** — text that sits on the primary color
- **Ink / Ink-strong** — main text color and a slightly lighter variant
- **Body / Body-mid** — paragraph and secondary text
- **Mute / Mute-soft** — placeholder, captions, disabled
- **Hairline** — subtle borders and dividers
- **Accents** — brand accent colors (list each distinctly, e.g. `accent-blue`, `accent-green`)
- **Semantic** — success, warning, error, info (if found)

Name tokens in kebab-case. If a value appears in multiple semantic roles, pick the most dominant one.

### Typography
For each text role (display-xxl → display-xs, eyebrow, body-lg → body-sm, caption, button), capture:
- `fontFamily` — full stack including fallbacks
- `fontSize` — in px
- `fontWeight`
- `lineHeight` — in px
- `letterSpacing` — in px (omit if 0 / normal)

Build a scale from the largest heading found down to captions. Map to the standard token names: `display-xxl`, `display-xl`, `display-lg`, `display-md`, `display-sm`, `display-xs`, `eyebrow-uppercase`, `body-lg`, `body-md`, `body-md-strong`, `body-sm`, `body-sm-strong`, `caption`, `button-md`.

### Spacing
Identify recurring padding / margin values. Fit them into a named scale:
`xxs` (2px) · `xs` (4px) · `sm` (8px) · `md` (12px) · `lg` (16px) · `xl` (20px) · `2xl` (24px) · `3xl` (32px) · `4xl` (48px) · `5xl` (64px)

Round observed values to the nearest common step. Add extra named entries if the site uses an unusual large step.

### Border Radius
Collect unique radius values, map to:
`none` (0px) · `xs` (2px) · `sm` (4px) · `md` (8px) · `lg` (12px) · `xl` (16px) · `2xl` (24px) · `full` (9999px)

---

## Phase 3 — Map Components

For each of the following component types found on the page, record its token references using `{token.name}` syntax:

**Required (if found):**
- `nav-bar` — sticky/top navigation
- `button-primary` — main CTA
- `button-secondary` — ghost/outline CTA
- `card-feature` — content card
- `hero-band` — hero section
- `footer` — page footer
- `text-input` — form field

**Optional (add if clearly present):**
- `button-text-arrow`, `button-icon-circular`
- `card-pricing`, `card-feature-dark`, `card-testimonial`
- `hero-band-dark`, `content-band`
- `badge`, `badge-info`, `tag`, `pill`
- `nav-link`, `nav-dropdown`
- `modal-card`, `drawer`
- `tab-bar`, `sidebar`
- Any brand-signature components unique to this site

**Example component block:**
```yaml
button-primary:
  backgroundColor: "{colors.primary}"
  textColor: "{colors.on-primary}"
  typography: "{typography.button-md}"
  rounded: "{rounded.sm}"
  padding: "{spacing.md} {spacing.xl}"
```

Also derive 10 `ex-*` example components from the standard set:
`ex-pricing-tier`, `ex-pricing-tier-featured`, `ex-product-selector`, `ex-cart-drawer`, `ex-app-shell-row`, `ex-data-table-cell`, `ex-auth-form-card`, `ex-modal-card`, `ex-empty-state-card`, `ex-toast`

Each `ex-*` must include a `description:` field, and all properties must reference brand tokens.

---

## Phase 4 — Write DESIGN.md

Output a single Markdown file. Structure:

```
---
version: alpha
name: <Brand-Name>-design-analysis
description: <One rich paragraph capturing the brand's visual voice>

colors:
  primary: "#hex"
  on-primary: "#hex"
  ink: "#hex"
  ...

typography:
  display-xxl:
    fontFamily: ...
    fontSize: ...
    fontWeight: ...
    lineHeight: ...
    letterSpacing: ... (omit if 0)
  ...

rounded:
  none: 0px
  sm: 4px
  ...

spacing:
  xxs: 2px
  xs: 4px
  ...

components:
  nav-bar:
    ...
  button-primary:
    ...
  ...
  # ─── Examples (illustrative) ───
  ex-pricing-tier:
    description: "..."
    ...
---

## Overview
<2–4 paragraph brand voice narrative. Cover: color philosophy, typography voice, shape language, elevation/depth approach, key brand signatures.>

**Key Characteristics:**
- <5–8 bullet points describing the most distinctive brand patterns>

## Colors

### Brand & Accent
<Named color descriptions with token references and hex values>

### Surface
...

### Text
...

### Semantic
...

## Typography

### Font Family
<Description of the typeface(s) — proprietary vs open source, weights used, special variants>

### Hierarchy
| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xxl}` | ...px | ... | ...px | ...px | ... |
...

### Principles
- <3–5 typographic principles observed from the site>

### Note on Font Substitutes
<Open-source alternatives if brand uses proprietary fonts>

## Layout

### Spacing System
- <Description of the base unit and token scale>

### Grid & Container
- <Column count, max-width, gutter observations>

### Responsive Strategy

#### Breakpoints
| Name | Width | Key Changes |
|---|---|---|
...

#### Touch Targets
<Observed button heights and WCAG compliance notes>

#### Collapsing Strategy
- <How nav, grids, and content collapse on mobile>

## Elevation & Depth
| Level | Treatment | Use |
|---|---|---|
| Level 0 — Flat | ... | ... |
...

## Shapes

### Border Radius Scale
| Token | Value | Use |
|---|---|---|
...

## Components

### Buttons
<Named description + token breakdown for each button variant>

### Cards & Containers
...

### Inputs & Forms
...

### Navigation
...

### Signature Components
<Any distinctive brand components unique to this site>

## Do's and Don'ts

### Do
- <5–8 affirmative brand rules derived from the site>

### Don't
- <5–8 prohibitions — what breaks the brand language>
```

---

## Quality Rules

- **Never invent** token values not observed on the site. If you can't determine a value, note `# TO_FILL` inline.
- **All component properties** must reference `{token.name}` syntax, not raw hex values.
- **Typography tokens** must always include `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`. Add `letterSpacing` only when non-zero.
- **Description field** (YAML frontmatter) must be a single paragraph — no bullet points.
- **ex-\* components** must all have a `description:` field.
- The `## Do's and Don'ts` section must contain at least 5 items in each list.
- The narrative sections (Overview, Colors, Typography, etc.) must be written prose — not bullet dumps.

---

## Output

Save the file as `DESIGN.md` in `/mnt/user-data/outputs/` and present it to the user.

If important tokens couldn't be determined from the crawl, list them at the end as a `## Missing / TO_FILL` section so the user knows what to verify manually.

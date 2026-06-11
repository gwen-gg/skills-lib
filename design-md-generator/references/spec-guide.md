# DESIGN.md Specification Reference

Source: https://stitch.withgoogle.com/docs/design-md/specification/

This file is the authoritative spec guide for generating valid DESIGN.md files. Read it before writing the output block.

---

## File Structure

A DESIGN.md file has two parts:

1. **YAML frontmatter** (between `---` delimiters) — machine-readable tokens
2. **Markdown body** — human-readable narrative and tables

The frontmatter defines the single source of truth. The body explains and documents it.

---

## YAML Frontmatter Fields

### Required top-level keys

```yaml
version: alpha
name: <brand-name>-design-analysis
description: <one paragraph, no bullets>
colors: { ... }
typography: { ... }
rounded: { ... }
spacing: { ... }
components: { ... }
```

---

### colors

All color values must be hex strings.

**Canonical required keys:**
```yaml
colors:
  primary:        # Main brand/CTA color
  on-primary:     # Text that sits on primary background
  ink:            # Default text color
  ink-strong:     # Heavier emphasis text
  body:           # Paragraph text
  body-mid:       # Secondary/footer text
  mute:           # De-emphasized text
  mute-soft:      # Placeholder / fine print
  hairline:       # Thin border / divider
  canvas:         # Page background
```

**Optional accent keys** (add as needed, prefix with `accent-`):
```yaml
  accent-blue:
  accent-green:
  accent-red:
  accent-yellow:
  accent-purple:
  accent-orange:
  accent-pink:
  # etc.
```

**Optional semantic keys:**
```yaml
  success:
  warning:
  error:
  info:
```

---

### typography

Each typography token is a nested object:

```yaml
typography:
  token-name:
    fontFamily: "Font Name, fallback, system-ui, sans-serif"
    fontSize: 80px
    fontWeight: 600
    lineHeight: 83.2px
    letterSpacing: -0.8px   # omit if 0 / normal
```

**Standard token names (in scale order):**
```
display-xxl       # Hero headline
display-xl        # Sub-hero
display-lg        # Section headline
display-md        # Card headline
display-sm        # Sub-section
display-xs        # Micro heading
eyebrow-uppercase # Uppercase label above sections
eyebrow-uppercase-sm
body-lg           # Lead paragraph
body-md           # Default body
body-md-strong    # Bold inline body
body-sm           # Secondary body
body-sm-strong    # Bold caption / nav
caption           # Badge/tag labels
caption-mono      # Code / mono captions
button-md         # Button labels
button-sm         # Small button labels (optional)
label-lg          # Form labels (optional)
label-sm          # Small form labels (optional)
```

---

### rounded

```yaml
rounded:
  none: 0px
  xs: 2px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  2xl: 24px
  full: 9999px
```

Only include values actually used on the site. Always include `none` and `full` if observed.

---

### spacing

```yaml
spacing:
  xxs: 2px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px
  4xl: 48px
  5xl: 64px
  6xl: 80px
  7xl: 96px
  8xl: 128px
```

Only include steps that appear in the site's actual spacing system.

---

### components

Each component is a nested object. **All property values must use token references** (`{colors.x}`, `{typography.x}`, `{rounded.x}`, `{spacing.x}`), never raw hex or px values.

**Component property keys:**
```yaml
components:
  component-name:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: "{spacing.md} {spacing.lg}"
    # Additional properties as needed:
    activeIndicator: "{colors.primary}"
    item-divider: "{colors.hairline}"
    headerBackground: "{colors.canvas}"
    headerTypography: "{typography.caption}"
    bodyTypography: "{typography.body-sm}"
    cellPadding: "{spacing.md} {spacing.lg}"
    rowBorder: "{colors.hairline}"
    captionTypography: "{typography.body-sm}"
```

**Ex- components** (required, always 10):
```yaml
  ex-pricing-tier:
    description: "Default pricing tier card"
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.hairline}"
    rounded: "{rounded.md}"
    padding: "{spacing.3xl}"
  ex-pricing-tier-featured:
    description: "Featured/highlighted tier"
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.3xl}"
  ex-product-selector:
    description: "What's Included / feature summary card"
    backgroundColor: "{colors.canvas}"
    rounded: "{rounded.md}"
    padding: "{spacing.3xl}"
  ex-cart-drawer:
    description: "Subscription summary drawer"
    backgroundColor: "{colors.canvas}"
    rounded: "{rounded.md}"
    padding: "{spacing.2xl}"
    item-divider: "{colors.hairline}"
  ex-app-shell-row:
    description: "Sidebar nav row — active state uses primary"
    backgroundColor: "{colors.canvas}"
    activeIndicator: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md} {spacing.lg}"
  ex-data-table-cell:
    description: "Data table th + td chrome"
    headerBackground: "{colors.canvas}"
    headerTypography: "{typography.caption}"
    bodyTypography: "{typography.body-sm}"
    cellPadding: "{spacing.md} {spacing.lg}"
    rowBorder: "{colors.hairline}"
  ex-auth-form-card:
    description: "Sign-in / sign-up card"
    backgroundColor: "{colors.canvas}"
    rounded: "{rounded.md}"
    padding: "{spacing.3xl}"
  ex-modal-card:
    description: "Modal dialog surface"
    backgroundColor: "{colors.canvas}"
    rounded: "{rounded.md}"
    padding: "{spacing.3xl}"
  ex-empty-state-card:
    description: "Empty state frame"
    backgroundColor: "{colors.canvas}"
    rounded: "{rounded.md}"
    padding: "{spacing.3xl}"
    captionTypography: "{typography.body-md}"
  ex-toast:
    description: "Toast notification"
    backgroundColor: "{colors.canvas}"
    rounded: "{rounded.md}"
    padding: "{spacing.md} {spacing.lg}"
    typography: "{typography.body-sm}"
```

---

## Token Reference Syntax

Inside component values, always use curly-brace token references:

| Reference | Points to |
|---|---|
| `{colors.primary}` | The `primary` key in the `colors` section |
| `{typography.body-md}` | The `body-md` key in the `typography` section |
| `{rounded.sm}` | The `sm` key in the `rounded` section |
| `{spacing.lg}` | The `lg` key in the `spacing` section |

Shorthand padding using two tokens: `"{spacing.md} {spacing.lg}"` (vertical horizontal).

---

## Markdown Body Sections (required)

After the closing `---`, include these sections in order:

1. `## Overview` — rich narrative, then `**Key Characteristics:**` bullet list (5–8 bullets)
2. `## Colors` — subsections: Brand & Accent / Surface / Text / Semantic
3. `## Typography` — subsections: Font Family / Hierarchy (table) / Principles / Note on Font Substitutes
4. `## Layout` — subsections: Spacing System / Grid & Container / Responsive Strategy (with Breakpoints table, Touch Targets, Collapsing Strategy, Image Behavior)
5. `## Elevation & Depth` — table of elevation levels + decorative depth notes
6. `## Shapes` — Border Radius Scale table
7. `## Components` — subsections mirroring component groups (Buttons / Cards / Inputs / Navigation / Signature Components / Examples)
8. `## Do's and Don'ts` — `### Do` and `### Don't` lists (5+ items each)

---

## Common Mistakes to Avoid

- ❌ Raw hex values in component properties → use `{colors.x}` instead
- ❌ Inventing colors not found on the site → mark as `# TO_FILL`
- ❌ Missing `letterSpacing` when it IS non-zero → always include if present
- ❌ `ex-*` components without a `description:` field
- ❌ Bullet points in the YAML `description` field
- ❌ Duplicate color tokens for semantically identical colors
- ❌ Using pixel values in component padding → use `{spacing.x} {spacing.y}`
- ❌ Forgetting `on-primary` — it's always required
- ❌ Using font-weight 700+ if the site never uses it

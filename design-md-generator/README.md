# design-md-generator

An Agent Skill that crawls any website URL and reverse-engineers its visual design language into a structured `DESIGN.md` file conforming to the [Google Stitch specification](https://stitch.withgoogle.com/docs/design-md/specification/). Given a URL, it fetches the page HTML and stylesheets, extracts design tokens (colors, typography, spacing, border-radius), maps them to named components using token references, and outputs a complete spec with both a machine-readable YAML frontmatter block and a human-readable narrative — covering color philosophy, typographic hierarchy, layout grid, elevation, responsive strategy, and a do's/don'ts guide.

---
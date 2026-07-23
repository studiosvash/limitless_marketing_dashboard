# Premier Staff — Design System

A premium executive event-staffing brand. This system is reconstructed
from the **"Premier Staff – Executive"** Figma file (2 pages, 100 frames).

> **Source:** Figma file `Premier Staff -  Executive.fig` (mounted as a
> read-only virtual filesystem during system creation — `/Page-1-NAV/`
> for marketing pages and components, `/AD-Pages/` for ads + city-targeted
> landing pages).

---

## Company

Premier Staff is a US-based **premier event staffing agency** that
provides "professional, highly trained event staff in every major US
city, offering premium solutions for corporate events, celebrations, and
more." The brand markets two product surfaces:

1. **Events** — bartenders, brand ambassadors, models, catering,
   crowd management, street teams (single-event hire).
2. **Enterprise** — long-term, large-scale staffing for venues,
   stadiums, conventions, festivals, ongoing brand activations.

Cities served (21+): NYC, LA, San Francisco, San Diego, San Jose,
Seattle, Phoenix, Las Vegas, Salt Lake City, Denver, Dallas, Houston,
Austin, Chicago, Atlanta, Charlotte, Nashville, Miami, Orlando, Boston,
Washington.

Notable clients in the trustedby strip include Netflix, Spotify,
Converse, Stagecoach, and others.

---

## Index — what's in this folder

| File / folder | What it is |
|---|---|
| `README.md` | This file. Brand context, content & visual fundamentals, iconography. |
| `SKILL.md`  | Agent-skill manifest. Read first if invoked as a skill. |
| `colors_and_type.css` | All raw + semantic CSS variables, type scale, button base. |
| `assets/`   | Logos (combined SVG), Trustedby client logos, hero & ambassador photography. |
| `preview/`  | Small HTML cards that populate the Design System tab. |
| `ui_kits/marketing-website/` | Pixel-fidelity recreation of the marketing site (light & dark themes). |

---

## CONTENT FUNDAMENTALS

### Voice
Confident, refined, **service-led**. The brand sells access to a vetted
human team — every line of copy reinforces *"we handle this so you can
host."* Premier writes from a posture of expertise, not enthusiasm.
Light marketing energy, no hype.

### Tone & POV
- **First-person plural — "we provide", "our ambassadors", "our team"** —
  paired with second-person — **"your event", "your brand"**. Always
  positions the company as a partner *to* the client, never as a
  marketplace.
- Sentences are short to medium. Subordinate clauses are common in body
  copy ("...offering premium solutions for corporate events,
  celebrations, and more.").
- No exclamation marks. No questions in headlines (only in FAQ).

### Casing
- **Hero headlines & section titles**: Title Case with **a final period.**
  ("Executive Staffing for your Premium needs.", "Stress-Free Event
  Staffing.", "Driven by people, powered by Premier."). The trailing
  period is signature — it lands the line like a brochure cut.
- **Buttons & nav**: ALL CAPS. ("HIRE STAFF", "SEE PRICING", "PRICING",
  "CONTACT US", "EVENTS", "ENTERPRISE", "LOCATIONS"). Letter-spacing
  is positive (+0.01em).
- **Eyebrows / category labels**: ALL CAPS, smaller (12px). ("WHERE WE
  WORK", "TRUSTED BY", "AVERAGE CLIENT RATING").
- **Body**: Sentence case, normal punctuation.

### Pronouns & emoji
- "We" / "Our" for Premier; "You" / "Your" for the client. **Never** "I".
- **No emoji** anywhere in product or marketing copy. Stars (★) are
  rendered as **icons**, not unicode.

### Vocabulary
Words that recur and *belong* to the brand:
- **Executive**, **Premier**, **Premium** (always capitalized as brand
  vocabulary, not adjectives).
- **Professional**, **Highly trained**, **Vetted**, **Nationwide**.
- **Ambassadors**, **Street teams**, **Hospitality**, **Service**.
- **Stress-Free**, **Seamless**, **Effortless**, **Transparent**.

Words to **avoid**: "platform", "marketplace", "gig", "app", "tap",
"book online", "AI", "powered by", anything self-congratulatory or
techy. Premier sells people, not software.

### Examples lifted from the Figma
- *"Executive Staffing for your Premium needs."* (Hero, light)
- *"Enterprise Staffing for your Premium needs."* (Hero, dark)
- *"We provide professional, highly trained event staff in every major
  US city, offering premium solutions for corporate events,
  celebrations, and more."* (Hero subhead)
- *"Because Every Guest Deserves a Premier Experience."* (Section title)
- *"Stress-Free Event Staffing."* (Section title)
- *"Transparent Pricing"* / *"21 Cities Nationwide"* (Bento card titles)
- *"Driven by people, powered by Premier."* (Closing manifesto)
- *"Turning Moments Into Memories: Inside the Premier Experience"*
  (Editorial / case-study headline)
- CTA verbs: **HIRE STAFF**, **SEE PRICING**, **CONTACT US**, **HIRE
  EVENT STAFF**, **HIRE OUR TEAM**.

---

## VISUAL FOUNDATIONS

### Color
- **Two primaries: warm-black (`rgb(23,23,18)`) and warm bone-white
  (`rgb(252,251,250)`).** This pairing — never pure `#000` / `#fff` —
  is the entire brand. The black has a faint olive undertone; the white
  has a faint cream undertone. Together they read editorial, not stark.
- **Single accent: gold** (`rgb(181,150,70)`) — used for star ratings
  and very small premium highlights. **Never** as a CTA fill.
- Dark theme swaps to `rgb(18,18,18)` background with `rgb(217,217,217)`
  foreground — used on the Enterprise page and select hero variants.
- A handful of secondary accents (periwinkle blue `rgb(116,130,183)`,
  dusty rose `rgb(209,157,154)`, salmon `rgb(255,156,156)`) appear in
  ad/promo treatments, never in core nav or hero.

### Type
- **Display: Playfair Display** (Bold 700) — every hero headline, every
  section title. Tight leading (line-height ≈ 0.9). On large hero
  centered variants letter-spacing pushes to **+0.15em** for an
  airy, almost couture feel; on left-aligned hero it's tighter at
  **+0.05em**.
- **Body: Roboto** (400 / 500 / 700). Workhorse for nav, buttons, body,
  metadata. Letter-spacing is consistently slightly negative
  (**-0.01em**).
- **Meta / micro: Roboto Medium** at 12px for very small legal / footer
  / chip text (same family as body — kept tight by weight + tracking).
- The mix is a pure **serif-display + sans-body** pairing using just
  two families: Playfair Display + Roboto. No mono, no third UI face.
- Font-substitution note: Figma calls these **"Playfair"** (the
  variable family) and **"Roboto"**. We import **"Playfair Display"**
  and **"Roboto"** from Google Fonts — the closest free equivalents.
  ⚠ **If exact Playfair (variable) files are required, please
  attach them to `fonts/`.**

### Spacing & rhythm
- 4px base. Common stops: 4 / 8 / 12 / 16 / 20 / 24 / 28 / 32 / 48 /
  60 / 80 / 84.
- **84px is the canonical page horizontal padding** (left/right gutters
  on every full-width section). Inner content width is **1272px**
  inside a **1440px** page.
- Vertical section gaps are large — **80–84px** is the default rhythm.

### Backgrounds
- Light: flat warm-white (`bone-200`), occasionally swapped to
  warm-cream (`bone-300`) for an alternating section.
- Dark: flat near-black (`ink-800`) with a **subtle multi-stop linear
  gradient** dropping from `rgba(18,18,18,0.9)` → `rgba(35,35,35,0.9)`
  on the enterprise long page — adds depth without becoming a fashion
  gradient.
- **Imagery is full-bleed inside cards**, not in big hero backgrounds.
  The only true full-bleed photo is the right side of the hero
  (people-photo with rounded corners). No repeating patterns, no
  hand-drawn illustration, no noise textures.

### Imagery vibe
- **Color story is warm and slightly desaturated** — golden-hour light,
  cream-stone architecture, deep blacks. Always feels editorial /
  lifestyle, never stock.
- Subjects are real Premier Staff team members, **always in all-black
  attire**. Confident posed group shots, candid event moments,
  bartender close-ups. Never illustration. Never people on phones.

### Borders
- 1px solid in `var(--border)` (12% black on light, 10% white on dark).
- Strong borders (CTA outline) are 1px in the warm-black.
- The brand uses an **outer ring shadow** (`0 0 0 4px rgba(0,0,0,0.15)`)
  on secondary buttons in lieu of a heavy border — gives a soft
  "halo" focus state.

### Corner radii
- **5px** is the canonical button + nav surface radius.
- **6px** for the hero photo wrapper.
- **12px** for content cards (bento cards, image tiles).
- **2px** for very large editorial sections.
- The brand never uses pill-shape buttons except for circular avatars.

### Cards & elevation
Cards are **flat surfaces with a 12px radius and subtle shadow**:
`0 4px 4px rgba(0,0,0,0.05)`. On hover, gain `0 8px 24px rgba(0,0,0,0.10)`
+ -1px translate. **No colored left-border accents, ever.**

### CTAs
- **Primary**: vertical gradient `rgb(60,60,60) → rgb(23,23,18)` on the
  warm-black, white text, 5px radius, 46px tall. The gradient is subtle
  but real — not a flat fill.
- **Secondary**: transparent, 1px warm-black outline, **`+ 4px outer
  ring shadow` at 15% black**. Same height/radius. On dark theme the
  outline switches to white.
- Buttons sit at the **center or bottom of hero compositions**, not
  in the top-right of the nav. The nav CTA ("CONTACT US") is the only
  exception and uses a flat solid fill.

### Hover & press
- Links: opacity → 0.7, 140ms.
- Primary buttons: shadow grows + 1px lift.
- Press: -1px → 0px, opacity 0.92.
- Cards: shadow grows + 1px lift.
- **No bounces, no spring physics, no scale-up wobble.** Motion is
  short, restrained, business-like.

### Animation
- Default duration **220ms**, ease `cubic-bezier(0.2, 0, 0, 1)`.
- Use only fade + slight translate (≤ 4px). No keyframe loops, no
  scrolljacking, no parallax. The brand's energy comes from the
  photography, not the motion.

### Transparency, blur & overlays
- Nav uses a **20px backdrop blur** with the bone-200 color at full
  opacity — gives a subtle "floating glass" feel on scroll.
- Photo overlays use 2–3 stop gradients dropping from black at 55%
  opacity in the top half to fully transparent — this is how text-on-
  image is handled. **No solid scrim ever.**

### Layout rules
- Fixed header at top, 82px tall (NAV).
- Footer is an extremely large dark editorial block (~2144px tall on
  desktop) — it acts as the manifest of cities + services + insights.
  Treat the footer as a destination, not a chrome.
- Page max width 1440. Content max width 1272 with 84px gutters.
- Sections are vertically separated by **80px**.

---

## ICONOGRAPHY

Premier Staff's icon language is **minimal and SVG-only**. There is
**no icon font** in the source. The brand mostly relies on type and
photography to communicate, and uses icons sparingly for:

- **Star ratings** — gold-filled five-pointed stars
  (Figma uses Material Symbols `star`, filled). 16–20px.
- **Down arrow / right arrow** — used inside primary buttons next to
  the label and on accordion FAQ rows. Stroked, ~1.5px stroke,
  warm-black.
- **Brand logo** — combined wordmark "PREMIER STAFF" — see
  `assets/logo-premier-staff.svg`. The "PREMIER" wordmark is custom
  serif; "STAFF" is rendered as a top-aligned tracker above the M/I.
- **Trustedby client logos** — real client wordmarks (Netflix, Spotify,
  Converse, etc.) used as monochrome SVGs in a single horizontal strip
  at ~70% opacity on dark backgrounds.

**No emoji.** **No unicode-as-icon.** **No PNG icons** in the source.

> **CDN substitute for system icons:** when the design system needs a
> generic icon (e.g. menu, close, arrow) we use **[Lucide](https://lucide.dev/)**
> at 1.5px stroke weight, 20–24px size, in `currentColor`. Lucide's
> stroke-based aesthetic matches the few hand-rolled arrows in the
> Figma. Loaded via:
> ```html
> <script src="https://unpkg.com/lucide@latest"></script>
> <i data-lucide="arrow-right"></i>
> ```
> ⚠ This is a substitution — none of the original SVGs are Lucide.
> If a precise icon set is required, please attach an icon font or
> SVG sprite to `assets/icons/`.

Logo / asset files copied into `assets/`:
- `logo-premier-staff.svg` — combined wordmark, single-color.
- `logo-union.svg` / `logo-path12.svg` — separated parts (PREMIER /
  STAFF tracker) for cases where the alignment ratio differs.
- `hero-image.png`, `enterprise-bg.jpg`, `event-1…5.png`,
  `ambassador-1…5.{png,jpg}` — reference photography for layout mocks.

---

## How to use this system

For HTML deliverables, link the css and the asset folder:

```html
<link rel="stylesheet" href="../colors_and_type.css">
<img src="../assets/logo-premier-staff.svg" alt="Premier Staff" style="color:var(--fg)" />
```

For dark theme, set on `<html>`:
```html
<html data-theme="dark">
```

The css file ships a `.btn`, `.btn-primary`, `.btn-secondary`, `.eyebrow`,
`.lead`, `.small`, `.meta` plus `h1`–`h6` defaults so most layouts
need no extra component CSS to start.

---

## Manifest / index

Root files:
- `README.md` — this file.
- `SKILL.md` — agent skill manifest. Cross-compatible with Agent Skills.
- `colors_and_type.css` — CSS variables (color, type, space, ease, radii)
  + a small set of base classes.
- `fonts/` — local copies of Playfair Display + Roboto (the two-font system).
- `assets/` — logos, photography, icon source files.
- `preview/` — small specimen/swatch cards (used by the Design System tab).

UI kits:
- `ui_kits/marketing-website/` — Premier Staff marketing site recreation.
  Click-thru between Home (light) and Enterprise (dark). Components:
  `Nav`, `Hero`, `HeroCentered`, `TrustedBy`, `Bento`, `BookingSteps`,
  `Review`, `FAQ`, `Footer`, `Buttons`, `Rating`, `SectionTitle`.

There is a single product surface in this brand — the marketing website.
There is no in-app product UI: the brand is service-driven, sold through
the website's contact + booking flows.

# Codestrata design system, v2

Date: 2026-07-22 (v2 same day; owner decisions: fog slate contrast color, character
type stack, descent narrative first). Pairs with `ACCEPTANCE-CRITERIA.md` (v5) and
`WEBSITE-STANDARDS.md`.
Evolved from the shipped v4 stylesheet, a rendered study of quest1.io, and a ten-site
design-language audit of the market (CAST, vFunction, CodeScene, Moderne, Sonar,
Kodesage, Mechanical Orchard, Thoughtworks, plus Linear and Tailscale as benchmarks;
audit notes in the research repo at `../../research-log/literature/competitors/` and
the session record). This document is prescriptive. If a page follows it mechanically,
visual harmony, presentation, and attention management come out right without taste
calls at build time. Where judgment is still needed, the rule says who decides.

---

## 0. Personality and strategy

**Personality in one line: a measurement instrument with a good bedside manner.**
The site should feel like a precision tool built by people who read code for a living,
presented calmly enough that a CFO trusts it.

Three strategy calls, from the audit:

1. **Dark-first stays.** Every vendor in this market is light-first enterprise SaaS.
   The developer benchmarks engineers admire (Linear) are dark and typographically
   confident. Dark-first plus a first-class light theme gives us the developer-familiar
   face and the executive/print face from one token set.
2. **Amber stays.** The entire market accents in blue or teal. Our amber/clay strata
   accent is ownable, on-metaphor (sediment, layers, core samples), and instantly
   distinguishes a screenshot of our site from every competitor. Never introduce blue
   as an accent; blue reads as "everyone else."
3. **Evidence is the hero.** No vendor shows a real analysis artifact above the fold;
   they show metaphors, gauges, and videos. Our hero visual is always an assessment
   artifact (core-sample column, a finding with file and rule ID, a report fragment),
   labeled illustrative where it is not from a real engagement. Linear proves
   product-as-hero converts; in our category it is unoccupied ground.

**The register split (this rule does most of the automatic work):**

- **Proportional carries the argument** (Space Grotesk speaks it loud, Inter speaks
  it plain). Claims, headlines, explanations, persuasion.
- **Mono (IBM Plex Mono, v2) carries the facts.** File paths, rule IDs, commands,
  JSON, machine data. Mono is never used for a persuasive sentence, and a statistic
  is never set in the display face. A reader should be able to squint and know:
  proportional = what we believe, monospace = what we measured.

## 1. The terminal grammar (adopted from quest1.io, dosed)

Quest1's charm is that the page speaks the reader's filesystem language. We adopt the
grammar where it annotates structure and facts, never where it decorates.

Vocabulary (the only allowed devices):

- **Section index eyebrows:** `01 // WHY ASSESS FIRST` in mono caps. Numbered in
  reading order, two digits, the `//` reads as a code comment. Replaces the current
  plain eyebrow. One per section, always.
- **Key-value metadata:** `scope: one application` `timeline: 3 weeks`
  `deliverable: strata report` for engagement tiers and report facts. Mono, muted key,
  foreground value.
- **Path notation for evidence:** `src/db/Conn.java:12` `DEP-EOL-001` always mono,
  always real-looking, always consistent with what the product emits.
- **Prompt lines only where the thing is literally a command or output:** a `$` line
  may introduce the report JSON or the re-scan promise (`$ codestrata assess ./billing
  # same input, same findings`). Maximum one `$` device per page.
- **Status chips:** `assessed` `partial` `unassessed` mono lowercase in bordered chips,
  mirroring the product's coverage states.

Dosage rules (mechanical):

- Mono never exceeds roughly 10 percent of visible text in any viewport (v2), never
  renders below 0.8rem, and tracks at .08em or tighter (section 3).
- Terminal devices never appear in the hero headline or any H2. Headlines are sans,
  human, confident.
- Never fake it: no decorative code, no gibberish hex dumps, no matrix rain. Every
  mono string on the page must be a plausible product output or a true fact. A
  developer who reads every mono string should nod, not smirk.

## 2. Color

Raw palette (v2: fog added by owner decision, 2026-07-22):

| Token | Value | Meaning |
|---|---|---|
| `--amber` | `#d98a3d` | the brand accent, dark theme |
| `--amber-bright` | `#eca860` | hover/active accent, dark theme |
| `--amber-deep` | `#b06a24` | accent on light theme (AA on white) |
| `--clay` | `#7a4a2b` | deep supporting tone, large surfaces only |
| `--mineral` | `#4fb3a5` | POSITIVE/health semantic only, never decoration |
| `--danger` | `#e06c5b` | NEGATIVE/risk semantic only, never decoration |
| `--fog` | `#7a8ba6` dark / `#5c6e88` light | the VILLAIN color: the problem state |

**The fog (the contrast narrative).** Fog is a cold, desaturated steel-slate reserved
exclusively for the problem state: stale diagrams, unknowns, redacted boxes, tribal
knowledge, the free assessment's pre-written conclusion, anything probabilistic or
unverified. Companion tokens `--fog-surface` and `--fog-border` give it its own cold
surface family. Three laws:

1. Fog never appears without amber resolving it in the same composition. Every fog
   element exists to be cut through; the reader always sees the victory.
2. Fog is never interactive and never decorates our own product surfaces. Findings,
   reports, CTAs, and chips stay in the brand family.
3. Fog is the market's blue, weaponized: every competitor accents in blue or teal, so
   the cold blue-gray literally codes "everyone else, and the state they leave you in."

Semantic tokens per theme: keep the v4 dark and light blocks exactly (`--bg` `--bg-2`
`--surface` `--surface-2` `--border` `--border-2` `--fg` `--fg-muted` `--fg-dim`
`--accent` `--accent-fg` `--code-bg` `--shadow`). Two amendments:

- Add `--good: var(--mineral)` and `--risk: var(--danger)` so severity coloring in
  evidence components is semantic, not hard-coded.
- Code blocks stay dark in BOTH themes (`--code-bg` stays near-black in light mode).
  A terminal that turns white stops reading as a terminal. This is already in v4;
  it is now a rule, not an accident.

**The accent budget (the core attention-management rule):** within any one viewport
height, the accent color may appear on at most three elements: one interactive (the
CTA or a link cluster), one structural (the section eyebrow), one informational (a
single highlighted word, number, or chart mark). Everything else is grayscale
hierarchy. If a section design wants a fourth amber element, one of the existing
three must lose it. Severity colors (`--good`, `--risk`) live inside evidence
components only and do not count against the accent budget, but a single component
never shows more than one severity color per row.

Contrast floors: body and UI text AA in both themes (the light-theme muted tokens are
the historical failure; check them first). Accent-on-bg is decorative only; never set
body copy in the accent.

**Presenting the palette (added 2026-07-22):** never show neutral tokens as flat
chips; adjacent dark neutrals are indistinguishable out of context. Show neutrals as
a nested elevation stack (bg holding surface holding surface-2, borders visible), and
show the inks (accent, good, risk, fog) as chips with their narrative role stated.
Show fog's value at map scale: the stale dashed diagram against the solid evidenced
map is the signature "turn" image (section 5c) and the preferred demonstration.

## 3. Typography (v2, owner decision 2026-07-22: the character stack)

v1 shipped Inter everywhere plus JetBrains Mono as the metadata workhorse. Owner
verdict: the mono was illegible at small sizes and the combination had no character.
The v2 stack, three faces with three jobs:

- **Display: Space Grotesk** (500 to 700). Headlines and section heads only. It has
  the techy personality Inter lacks; free and self-hostable.
- **Body and UI: Inter** (400 to 700). Prose, ledes, cards, buttons, forms, AND all
  small labels and captions that are not literal machine output.
- **Code: IBM Plex Mono** (400, 500). ONLY true machine strings: file paths, rule
  IDs, commands, JSON, key-value data, coverage states, stat numerals. Chosen over
  JetBrains Mono for small-size legibility.

**The mono legibility floor:** mono never renders below 0.8rem (about 13.6px);
letter-spacing never exceeds .08em; uppercase mono only in the section eyebrow.
Everything that was tiny tracked-out mono in v1 (captions, sources, nav meta) either
moves to Inter or grows to the floor. Mono drops from metadata workhorse to
authenticity accent: well under 10 percent of visible text per viewport (was 15).

The scale (six levels, no more; clamp values are the spec):

| Level | Spec | Use |
|---|---|---|
| Display | Space Grotesk, `clamp(2.5rem, 5.6vw, 4rem)`, weight 600, tracking -0.02em, lh 1.04 | one per page, the hero H1 |
| Section | Space Grotesk, `clamp(1.85rem, 3.6vw, 2.6rem)`, weight 600, tracking -0.015em | H2, one per section |
| Card | Inter, `1.08rem`, weight 640, lh 1.35 | H3 in cards and list items |
| Body | Inter, `17px`, weight 400, lh 1.6 | prose |
| Lede | Inter, `clamp(1.08rem, 1.5vw, 1.24rem)`, weight 420, muted, max 58ch | one under each H2 |
| Meta | Plex Mono `.8rem` for machine strings; Inter `.78rem` weight 550, tracking .06em caps for non-machine labels | labels, indices, captions |

Rules that keep harmony automatic:

- **Only adjacent levels touch.** A Display never sits directly above Body; there is
  always a Lede or Meta between them. This single rule prevents most "looks off" cases.
- One Display per page. One Section head per section. If a section wants two H2s it
  is two sections.
- Numbers in running text stay in the body face, but every number inside a stat tile,
  table, chip, or key-value is mono with `font-variant-numeric: tabular-nums`.
- `text-wrap: balance` on all headings and ledes, `text-wrap: pretty` on body and
  list items (v2 carry). Measure: body max 60ch, ledes 58ch, section heads 680px.
- Space Grotesk never sets body copy or UI controls; Inter never sets a machine
  string; Plex Mono never sets a persuasive sentence. Three faces, three jobs.
- Headings at weight 600 to 680, never 800 plus. Heavy weights read as retail.

## 4. Space, size, and shape

- **Spacing scale:** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128 px. Every margin,
  gap, and padding is one of these. Inline one-off values are forbidden (v4 carry);
  if a layout needs a nudge, change the token or the component, not the instance.
- **Section padding:** `clamp(4rem, 8vw, 7.5rem)` block; tight variant
  `clamp(3rem, 6vw, 4.5rem)` for bands (stats, logos, guarantee).
- **Container:** `--maxw: 1120px`; prose column 680px; gutter
  `clamp(1.25rem, 4vw, 2.5rem)`.
- **Radii:** 10px controls and chips, 16px cards, 22px feature panels. Nothing
  fully-rounded except status dots.
- **Borders over shadows in dark, shadows over borders in light.** Dark theme:
  1px `--border` with `--surface` fills; shadows barely read on dark. Light theme:
  the v4 soft shadow pair plus lighter borders. Components carry both; the theme
  decides which is visible.
- **Grid habits:** cards in 2-up or 3-up only (4-up allowed for logos/chips only).
  Any table wider than three columns is a design smell (v4 carry) and must become
  cards or a two-axis diagram.

## 5. Attention management (the algorithm)

The goal: a visitor's eye should never have to decide. Apply these rules in order
when composing any page.

1. **One focal point per viewport.** The focal point is whatever combines largest
   size, highest contrast, and accent presence. Compose each screenful so exactly one
   element wins all three. Everything else steps down at least two hierarchy levels.
2. **Declare each section's scan pattern.** Hero and CTA sections compose on a
   Z-path (headline top-left, visual right, CTA at the exit point). List and evidence
   sections compose on an F-path (left-aligned heads, scannable rows). Prose sections
   are single center column. Never mix patterns inside one section.
3. **Section cadence (the pacing device the market uses; ours is token-driven):**
   alternate `--bg` and `--bg-2` sections; never two identical backgrounds adjacent.
   After every second content section, insert a breather: a stat band, a pull-quote
   with witness, or the guarantee band. Maximum two card-grid sections in a row.
4. **The 5-second ramp (v1 carry, now mechanical):** above the fold contains, in
   this order of visual weight: what it is (Display), who it is for and what you get
   (Lede), proof it is real (the artifact visual), where to act (primary CTA). If any
   fourth element competes with these, cut it.
5. **CTA rhythm:** the primary CTA appears exactly three times on a page: hero,
   after the strongest proof section, footer. Never twice in one viewport. The
   secondary (sample report) sits adjacent to the primary at hero and footer only.
   All other links are text links with arrow suffix.
6. **Number salience:** a statistic gets visual emphasis (size, mono, accent) only
   when paired at the point of use with its source or witness (per PRF-1). An
   unattributed number is set in plain body text, which removes the temptation.
7. **Progressive disclosure:** depth lives behind interaction (accordion, approach
   page, sample report), never in longer sections. A section that exceeds a headline,
   one visual, and two sentences moves its overflow to a details surface (v4 carry).
8. **Motion budget:** revised 2026-07-22; superseded by section 5b (the life layer).
   The original rule ("entrance reveals only, nothing loops") shipped a lifeless
   specimen. Reveals, ambient motion, and interaction choreography are now specified
   in 5b with hard caps instead of a blanket ban.

## 5b. The life layer (added 2026-07-22)

Owner feedback on specimen v1: correct but lifeless; no gradients, no lively
interaction, the design does not speak. Root cause: the system codified restraint and
never budgeted for expression. This section is the budget. The principle: **life
serves the evidence, never competes with it.** Every device below exists to make the
instrument feel precise and alive, like a scanner mid-scan, not decorated.

### Gradients (now first-class, one hue family)

- **The aura.** Each page gets one large, soft radial amber glow
  (`--hero-glow`: amber at 14 to 20 percent, to transparent) placed behind the hero
  artifact. A second, fainter aura may sit behind the guarantee band. Auras never sit
  behind body text columns.
- **Surface light.** Cards and artifacts may carry a faint top-lit linear gradient
  (surface to surface-2) plus a 1px gradient top border (border-2 to transparent),
  reading as light from above. Applied via the component, identical everywhere.
- **Gradient ink.** Exactly one word of the hero headline may be set in an amber
  gradient (`amber-bright` to `amber-deep`, background-clip: text). One word, chosen
  for meaning, once per page. Gradient ink never appears elsewhere.
- **The depth gauge.** A 2px scroll-progress bar fixed under the nav, amber gradient.
  It is on-metaphor (how deep in the strata you are) and gives the page a pulse.
- Gradients stay in the amber family plus neutral surface tones. Never multi-hue,
  never rainbow mesh, never blue (section 0).

### Ambient motion (the scanner idiom)

Ambient means it moves without input. Hard caps: at most ONE ambient device visible
per viewport; cycle time 6 seconds or slower; amplitude subtle enough that a
screenshot at any moment still passes every static rule; all of it freezes under
`prefers-reduced-motion`.

- **The scan line.** A soft amber sweep that travels down the core-sample artifact on
  a 7 second cycle. This is the signature: the instrument is running. Allowed on the
  hero artifact and on the sample-report artifact, one at a time.
- **Settling strata.** On first reveal, artifact layers drop in with a 60ms stagger,
  like sediment settling. Once, on entry, never looping.
- **Counting numbers.** Stat-unit numerals count up over 900ms when first scrolled
  into view. Numbers land exactly on the attributed value.
- **The typed command.** The guarantee's `$` line types itself on first view, 18ms
  per character, then a steady block cursor blinks at 1.1s. The one permitted
  perpetual motion besides the scan line, and they should not share a viewport.

### Interaction choreography (feedback under 200ms)

- **Cards and layers:** hover lifts 2 to 3px, border warms toward
  `color-mix(accent 35%, border-2)`, shadow gains a faint amber tint. Cursor never
  changes what a thing means, only confirms it is alive.
- **Primary button:** a sheen sweep (white at 12 percent, 500ms) crosses on hover;
  active state presses 1px down.
- **Finding rows:** hover raises the row background one surface step and brightens
  the severity dot. Rows feel inspectable, like a log viewer.
- **Links:** underline slides from left (border-image or scaled pseudo-element),
  140ms.
- **Theme flip:** 300ms cross-fade (already token-driven); the toggle label swaps
  with a 120ms fade so the switch feels engineered, not instant-teleport.
- **Reveals:** opacity plus 10px rise plus a 6px blur-to-sharp, 350ms, staggered
  60ms up to 5 siblings. The blur-in reads as focus being achieved, which is the
  brand promise. No-JS failsafe mandatory (v3 carry).

### Scroll rhythm and the micro layer (added 2026-07-22, second pass)

Owner feedback on life-layer v1: a couple of animations do not make a personality.
Two additions, still under the same principle.

**Reveal by default.** Every section head, evidence block, and band content reveals
once on scroll entry (the blur-to-sharp rise), staggered among siblings. A section
that does not move as it enters is the exception and needs a reason. The page should
feel like the report assembling itself as the reader descends. Caps stay: 350ms, one
pass, failsafe, reduced-motion static.

**The micro layer.** Small, quiet, everywhere:

- **Eyebrow line draw.** The 22px rule before each section index draws in from zero
  when the section reveals, 450ms delayed 150ms. The section signs itself in.
- **Depth readout.** Next to the depth gauge, the nav meta shows a live mono
  `depth: 42%` that tracks scroll. The page is an instrument; instruments have dials.
- **Ghost indices.** Each section carries its two-digit index as a giant mono
  numeral, 4 to 5 percent opacity, top right, hidden on mobile. Structure made
  visible, quest1's editorial numbering at our volume.
- **Chip and control hovers.** Every chip, tag, and button responds: 1px rise,
  border warming toward accent, under 200ms. Nothing interactive is inert.
- **The logo breathes.** On hover the three strata bars of the logo mark shear
  1 to 2px in alternating directions, 250ms, and settle back. One private joke,
  played quietly.
- **Theme swap.** The toggle label cross-fades 120ms on switch.

**Widow enforcement (restated as a check, not a hope).** `text-wrap: balance` on
every heading and lede; `text-wrap: pretty` on every body, claim, description, list
item, and caption element, including ones not typed as `p`. The rendered-eye pass
rejects any text block ending in a stranded word (v2 carry, CPY-1.3).

### What stays banned

Parallax backgrounds, cursor followers, magnetic buttons, marquee logo strips,
particle fields, 3D tilts, scroll-jacking, autoplaying video, and any animation on
body text. Decorative code and fake terminals stay banned (section 1); the life layer
animates real artifacts only.

### Verification additions

The rendered-eye pass (section 10) now also checks: the scan line runs; numbers
count and land exact; typing completes and the cursor blinks; hovers respond under
200ms; `prefers-reduced-motion` yields a fully static, fully legible page; no
viewport shows two ambient devices at once.

## 6. Evidence presentation (our signature components)

These components are the brand. Build them once, reuse everywhere.

- **The finding row.** One finding = severity dot (`--risk`/`--good`/neutral), mono
  rule ID chip (`DEP-EOL-001`), sans one-line description, mono evidence path
  (`pom.xml:47`), muted effort tag. This row is the atomic unit of the whole visual
  identity; it appears in the hero artifact, the report preview, and the sample
  report page, identical every time.
- **The stat unit.** Mono number (tabular), sans claim, mono source line
  (`GAO-25-107795` or the named study) in `--fg-dim`. Number and witness are one
  component; the number cannot be instantiated without the source slot filled
  (mirrors PRF-1 mechanically). Stat bands hold three units maximum.
- **The core-sample column.** The layered-strata hero visual: stacked layers, each a
  surface with a mono year plus stack label and a severity edge. It is our logo-scale
  motif; also usable as small multiples (per-app columns in the portfolio section).
- **The coverage chip row.** `assessed` `partial` `insufficient` `unassessed` chips,
  exactly the product's states, as honesty-forward UI.
- **The report artifact.** The JSON block, dark in both themes, with the
  `// illustrative output format` comment line pinned (GOV-1.1). Syntax coloring:
  keys muted, strings foreground, numbers accent, exactly three colors.
- **The guarantee band.** Full-width `--bg-2` band, tight padding: sans commitment
  sentence, then the falsifiable line in mono (`$ codestrata assess ./billing  # rerun
  it. same findings.`), then the redo-if-wrong clause in body text. This is where the
  market puts logo walls; ours is a promise with a command.
- **The method note.** A bordered aside in the approach page and sample report:
  "how this finding is produced, what it cannot see," in the register of a methods
  section. The audit found no vendor publishes limits; Sonar's false-positive rate is
  the only self-critical number in the market. This component occupies that gap.

## 7. Diagrams and imagery

- Inline SVG only. No stock photography, no abstract 3D, no screenshots of dashboards
  we do not ship. Photography enters only when we have real people to show.
- Diagram style: 1.5px strokes in `--border-2`, node fills `--surface-2`, labels in
  mono Meta, one accent element per diagram (the thing the diagram is about), arrows
  with small triangular heads, orthogonal routing. Trust-boundary diagrams show the
  perimeter as a dashed rounded rectangle with the mono label `your perimeter`.
- Every diagram is theme-aware (uses tokens, not literal colors) and carries a
  one-line caption in Meta. Alt text states the claim the diagram makes, not its shape.

## 8. Voice in the interface

Microcopy follows CPY (v5) plus: buttons are verb-first two to four words ("Book an
assessment", "Read a sample report"); no "Learn more" anywhere; empty states and form
feedback are plain and human ("That reached us. Expect a reply within two business
days."); the 404 may use one terminal joke, the only permitted humor slot. No em or
en dashes anywhere, including SVG text and code comments (grep-enforced).

## 9. Implementation contract

- All tokens live in one `:root` block plus one `[data-theme="light"]` override
  block in `assets/styles.css`; components reference semantic tokens only. A rebrand
  stays a palette-block swap.
- Theme toggle: respects `prefers-color-scheme`, persists in localStorage, and the
  toggle is keyboard-operable (v2 carry). Both themes ship AA on every page.
- Fonts are the only external dependency; everything else self-contained (v1 carry).
- Class naming: component-first (`.finding-row`, `.stat-unit`, `.guarantee-band`);
  utilities limited to the existing type helpers. Every class in HTML has a CSS rule
  (GOV-2.2 grep).
- Print stylesheet for the sample report page: light theme forced, nav and CTAs
  hidden, evidence rows intact. PE buyers print things.

## 5c. The story layer (added 2026-07-22, owner decision: descent narrative)

A marketing page is a drama, not a catalog. Every page composes from five story
primitives, in reader order; components from sections 6 and 5b are the props.

1. **The villain.** The problem state, rendered in fog: the stale architecture
   diagram with redacted unknowns, the tribal-knowledge gap, the free assessment
   whose conclusion is pre-written. One villain per page, named early, shown not told.
2. **The stakes.** What the villain costs, as stat units with witnesses (the 79
   percent, the black swan). Stakes follow the villain immediately.
3. **The turn.** The moment evidence cuts the fog: a composition where fog elements
   resolve into amber findings, ideally the same modules before and after. This is
   the signature image of the brand.
4. **The proof.** Findings, the report artifact, the method note, and (when real)
   case studies and references in the designed proof slots.
5. **The ask.** The guarantee band plus the primary CTA.

**The descent (homepage architecture).** The homepage is one continuous core-sample
descent. Surface = the villain in fog. Each scroll stratum goes deeper and older;
the depth gauge and readout tie scrolling to descending; the strata motif recurs and
darkens; bedrock = the full report artifact and the ask. The page performs the
product: an assessment, run on the reader's attention. Section backgrounds may shift
one step colder or deeper per stratum to sell the descent, within token discipline.

## 9b. The business layer (what the system does for marketing, sales, and product)

The design system is a revenue asset, not a stylesheet. Three bridges, owned here:

1. **Product bridge.** The CLI's HTML Strata Report consumes THIS token set (a
   shared `tokens.css`). Every delivered report is a branded artifact circulating
   inside the buyer's org: the report is the best salesperson. The finding row,
   coverage chips, and strata column render identically in product and marketing.
2. **Sales kit.** From the same tokens: the one-pager, the deck master (title,
   divider, evidence, pricing-anchor slides), the proposal cover, OG and LinkedIn
   card templates, the email signature. A campaign never starts from a blank page.
3. **Conversion components, designed and waiting.** Proof slots (case-study card
   with time-boxed headline, testimonial with named witness, analyst mention, trust
   bar) specified now, populated only when true (GOV-1). Objection modules encoding
   the pushback catalog: the "compared to the free assessment" block, the
   risk-reversal panel, the "what about SonarQube" answer. The EOL exposure checker
   and sample-report flipper are the instrument-teaser components, next in build
   order after the descent homepage.

## 10. Definition of visually done (hooks into v5)

A page passes this system when: rendered review at tall viewport in BOTH themes shows
one focal point per screenful (5.1); the accent budget holds on every screenful (2);
only adjacent type levels touch (3); section cadence alternates and breathers land
(5.3); every number on screen sits inside a stat unit or plain body text (5.6, 6);
mono share stays under the dosage cap and every mono string is true (1); DSN-1.1
through DSN-1.4 and GOV-2.1 through GOV-2.3 pass. Screenshot both themes at 375, 768,
1280 wide before calling it done.

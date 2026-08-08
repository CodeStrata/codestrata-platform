"""Embedded CSS for website-safe EIR HTML — Design System 1.0 consumer.

Authority: ``codestrata-visual-design-system:1.0`` via
``codestrata.design_system.tokens`` (embedded at generation time).
Brand hex lives in the token artifact; component rules use custom properties.
"""

from __future__ import annotations

from codestrata.design_system.tokens import BRAND_VALUES, DESIGN_TOKENS_CSS

_PRINT_PAPER = BRAND_VALUES["paper"]
_PRINT_INK = BRAND_VALUES["ink"]
_PRINT_MUTED = BRAND_VALUES["muted"]
_PRINT_LINE = BRAND_VALUES["line"]
_PRINT_LINE_STRONG = BRAND_VALUES["line_strong"]
_PRINT_SOFT = BRAND_VALUES["paper_soft"]

REPORT_CSS = f"""
{DESIGN_TOKENS_CSS}
* {{ box-sizing: border-box; }}
html {{ scroll-padding-top: 1.25rem; max-width: 100%; overflow-x: hidden; }}
body {{
  margin: 0;
  font-family: var(--cs-font-sans);
  color: var(--ink);
  background: var(--bg);
  line-height: 1.65;
  max-width: 100%;
  overflow-x: hidden;
}}
.report-shell, .wrap, main {{
  max-width: 100%;
  min-width: 0;
  overflow-x: hidden;
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-delay: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-delay: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }}
}}
.sr-only {{
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}}
a {{ color: var(--accent); }}
a:focus-visible, button:focus-visible, summary:focus-visible, [tabindex]:focus-visible {{
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}}
.skip-link {{
  position: absolute;
  left: 1rem;
  top: 1rem;
  transform: translateY(-250%);
  background: var(--surface);
  color: var(--ink);
  padding: 0.5rem 0.75rem;
  z-index: 100;
  border: 1px solid var(--border);
  border-radius: var(--cs-radius-control);
}}
.skip-link:focus {{ transform: translateY(0); }}
.report-shell {{ min-height: 100vh; }}
.report-product-bar {{
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 1rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}}
.report-product-mark {{
  display: inline-flex;
  align-self: center;
  color: var(--accent);
}}
.report-product-mark .cs-mark {{
  width: 20px;
  height: 20px;
}}
.report-product-name {{
  font-family: var(--cs-font-display);
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: -0.01em;
  color: var(--accent);
}}
.report-product-label {{
  font-size: 0.85rem;
  color: var(--muted);
}}
.wrap {{
  max-width: var(--cs-max-content);
  margin: 0 auto;
  padding: 1.5rem;
}}
/* The cover is a section for landmark reasons; keep its original spacing. */
section.cover {{
  margin-top: 0;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 1.75rem 0 1.25rem;
}}
section.cover .wrap {{
  padding-top: 0;
  padding-bottom: 0;
}}
.cover-panel {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.35rem 1.5rem;
}}
h1 {{
  font-family: var(--cs-font-display);
  font-size: clamp(1.75rem, 3vw, 2.25rem);
  margin: 0.35rem 0 0.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.12;
}}
h2 {{
  font-family: var(--cs-font-display);
  font-size: clamp(1.25rem, 2vw, 1.5rem);
  margin-top: 2rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.35rem;
  font-weight: 600;
  letter-spacing: -0.015em;
}}
h3 {{
  font-family: var(--cs-font-display);
  font-size: 1.1rem;
  margin-top: 1.25rem;
  font-weight: 600;
}}
h4 {{
  font-size: 0.95rem;
  margin: 0.85rem 0 0.35rem;
  font-weight: 650;
}}
.meta, .muted {{ color: var(--muted); }}
.cover-meta {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.65rem;
  margin: 0.85rem 0 0;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border);
}}
.meta-item {{ display: flex; flex-direction: column; gap: 0.1rem; }}
.meta-label {{
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  font-weight: 650;
}}
.meta-value {{
  font-weight: 600;
  overflow-wrap: anywhere;
}}
.summary-kpis {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}}
.kpi {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--cs-radius-control);
  padding: 0.85rem 0.95rem;
}}
.kpi-label {{
  margin: 0;
  color: var(--muted);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 650;
}}
.kpi-value {{
  margin: 0.25rem 0 0;
  font-family: var(--cs-font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 1.2rem;
  font-weight: 500;
}}
.badge {{
  display: inline-block;
  border: 1px solid var(--border);
  padding: 0.12rem 0.5rem;
  border-radius: var(--cs-radius-button);
  font-size: 0.72rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  background: var(--surface-2);
  color: var(--ink);
}}
.badge-status {{
  background: var(--cs-teal-soft);
  color: var(--cs-status-success);
  border-color: var(--cs-line-strong);
}}
.status-badge {{
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: var(--cs-radius-button);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  border: 1px solid var(--cs-line-strong);
  background: var(--cs-fog-surface);
  color: var(--muted);
}}
.status-severity-critical, .status-severity-high {{
  background: var(--cs-risk-critical-soft);
  color: var(--critical);
}}
.status-severity-medium {{
  background: var(--cs-risk-medium-soft);
  color: var(--medium);
}}
.status-severity-low {{
  background: var(--cs-risk-low-soft);
  color: var(--low);
}}
.status-severity-informational {{
  background: var(--cs-blue-soft);
  color: var(--cs-status-info);
}}
.status-severity-critical::before,
.status-severity-high::before,
.status-severity-medium::before,
.status-severity-low::before,
.status-severity-informational::before {{
  content: "";
  display: inline-block;
  width: 0.45em;
  height: 0.45em;
  margin-right: 0.3em;
  border: 1.5px solid currentColor;
  vertical-align: 0.05em;
}}
.status-severity-critical::before {{ background: currentColor; }}
.status-severity-high::before {{ background: currentColor; opacity: 0.7; }}
.status-severity-medium::before {{ background: transparent; }}
.status-severity-low::before {{ border-radius: 50%; background: currentColor; }}
.status-severity-informational::before {{ border-radius: 50%; background: transparent; }}
.confidence-badge {{
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: var(--cs-radius-button);
  font-size: 0.72rem;
  font-weight: 650;
  border: 1px solid var(--cs-line-strong);
  background: var(--cs-blue-soft);
  color: var(--cs-status-info);
}}
.confidence-badge-limited, .confidence-badge-unavailable {{
  background: var(--cs-paper-soft);
  color: var(--cs-status-neutral);
}}
nav.toc {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  margin: 1.25rem 0;
}}
@media (min-width: 1040px) {{
  nav.toc {{
    position: sticky;
    top: 0.5rem;
    z-index: 20;
  }}
}}
nav.toc h2 {{
  margin-top: 0;
  border-bottom: 0;
  font-size: 1.15rem;
}}
nav.toc ol {{
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  columns: 2;
  column-gap: 1.5rem;
}}
nav.toc li {{ break-inside: avoid; margin: 0.3rem 0; }}
nav.toc a {{
  color: var(--ink);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}}
nav.toc a:hover, nav.toc a:focus:not(:focus-visible) {{
  color: var(--accent);
  border-bottom-color: var(--accent);
  outline: none;
}}
nav.toc a:focus-visible {{
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}}
section {{
  margin-top: 0.5rem;
}}
section > h2:first-child {{ margin-top: 1.75rem; }}
.table-wrap {{
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow-x: auto;
  contain: paint;
  -webkit-overflow-scrolling: touch;
  margin: 0.75rem 0 1.25rem;
  border: 1px solid var(--border);
  border-radius: var(--cs-radius-control);
  background: var(--surface);
}}
.table-wrap:focus-visible {{
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}}
.table-wrap > table {{
  width: 100%;
  min-width: 28rem;
  border-collapse: collapse;
  margin: 0;
  border: 0;
  background: transparent;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  margin: 0.75rem 0 1.25rem;
}}
th, td {{
  border-bottom: 1px solid var(--border);
  padding: 0.55rem 0.7rem;
  text-align: left;
  vertical-align: top;
  font-size: 0.92rem;
}}
.table-wrap th, .table-wrap td {{
  border-left: 0;
  border-right: 0;
}}
th {{
  background: var(--surface-2);
  font-family: var(--cs-font-sans);
  color: var(--muted);
  font-weight: 650;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
td {{ overflow-wrap: anywhere; }}
td.numeric, th.numeric {{
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-family: var(--cs-font-mono);
}}
tbody tr:nth-child(even) {{
  background: color-mix(in srgb, var(--surface-2) 80%, transparent);
}}
.empty-state {{
  margin: 0.75rem 0;
  padding: 0.85rem 1rem;
  border: 1px dashed var(--border-2);
  border-radius: var(--radius);
  background: var(--surface-2);
  color: var(--muted);
}}
details {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--cs-radius-control);
  padding: 0.75rem 1rem;
  margin: 0.75rem 0;
}}
details[id^="pattern-"], details[id^="observation-"] {{
  border-left: 3px solid var(--accent);
}}
summary {{
  cursor: pointer;
  font-weight: 600;
  font-family: var(--cs-font-display);
}}
.evidence-block, .tech-ref {{
  font-family: var(--cs-font-mono);
  font-size: 0.85rem;
  overflow-wrap: anywhere;
}}
.disclaimer {{
  border-left: 3px solid var(--cs-status-warning);
  padding: 0.55rem 0.75rem;
  background: var(--cs-rust-soft);
  color: var(--ink);
  border-radius: 0 var(--cs-radius-control) var(--cs-radius-control) 0;
}}
article.drilldown-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--cs-radius-control);
  padding: 1rem 1.1rem;
  margin: 1rem 0;
}}
article.drilldown-card h3 {{ margin-top: 0; }}
.trace-list {{
  margin: 0.35rem 0 0.75rem;
  padding-left: 1.15rem;
}}
.trace-list li {{
  margin: 0.25rem 0;
  font-family: var(--cs-font-mono);
  font-size: 0.88rem;
}}
footer.site-footer {{
  margin: 2.5rem 0 1rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.9rem;
}}
footer.site-footer p {{ max-width: 70ch; }}

@media (max-width: 1024px) {{
  nav.toc ol {{ columns: 1; }}
  nav.toc {{ position: static; }}
}}
@media (max-width: 820px) {{
  .wrap {{ padding: 1.1rem 0.95rem; }}
  .report-product-bar {{ padding-inline: 0.95rem; }}
  .summary-kpis {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 560px) {{
  .summary-kpis, .cover-meta {{ grid-template-columns: 1fr; }}
  h1 {{ font-size: 1.55rem; }}
}}

@media (forced-colors: active) {{
  .badge, .status-badge, .confidence-badge {{
    forced-color-adjust: none;
    border: 1px solid CanvasText;
    background: Canvas;
    color: CanvasText;
  }}
  .status-badge::before {{ border-color: CanvasText; }}
  details, article.drilldown-card, .table-wrap, nav.toc, .cover-panel, .kpi, .disclaimer {{
    border: 1px solid CanvasText;
  }}
  a:focus-visible, summary:focus-visible, [tabindex]:focus-visible {{
    outline: 3px solid Highlight;
    outline-offset: 2px;
  }}
  .skip-link {{ background: Canvas; color: CanvasText; border-color: CanvasText; }}
}}

@media print {{
  @page {{ margin: 1.4cm; }}
  :root {{
    color-scheme: light;
    --cs-bg: {_PRINT_PAPER};
    --cs-canvas: {_PRINT_PAPER};
    --cs-surface: {_PRINT_PAPER};
    --cs-surface-2: {_PRINT_SOFT};
    --cs-paper: {_PRINT_PAPER};
    --cs-paper-soft: {_PRINT_SOFT};
    --cs-fog-surface: {_PRINT_SOFT};
    --cs-ink: {_PRINT_INK};
    --cs-muted: {_PRINT_MUTED};
    --cs-border: {_PRINT_LINE};
    --cs-border-2: {_PRINT_LINE_STRONG};
    --cs-line: {_PRINT_LINE};
    --cs-line-strong: {_PRINT_LINE_STRONG};
    --cs-teal-soft: {_PRINT_SOFT};
    --cs-rust-soft: {_PRINT_SOFT};
    --cs-blue-soft: {_PRINT_SOFT};
    --cs-risk-critical-soft: {_PRINT_SOFT};
    --cs-risk-high-soft: {_PRINT_SOFT};
    --cs-risk-medium-soft: {_PRINT_SOFT};
    --cs-risk-low-soft: {_PRINT_SOFT};
    --cs-risk-info-soft: {_PRINT_SOFT};
    --bg: {_PRINT_PAPER};
    --surface: {_PRINT_PAPER};
    --surface-2: {_PRINT_SOFT};
    --ink: {_PRINT_INK};
    --muted: {_PRINT_MUTED};
    --border: {_PRINT_LINE};
  }}
  body {{ background: {_PRINT_PAPER} !important; color: {_PRINT_INK} !important; }}
  .skip-link, .report-product-bar {{ display: none !important; }}
  nav.toc {{
    break-after: page;
    position: static;
    box-shadow: none;
  }}
  nav.toc ol {{ columns: 1; }}
  nav.toc a {{ text-decoration: underline; color: {_PRINT_INK}; }}
  details {{
    break-inside: avoid;
    display: block;
  }}
  details > *:not(summary) {{ display: block !important; }}
  details summary {{ margin-bottom: 0.35rem; }}
  a[href^="#"]::after {{ content: ""; }}
  /* Cards and rows avoid splits; whole sections are often taller than a page. */
  section.cover, article, tr {{ break-inside: avoid; }}
  .table-wrap {{ overflow: visible; border: 1px solid {_PRINT_LINE}; }}
  thead {{ display: table-header-group; }}
  tbody tr:nth-child(even) {{ background: transparent; }}
  .badge, .status-badge {{
    border: 1px solid {_PRINT_LINE_STRONG} !important;
    color: {_PRINT_INK} !important;
    background: {_PRINT_SOFT} !important;
  }}
}}
"""

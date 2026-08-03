"""Embedded CSS for website-safe static HTML (no external assets)."""

from __future__ import annotations

REPORT_CSS = """
:root {
  --ink: #1a1f24;
  --muted: #5b6570;
  --line: #d7dde3;
  --bg: #f7f8fa;
  --card: #ffffff;
  --accent: #0f4c5c;
  --warn: #8a5a00;
}
* { box-sizing: border-box; }
html { font-size: 16px; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.55;
}
a { color: var(--accent); }
a:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
.skip-link {
  position: absolute; left: -999px; top: 0;
  background: var(--card); padding: 0.5rem 1rem;
}
.skip-link:focus { left: 1rem; top: 1rem; z-index: 10; }
.wrap { max-width: 960px; margin: 0 auto; padding: 1.5rem; }
header.cover {
  background: var(--card);
  border-bottom: 1px solid var(--line);
  padding: 2rem 0 1.25rem;
}
h1 { font-size: 2rem; margin: 0 0 0.5rem; font-weight: 700; }
h2 { font-size: 1.35rem; margin-top: 2rem; border-bottom: 1px solid var(--line); padding-bottom: 0.35rem; }
h3 { font-size: 1.1rem; margin-top: 1.25rem; }
.meta, .muted { color: var(--muted); }
.badge {
  display: inline-block; border: 1px solid var(--line);
  padding: 0.15rem 0.5rem; border-radius: 0.25rem; font-size: 0.85rem;
  background: var(--card);
}
nav.toc {
  background: var(--card); border: 1px solid var(--line);
  padding: 1rem 1.25rem; margin: 1.25rem 0;
}
nav.toc ol { margin: 0.5rem 0 0; padding-left: 1.25rem; }
table {
  width: 100%; border-collapse: collapse; background: var(--card);
  margin: 0.75rem 0 1.25rem;
}
th, td {
  border: 1px solid var(--line); padding: 0.45rem 0.6rem;
  text-align: left; vertical-align: top; font-size: 0.95rem;
}
th { background: #eef2f5; font-family: system-ui, sans-serif; }
details {
  background: var(--card); border: 1px solid var(--line);
  padding: 0.75rem 1rem; margin: 0.75rem 0;
}
summary { cursor: pointer; font-weight: 600; }
.disclaimer { border-left: 3px solid var(--warn); padding-left: 0.75rem; }
footer { margin: 2.5rem 0 1rem; color: var(--muted); font-size: 0.9rem; }
@media print {
  body { background: #fff; color: #000; }
  nav.toc { break-inside: avoid; }
  details {
    break-inside: avoid;
    display: block;
  }
  details > *:not(summary) { display: block !important; }
  details summary { margin-bottom: 0.35rem; }
  a[href^="#"]::after { content: ""; }
  .skip-link { display: none; }
  header.cover, section, article { break-inside: avoid-page; }
}
"""

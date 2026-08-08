---
title: Telemetry
description: Community Edition telemetry and analytics posture for Engine and VS Code.
---

# Telemetry

Community Edition telemetry is **privacy-first** and **off by default** for product
transmission.

## Principles

- No production telemetry collection is claimed as operational in current Community
  releases unless explicitly stated for a specific surface
- VS Code consent is command-local, default Deny, and not persisted
- No machine identity or installation identity for Community telemetry
- Analytics sinks may be unavailable by design until a later operational gate

## VS Code extension

Eligible assessment commands may prompt for optional, privacy-safe anonymous product
telemetry for that command only. Dismissal or Deny is safe. Discovery, installation
guidance, initialization, report open, doctor, and recovery do not prompt.

See the extension repository privacy materials packaged with the VS Code extension.

## Engine

Engine telemetry follows Engine public contracts: disabled by default, documented
event catalogs where applicable, and no requirement to enable telemetry to assess.

## Related

- [Privacy](/security/privacy)
- [Security](/security/)
- [FAQ](/faq/)

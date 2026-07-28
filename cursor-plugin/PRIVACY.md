# Privacy

CodeStrata Cursor Extension (Community Edition) is designed for **local** Engineering Assessments.

## What this extension does

- Discovers / installs **CodeStrata Engine** locally
- Runs `codestrata` against your open workspace
- Reads public Engine report artifacts
- Writes a generated Cursor rule under `.cursor/rules/` from those artifacts
- Helps copy grounded prompts for Cursor Chat / Agent

## What this extension does not do

- Does **not** call CodeStrata Platform APIs
- Does **not** upload source code by itself
- Does **not** store AI provider credentials in extension settings
- Does **not** ship telemetry in this Community release
- Does **not** independently analyze repository source

## Engine and Cursor

Assessment execution is local unless **you** configure an Engine AI provider.  
Cursor’s own models and privacy controls are separate from CodeStrata — review Cursor’s documentation.

Optional AI uses Engine provider configuration (Bedrock / OpenAI / Azure OpenAI / Anthropic).  
Never confuse AI keys with Platform API keys.

Engine docs: https://github.com/sknampally/codestrata-engine/blob/main/docs/quick-start.md

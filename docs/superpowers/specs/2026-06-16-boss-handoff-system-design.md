# Design Spec: Boss Handoff Documentation System

**Date:** 2026-06-16  
**Status:** Complete  
**Location:** `fusehealth/docs/handoff/`

---

## Problem

The FuseHealth codebase is being handed off to a designer/engineer who will redesign
the UI using Claude. Without documentation, they would:
- Design components that require fields no connected API provides
- Design interactions that violate the database-first contract
- Not know which pages/fields are blocked vs working
- Have no system for verifying designs against real API capabilities

---

## Solution

A 4-document handoff package in `fusehealth/docs/handoff/`:

| File | Audience | Purpose |
|------|----------|---------|
| `API_SOURCES.md` | Human + AI | Official docs URLs for all 12 APIs, credentials, status |
| `DESIGN_BRIEF.md` | Human | Product overview, page-by-page data map, hard constraints |
| `BOSS_README.md` | Human (designer) | Step-by-step process for using Claude to verify designs |
| `AI_TECHNICAL_GUIDE.md` | AI (Claude) | Verification protocol, field-to-connector map, prompt template |

---

## Key Design Decisions

1. **AI_TECHNICAL_GUIDE.md is written for Claude, not humans.** It tells Claude its role, the
   core constraint (database-first), and exactly how to produce a structured verdict. The
   designer pastes their component spec + this guide into a Claude conversation.

2. **The field-to-connector map is the core of the AI guide.** It maps every data field a
   designer might want → which connector supplies it → current status. This prevents Claude
   from guessing or hallucinating API capabilities.

3. **Official API docs are NOT embedded** — they're referenced by URL in `API_SOURCES.md`.
   The designer pastes the relevant section into the prompt template when verifying a component.
   This keeps the guide maintainable (URLs update, embedded docs go stale).

4. **Four verdict states:** APPROVED / APPROVED WITH CONDITIONS / NEEDS REVISION / HARD BLOCK.
   "HARD BLOCK" is reserved specifically for database-first violations — the most important
   architectural constraint to catch before any code is written.

---

## What Is Not In Scope

- This system does not automate the verification — it requires a human to run the prompt
- It does not cover the Django/HTMX implementation details (those are in `SKILLS.md`)
- It does not replace `DESIGN.md` (visual identity / color system)

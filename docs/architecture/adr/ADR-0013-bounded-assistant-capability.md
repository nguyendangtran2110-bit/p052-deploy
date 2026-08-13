# ADR-0013: Bounded Assistant Capability

**Status:** Accepted
**Date:** 2026-08-11

## Context

The assistant answers resident questions and helps fill ticket fields, but resident/profile data and ticket submission are trusted backend actions. LLM output is untrusted and provider availability is optional to manual ticket creation.

## Decision

The assistant can retrieve approved content, return grounded Vietnamese answers/citations, and propose validated patches for subject, content, and urgency only. It has no tool to submit tickets, update verified profile/location fields, change scope, or send notifications. The resident reviews and submits through the normal ticket API.

## Rationale

- Preserves resident control and backend trust boundaries.
- Limits prompt-injection impact.
- Keeps manual ticket creation available when the model is unavailable.

## Tradeoffs

- The assistant cannot fully automate ticket creation.
- Frontend reconciliation is required when proposed fields differ from resident input.

## Consequences

Provider/model and source governance remain deferred, but every implementation must preserve the capability boundary.

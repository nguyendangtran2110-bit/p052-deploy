# ADR-0010: Versioned Onboarding Definitions from Deployment Seeds

**Status:** Accepted
**Date:** 2026-08-11

## Context

Onboarding steps will evolve, but MVP does not require a content-management UI. Progress and reminders must not change unpredictably when a deployment adds, reorders, or retires steps.

## Decision

Store version-controlled building-scoped seed files in the repository and publish them as immutable database definition versions during deployment. Steps use stable keys across versions. A resident remains pinned to the version assigned at enrollment unless an explicit audited migration carries completion by stable step key and recalculates reminders.

Retired steps remain in historical versions. Newly required steps affect existing residents only through that explicit migration.

## Rationale

- Supports evolving steps without adding an MVP administrator UI.
- Preserves completion history and deterministic reminders.
- Makes configuration changes reviewable with code/deployment changes.

## Tradeoffs

- Product/operations changes require a deployment or controlled migration.
- Migrating residents to a new version needs an explicit decision and audit.

## Consequences

Document uploads remain outside MVP. Onboarding content governance beyond the seed publication mechanism is not expanded here.

---
name: OnBxrd
description: A dark operations cockpit for calm resident decisions.
colors:
  ink: "#edf5f2"
  paper: "#0b1114"
  panel: "#111c20"
  line: "#26383b"
  teal: "#8ad3bd"
  teal-soft: "#173c38"
  amber: "#e3ae5b"
  coral: "#f07b72"
  navy: "#071316"
typography:
  display:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "clamp(32px, 4.3vw, 59px)"
    fontWeight: 700
    lineHeight: 1.03
    letterSpacing: "-0.065em"
  body:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.7
  label:
    fontFamily: "DM Mono, monospace"
    fontSize: "10px"
    fontWeight: 400
    letterSpacing: "0.11em"
rounded:
  control: "9px"
  surface: "16px"
spacing:
  compact: "8px"
  control: "12px"
  panel: "25px"
components:
  button-primary:
    backgroundColor: "{colors.teal}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "11px 15px"
  button-ghost:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 15px"
---

# Design System: OnBxrd

## Overview

**Creative North Star: "The Night Operations Cockpit"**

OnBxrd turns high-volume resident communication into a composed, reviewable operational scene. The center of gravity is the message, checklist, or ticket—not decorative dashboard metrics. Rails, ledger rows, and evidence panels support a direct reading path from signal to human decision.

The system is compact and trusted rather than austere: obsidian surfaces, midnight contrast, and a sparing mint-teal action color. Navigation becomes a floating command deck instead of a fixed sidebar; this remains coherent when the deck compresses for mobile use.

**Key Characteristics:** message-first; flat tonal surfaces; readable operational density; explicit human control.

## Colors

The palette uses low-light architectural surfaces and reserves color for meaning.

### Primary

- **Signal Teal** (`#8ad3bd`): primary actions, progress, selected navigation, and confirmed workflow state.
- **Midnight Navy** (`#071316`): the onboarding assistant panel and high-contrast operational focus.

### Tertiary

- **Attention Amber** (`#b87918`): pending or informational cues.
- **Priority Coral** (`#b74742`): high-priority issue emphasis and rejection affordances.

### Neutral

- **Obsidian Field** (`#0b1114`): application background.
- **Graphite Panel** (`#111c20`): operational surfaces.
- **Low-Light Divider** (`#26383b`): dividers and quiet field boundaries.
- **Frosted Ink** (`#edf5f2`): reading text and headings.

**The Signal Is Sparse Rule.** Teal carries action and completion; coral only marks a real attention state. Never use colorful decoration to make routine content appear urgent.

## Typography

**Display Font:** Manrope, with Arial fallback.  
**Body Font:** Manrope, with Arial fallback.  
**Label/Mono Font:** DM Mono, monospace.

**Character:** Manrope keeps operational text plain-spoken and compact; DM Mono turns sources, labels, timestamps, and system states into factual evidence rather than decoration.

### Hierarchy

- **Display** (700, `clamp(32px, 4.3vw, 59px)`, 1.03): scene-level purpose and direction.
- **Title** (700, 21px): panel and task titles.
- **Body** (500, 15px, 1.7): explanations and resident-facing guidance.
- **Label** (400, 10px, `0.11em`, uppercase): source, category, and operational metadata.

## Layout

Desktop uses a floating top command bar and a centered, floating task deck at the bottom edge. Primary scenes cap at 1260px and compose one wide task canvas beside a focused evidence or action rail. The 26px grid gap and 25px panel padding create a compact ledger rhythm.

Below 900px, the task rail becomes a fixed bottom navigation, scene rails stack, and fields collapse to one column. The message stream remains scrollable inside a bounded conversation panel.

## Elevation & Depth

The system is flat at the panel layer. Borders, tonal surface shifts, and foreground/background contrast establish hierarchy. The floating command surfaces and ticket-confirmation dialog use a soft black ambient shadow to lift above the obsidian field.

## Shapes

Operational panels use 22px corners; buttons, inputs, chips, and compact system controls use 9px corners. Dividers are thin and low-light. Use blur only for floating command surfaces, never as decoration.

## Components

### Buttons

- **Shape:** confident 9px control corners.
- **Primary:** Signal Teal on white, `11px 15px` padding, used for decisive but reversible forward actions.
- **Ghost:** white with a Ledger Line border; use for return, defer, and cancellation actions.
- **Focus:** 3px teal focus outline with a 2px offset.

### Cards / Containers

- **Corner Style:** 16px.
- **Background:** Warm Panel on Mineral Paper.
- **Shadow Strategy:** none except temporary dialogs.
- **Border:** 1px Ledger Line.
- **Internal Padding:** 25px for panels.

### Inputs / Fields

- **Style:** white fields with a 1px Ledger Line border and 9px radius.
- **Focus:** teal outline; never rely only on color for state.

### Navigation

The top bar owns role switching; the left rail owns tasks. Selected rail items receive a teal-soft background and teal ink. On mobile, task navigation moves to the bottom edge.

### Signal Brief

The evidence rail groups actionable reports, announcements, and suppressed noise in a chronological digest. It explains the rule basis without revealing hidden reasoning or treating group chatter as a submitted ticket.

## Do's and Don'ts

### Do:

- **Do** make onboarding and Zalo workflows equally prominent in the primary navigation.
- **Do** attach sources or rules to agent-facing claims.
- **Do** keep a resident’s explicit confirmation between detection and ticket submission.
- **Do** preserve a visible ticket lifecycle for both resident and manager roles.

### Don't:

- **Don't** turn every message into a high-priority ticket signal.
- **Don't** build generic stat-card dashboards in place of the message or task canvas.
- **Don't** use gradients, glassmorphism, emoji iconography, or heavy decorative shadows.
- **Don't** communicate status by color alone.

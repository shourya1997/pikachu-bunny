---
version: "alpha"
name: "AuditOS"
description: "A hybrid Stripe + Linear + Revolut design system for a privacy-first financial audit app."
colors:
  primary: "#0A0A0B"
  primary-foreground: "#FFFFFF"
  accent: "#635BFF"
  accent-2: "#00D084"
  accent-3: "#00A3FF"
  danger: "#E5484D"
  warning: "#F5A524"
  success: "#12A150"
  background: "#F7F8FC"
  surface: "#FFFFFF"
  surface-raised: "#FBFCFF"
  border: "#E3E6EF"
  muted: "#687083"
  ink: "#111318"
typography:
  display:
    fontFamily: "Inter"
    fontSize: "3.1rem"
    fontWeight: 850
    lineHeight: "0.98"
    letterSpacing: "-0.055em"
  h1:
    fontFamily: "Inter"
    fontSize: "2rem"
    fontWeight: 820
    lineHeight: "1.08"
    letterSpacing: "-0.04em"
  h2:
    fontFamily: "Inter"
    fontSize: "1rem"
    fontWeight: 800
    lineHeight: "1.2"
  body:
    fontFamily: "Inter"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: "1.45"
  label:
    fontFamily: "Inter"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: "1"
    letterSpacing: "0.08em"
rounded:
  sm: "8px"
  md: "14px"
  lg: "22px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "36px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.pill}"
    padding: "12px 18px"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.pill}"
    padding: "12px 18px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "24px"
---

## Visual Theme & Atmosphere

AuditOS blends three cues:

- Stripe: premium financial precision, crisp hierarchy, strong conversion moments.
- Linear: calm issue tracking, status clarity, dense-but-readable workflows.
- Revolut: modern consumer fintech energy, friendly action surfaces, confidence around money.

The result should feel like a financial control room regular people can understand. Not a bank portal. Not a spreadsheet. Not crypto casino energy.

## Color Palette & Roles

- **Primary `#0A0A0B`:** High-trust ink for navigation, top actions, and important text.
- **Accent `#635BFF`:** Stripe-like precision accent for imports, packet generation, and selected states.
- **Accent 2 `#00D084`:** Consumer fintech progress and successful matches.
- **Accent 3 `#00A3FF`:** Informational links, source traces, and inspectable evidence.
- **Danger `#E5484D`:** Confirmed mismatch requiring action.
- **Warning `#F5A524`:** Needs review, especially tax or ambiguous findings.
- **Background `#F7F8FC`:** Cool off-white product canvas.
- **Surface `#FFFFFF`:** Cards, issue rows, source panels.

## Typography Rules

Use Inter or a close system equivalent. Headlines should be large and direct. Labels should be compact, uppercase, and status-oriented.

Write for the user who is worried about money. Prefer "PF missing for August" over "EPF contribution exception."

## Component Stylings

- **Issue rows:** Linear-style rows with severity, source badges, status, and next action.
- **Cards:** Stripe-like clean cards, subtle border, minimal shadow.
- **Action buttons:** Black primary for serious action. Purple for system actions. Green for safe progress.
- **Source badges:** Small colored chips for Bank, EPF/UAN, Salary, Form 16, AIS, Form 26AS.
- **Evidence drawer:** Opens from a finding and shows source snippets, rule trace, and redaction controls.
- **Packet composer:** Email preview plus attachment checklist, inspired by premium productivity tools.

## Layout Principles

Default product screen:

1. Top summary: financial truth score, clean months, open issues.
2. Left or center: issue queue ordered by severity.
3. Right: selected issue detail, evidence, next action.
4. Secondary view: timeline or source graph for inspection.

The app should make the first reasonable action obvious. Users should not need to understand the whole reconciliation engine to fix one problem.

## Depth & Elevation

Use shallow depth. Border-first, light shadows only for overlays and focused panels. Reserve strong color for actions and statuses.

## Do's and Don'ts

Do:

- Make mismatches feel actionable, not scary.
- Keep the evidence trail one click away.
- Make privacy and redaction visible.
- Separate "confirmed problem" from "needs review."
- Let the user export an HR/CA-ready packet.

Don't:

- Show dense tables by default.
- Use crypto-like gradients as the primary visual language.
- Hide critical findings in charts.
- Recommend a CA before the finding has evidence.
- Present generated text as legal or tax advice.

## Responsive Behavior

Desktop can use a three-pane workflow: issue queue, selected issue, evidence or packet panel. Mobile becomes a single issue feed with a bottom action area for the selected finding.

## Agent Prompt Guide

When generating UI, use this direction:

"Create a premium consumer fintech workflow UI inspired by Stripe, Linear, and Revolut. Use crisp off-white surfaces, black primary actions, purple system accents, green progress states, Linear-style issue rows, source badges, and an evidence drawer. The app helps Indian salaried employees reconcile bank, EPF/UAN, salary, Form 16, AIS, and Form 26AS records. It must feel trustworthy, modern, private, and action-oriented."

## Selected Product Direction

Use the **Financial Control Room** layout as the primary home screen:

- Show a top-level dashboard with truth score, clean months, open issues, ready packets, and local mode.
- Show priority findings in a central card so users immediately see what needs action.
- Show the recommended next action prominently, such as "Send HR email first."

Pair it with a **Timeline Investigator** drilldown:

- Every dashboard finding should open a month-wise detail view.
- The drilldown should explain what matched, what failed, and which documents produced the conclusion.
- Month-wise status should make it easy to answer, "When did my records stop agreeing?"

The final app direction is therefore **dashboard first, month-wise audit second, action packet third**.

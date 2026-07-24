# Pews early-access landing — Open Design direction

## Direction in one sentence

A calm, editorial, product-first early-access page that earns trust through clear language and source-grounded product evidence rather than social proof, feature-card volume, religious imagery, or startup theatrics.

## Conversion strategy

This is a lead-validation page, not a broad feature brochure.

1. **Name the weekly burden** — the hero frames Pews around keeping a church week coherent without losing the mission behind the work.
2. **Show product evidence early** — the first screen contains an explicitly labelled illustrative product preview grounded in real Pews routes.
3. **Organize around ministry rhythms** — plan, staff, care, and steward are more legible to church leaders than a wall of modules.
4. **Explain founder-market fit without mythology** — worship-pastor experience and twelve years in technology are presented as the reason for the product posture, not as a traction claim.
5. **Be explicit about the beta** — the page does not imply a free beta, exact price, guaranteed acceptance, or immediate access. The preferred-rate commitment is stated exactly where a prospect decides whether to submit.
6. **Use one conversion destination** — primary CTAs scroll to `#early-access`; Friday can replace the placeholder form with Formbricks without restructuring the page.

## Visual system

- **Mood:** warm, capable, quiet, operationally literate.
- **Memorable move:** an editorial serif promise sits beside a deliberately composed, slightly angled product surface. The page then shifts into a rectilinear operational system.
- **Palette:** Pews source informed the teal/navy/sage family (`#4A8B8C`, `#1B3A4B`, `#8FBCB0` are present in the application source). This direction deepens those roles into dark ink, restrained teal, cool paper, and a small warm amber signal. There is no purple gradient, glass, beige devotional wash, or multi-accent icon confetti.
- **Type:** Iowan Old Style/Palatino/Georgia for editorial display and Avenir Next/Segoe UI/Helvetica/Arial for UI and body. No network font dependency.
- **Surfaces:** flat or ring-bordered by default; one significant product-preview shadow is reserved for the hero.
- **Containment:** cards are used only for recognizable product objects, the preview frame, and the conversion form. Most explanation is carried by rules, type, and whitespace.
- **Motion:** only short state transitions and tab changes; no ambient hero choreography. `prefers-reduced-motion` removes smooth scrolling and the hero-frame rotation.

## Responsive composition

- **Desktop / 1440:** asymmetric two-column hero; full product frame with navigation rail; four-column principle strip; split product-evidence panels.
- **Tablet / 1024:** tighter split hero and app; principle strip becomes 2×2; evidence remains split where space permits.
- **Mobile / 390:** hero becomes single column; all hero actions become full-width; app navigation rail disappears; attention states move below their labels; the principle strip becomes a vertical editorial sequence; workflow rows become index + title + body; product tabs become stacked 44px controls; evidence copy and product UI stack; care preview shows one representative board column; form fields become one column.
- **Targets:** primary controls are at least 44px high; mobile fields/buttons are 48px high.

## Exact Open Design 0.13.0 materials used

Pinned repository: `/Users/citadel/Projects/Pews-ui-fleet/open-design`

Verified commit: `94f8ea2a15a536ba5857264091b985f212ac0705`

### Skills

- `skills/frontend-design/SKILL.md`
  - Used its requirement to commit to a specific visual direction, use honest content, create a self-contained artifact, avoid generic SaaS defaults, and self-review mobile/desktop behavior.
- `skills/web-design-guidelines/SKILL.md`
  - Used its layout, typography, motion, and accessibility checklist posture.
- `skills/ui-skills/SKILL.md`
  - Used as a catalogue-level reminder to keep the small UI pieces coherent under one constrained system.

### Craft

- `craft/anti-ai-slop.md`
  - Avoided default indigo, trust gradients, feature-icon walls, invented metrics, filler copy, and the standard feature/pricing/testimonial skeleton.
  - Added `data-od-id` to major sections and created a product-specific inline preview.
- `craft/typography.md`
  - Applied a two-font maximum, tight display leading, negative display tracking, tracked uppercase/mono eyebrows, and restrained line length.
- `craft/color.md`
  - Used neutral-dominant composition, one primary accent, restrained semantic colors, and high-contrast body/UI roles.
- `craft/accessibility-baseline.md`
  - Applied semantic landmarks, one H1, heading order, native controls, labels, keyboard-operable tabs, visible 3px focus, 44px mobile targets, and reduced-motion support.
- `craft/animation-discipline.md`
  - Limited state feedback to 100–150ms and removed transform/smooth-scroll behavior under reduced motion.
- `craft/form-validation.md`
  - Used native `required`/`type="email"`, `checkValidity()`/`reportValidity()`, retained input on validation, and avoided premature per-keystroke errors.

### Design templates

- `design-templates/waitlist-page/SKILL.md`
  - Used its anti-manipulation rules: no countdown, fake scarcity, fake social proof, or guarantee language; clear required email; polite status message; mobile-fit form.
  - The hardened waitlist template itself was **not copied**, because the brief requires a product-first multi-section validation page rather than its single-CTA minimal structure.
- `design-templates/web-prototype/SKILL.md`
  - Used self-contained HTML, semantic section composition, `data-od-id` targeting, and the mobile reflow/checklist discipline.
- `design-templates/saas-landing/SKILL.md`
  - Used its semantic HTML, product-specific copy, and design-system discipline.
  - Deliberately rejected its generic social-proof/pricing sequence because both would require unsupported claims.

### Design system

- `design-systems/wise/DESIGN.md`
- `design-systems/wise/tokens.css`
  - Used only transferable system principles: role-based token organization, neutral-dominant canvas, single-accent discipline, 8px-based rhythm, ring-first elevation, short interaction timing, and explicit mobile/tablet/desktop breakpoints.
  - Did **not** use Wise’s signature lime palette, extreme 900-weight display typography, proprietary typeface, pill-heavy component language, or layout. The Pews direction remains original and source-aligned.

## Product source evidence used

Read-only source root: `/Users/citadel/Projects/Pews-review/web/src`

Key routes inspected:

- `routes/dashboard/+page.svelte` — dashboard KPIs, at-risk people, activity, upcoming events, giving, check-ins, and engagement surfaces.
- `routes/dashboard/services/+page.svelte` — service types, statuses, dates/times, upcoming services, templates, song library, create/copy flow.
- `routes/dashboard/scheduling/needs/+page.svelte` — unfilled volunteer positions by date/team, urgency, people search, assignment.
- `routes/dashboard/care/+page.svelte` — visitor/pastoral/prayer/membership follow-up types, ownership, priorities, due dates, notes, and status board.
- `routes/dashboard/giving/+page.svelte` — donations, funds, statements, trends, recent donations, and setup state.
- `routes/dashboard/people/+page.svelte` — people records, status, tags, search/filter, bulk actions, and export.
- Route inventory under `routes/` — communications, check-ins, groups, events, prayer, media, sermons, streaming, rooms, reports, and settings.

## Claims ledger

| Landing-page statement | Evidence / status |
|---|---|
| Pews covers services, people, care follow-ups, volunteer scheduling, giving, and communications | Verified by current route/source inventory. |
| Services include types, dates/times, status, templates, songs, and copying | Verified in `dashboard/services/+page.svelte`. |
| Scheduling can surface unfilled positions by date/team and assign people | Verified in `dashboard/scheduling/needs/+page.svelte`. |
| Care work includes visitor, prayer, pastoral-care, hospital, counseling, membership, and general follow-ups with ownership, due dates, priority, status, and notes | Verified in `dashboard/care/+page.svelte`. |
| Giving includes donation records, funds, statements, recent activity, trends, and setup states | Verified in `dashboard/giving/+page.svelte` plus giving route inventory. |
| Founder spent years as a worship pastor and twelve years in technology | User-provided founder story; presented without embellishment. |
| Product is intended to meet church needs without unreasonable software bills diverting mission funds | User-provided founder motivation; phrased as product posture, not a price/outcome claim. |
| Accepted beta participants receive a preferred, committed early-access rate once pricing is finalized | Required program statement; no number or free-beta implication added. |
| Illustrative UI values/names | Explicitly labelled “illustrative” and “sample data”; not presented as actual customer data or proof. |

### Claims intentionally omitted

No customers, customer logos, testimonials, funding, traction, usage counts, outcomes, integrations, security/compliance certifications, migration guarantees, exact pricing, free-beta promise, release date, uptime, team size, or competitive-superiority claims appear in the prototype.

## Form handoff

- Primary destination: `#early-access`.
- Placeholder form ID: `beta-form`.
- The current submit handler validates required fields, prevents network submission, and shows: “Prototype only: the request was not sent. Friday will connect this form to Formbricks.”
- Friday can replace the `<form class="form-card">…</form>` block or its submit handler with the approved Formbricks embed/SDK implementation.
- No Formbricks, production, DNS, GitHub, or Pews source changes were made.

## Accessibility notes

- WCAG-AA-oriented color choices; automated contrast should still be rerun after any brand-color changes.
- Visible `:focus-visible` outline with a high-contrast warm focus color.
- Skip link and semantic header/nav/main/section/footer landmarks.
- Native button/link/form controls and keyboard tab pattern with arrow/Home/End navigation.
- Explicit labels, native required/email constraints, live status region.
- Reduced-motion query removes smooth scroll and transform motion.
- No content depends on color alone: all states include text labels.

## Prototype boundary

This is an isolated landing-page direction, not production Pews UI and not a live signup flow. It is intentionally self-contained, has no external dependencies, and is safe to open locally.
---
name: vsl-funnel-structure
description: Load when generating or editing VSL funnels with video-first conversion flow.
---

# VSL Funnel Structure

## Core pages
1. VSL page
   - Big headline and clear promise.
   - `VideoEmbed` as the primary conversion asset.
   - Benefit bullets and proof below video.
   - One primary CTA with no navigation distractions.

2. Order page
   - Reinforce buying momentum.
   - Offer stack and price clarity.
   - Guarantee reminder.
   - Placeholder area for external checkout/calendar embed.
   - Single action CTA.

3. Thank You page
   - Confirmation headline.
   - Exact next steps in concise numbered format.
   - Set expectation for delivery or access timing.

## Optional pages
4. Upsell page (OTO)
   - One relevant add-on offer with yes/no decision.

5. Downsell page
   - Lower-commitment alternative for upsell declines.

## Route expectations
- `/vsl` entry page for VSL flow.
- `/order` and `/thank-you` always present.
- `/upsell` and `/downsell` only when selected.
- `App.tsx` must be rewritten when routes change.

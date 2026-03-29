---
name: lead-magnet-funnel-structure
description: Load when generating or editing lead magnet funnels focused on opt-in and warm-up conversion.
---

# Lead Magnet Funnel Structure

## Core pages
1. Opt-in page
   - Specific promise of the free asset.
   - Brief supporting copy and a single form placeholder.
   - One CTA only, no navigation distractions.

2. Thank You page
   - Confirm delivery and next step.
   - Tell the user where/how to access the lead magnet.

## Optional pages
3. Bridge page
   - Story-based transition from free value to paid solution.
   - CTA that introduces the paid offer page.

4. Offer page
   - Warmer sales message than cold-traffic VSL.
   - Clear offer breakdown, proof, pricing, and CTA.

## Route expectations
- `/` is opt-in entry point.
- `/thank-you` always present.
- `/bridge` and `/offer` appear only when selected.
- Always rewrite `App.tsx` when adding/removing funnel steps.

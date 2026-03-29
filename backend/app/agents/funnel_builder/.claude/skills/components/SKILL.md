---
name: component-inventory
description: Load when selecting components for page composition and deciding layout patterns.
---

# Component Usage Guide

## UI components in this project
- `Button`: primary CTA actions. Use large sizing for main conversion buttons.
- `Card`: offer blocks, testimonial containers, pricing summaries.
- `Accordion`: FAQs and objection handling sections only.
- `Tabs`: package comparisons or tier layouts.
- `Badge`: labels like "Most Popular" or section tags.
- `Input`, `Textarea`, `Label`: form UI or placeholders for embeds.
- `Separator`: visual separators between major sections.
- `TextAnimate`: headline reveal effect. Use at most once per page.

## Funnel-specific components
- `VideoEmbed`
  - props: `{ url: string, placeholder?: string }`
  - supports YouTube, Vimeo, Wistia, Loom
  - pass empty string to render placeholder state

- `CountdownTimer`
  - props: `{ targetDate?: string, minutes?: number, label?: string, onExpire?: () => void }`
  - use `minutes` for evergreen urgency
  - use `targetDate` for fixed launch deadlines

## Icons and utility imports
- `lucide-react`: `Check`, `Shield`, `Star`, `Clock`, `ChevronDown`, etc.
- `@/lib/utils`: `cn` helper for class composition

## Import constraints
- UI imports: `@/components/ui/{kebab-name}`
- Funnel imports: `@/components/funnel/{name}`
- Do not reference any `magic/` directory in this project.

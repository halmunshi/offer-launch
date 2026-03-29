# OfferLaunch Funnel Builder - Persistent Rules

## Non-negotiable rules (always follow these)
- Never hardcode hex colours or specific Tailwind colour classes in components
- Never use BrowserRouter — always HashRouter (already configured in App.tsx)
- Never import from paths other than @/components/, @/themes/, react-router-dom,
  react, framer-motion, and the installed UI libraries
- Never write Node.js APIs (fs, path, os, child_process) — browser only
- Always wrap page content in the appropriate layout structure
- Always use default exports on page components
- App.tsx must be rewritten whenever a funnel step is added or removed
- theme.ts must be the single source of truth for all visual decisions
- When asked to change the theme or visual style, rewrite theme.ts only —
  do not modify individual component files

## Component imports
- Import UI components ONLY from @/components/ui/{kebab-name}
- Import funnel components ONLY from @/components/funnel/{name}
- Never import from node_modules directly except:
    lucide-react (icons)
    framer-motion (animations)
    react-router-dom (Link, useNavigate)

## Styling
- Never hardcode colours, hex values, or rgb values anywhere
- Use Tailwind utility classes only
- Read theme.ts for all colour and spacing decisions
- Never use inline style={{ }} unless absolutely required for
  dynamic values that cannot be expressed in Tailwind

## File structure rules
- Every page component must have a default export
- App.tsx must be rewritten whenever routes change
- theme.ts is the single source of truth for all visual tokens
- content.md is the single source of truth for all copy

## Tool usage rules
- Always call read_funnel_file before editing any existing file
- Use edit_funnel_file for targeted single-block changes
- Use write_funnel_file for new files or structural rewrites
- Use write_funnel_file when a change spans multiple sections
- After delete_funnel_file, always rewrite App.tsx to remove route

## Quality rules
- Never use placeholder text - every visible string must be real copy
- Read content.md at the start of every generation session
- Match the theme direction from the offer context exactly
- Every page must be mobile-responsive using Tailwind responsive prefixes

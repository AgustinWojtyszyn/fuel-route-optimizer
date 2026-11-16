# Fuel Route Optimizer — visual system

This is the locked direction for future Hallmark redesigns. It supersedes the former light, screenshot-led landing system.

## Two distinct experiences

**Landing (/):** Editorial, dark-first introduction to the range and fuel assumptions. Its signature is a bespoke, curved six-milestone journey **schematic** illustrating the 500-mile assumption, while the separate interactive section demonstrates arithmetic-only distance examples. Never embed the planner itself, a real-map imitation, screenshot of the application, claimed real road, imaginary station, testimonials or fabricated performance metrics.

**Planner (/demo/):** A dense, usable cartographic workspace with city autocomplete, road map, route stats, estimated purchases and explicit safety caveats. Do not rework the Django backend to polish the UI.

## Visual language

- Dark is the first-load default; light mode is selected manually using the shared toggle. Store the choice as `fuel-route-theme`.
- English is the first-load default. Spanish, French and Portuguese are optional, manual and persistent via `fuel-route-language-v2`.
- The old Flaticon fuel-pump asset is permanently retired. Keep the original typographic Fuel/Route wordmark and locally owned FR SVG favicon. Use Bricolage Grotesque for display and Manrope for prose and controls; prefer locally hosted fonts.
- Dark charcoal-green surfaces and warm amber actions. Light theme uses warm off-white and dark text. Use accessible contrast and high-visibility keyboard focus.
- Clear typographic hierarchy, generous negative space, factual illustrations and lightly ruled information groups. Avoid generic three-card grids, gradients, glow effects, eyebrow labels and ornamental metrics.
- Keep user-facing copy brief. Every numeric claim must derive from the real application or the explicit 500-mile / 10 mpg assumptions. The hero shows 0–500 miles in five equal-mileage segments along a symbolic curved path. It must be explicitly labelled as schematic, not an actual driving route; it makes no routing API calls.
- Use restrained Hallmark interaction polish: consistent hover, keyboard focus, mobile spacing and accessible, genuinely functional distance presets. Never add icons merely for decoration.
- The landing stylesheet is `routes/static/routes/landing.css`; the planner uses `routes/static/routes/product.css`, `tokens.css` and `theme.css`. Both load `theme.js`.

## Quality and functionality

- No removal of current links, interactive elements, map controls, destination field, translations, provider integrations, calculated fuel stops, cost breakdowns or warnings.
- No claims of verified pump entrances or live prices: positions are city-level approximations and price observations are undated.
- Mobile from 320px, 1280px/1440px desktop, and 1920px widescreen, with no horizontal document scrolling.
- Respect `prefers-reduced-motion`, semantic HTML, readable labels and keyboard navigation.
- Before publishing, run Django tests, Node JavaScript syntax checks and the Hallmark visual audit where a local browser is available. Do not claim a successful screenshot/render audit without actually performing it.

## Acceptance

A reviewer can understand the product without seeing the same map twice; the landing and tool remain recognizable as one brand, and either page can switch themes and language without breaking the route calculator.

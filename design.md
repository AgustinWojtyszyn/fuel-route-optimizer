# Fuel Route Optimizer visual system

Both routes use the same system: mineral paper, navy ink, a cobalt action, and a real road map. The existing pump logo is retained. Bricolage Grotesque provides the display face; Manrope handles controls and reading. Both variable fonts are self-hosted with their OFL licenses.

The canonical files are `routes/static/routes/tokens.css`, `base.css`, and `product.css`. Root CSS files are compatibility imports. The existing Hallmark scaffold has been integrated; it has not been reinstalled. No UI framework is required.

The landing opens with a short product statement and a real screenshot of the empty planner. It never presents test fixtures, prices, a claimed computed route, or commercial source data. Its factual capability section stays compact rather than multiplying the same facts across marketing sections.

The planner is a continuous workspace: input rail on the left, map on the right, numeric results below. On narrow screens the form precedes the map. Inputs have 48px targets, visible focus and keyboard city selection. Async regions show progress, empty, error and successful states. Result figures always distinguish new purchases from fuel already in the starting tank.

Use semantic color tokens, the shared spacing scale, tabular numerals for comparable values, sentence case for labels, and reduced motion fallbacks. Keep the vehicle assumptions, source caveats, multilingual catalogs, city lookup, endpoint payloads, and mapping providers intact.

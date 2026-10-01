// SpiderGPT screen module: pricing
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pagePricing(...(ctx.args || []));
}

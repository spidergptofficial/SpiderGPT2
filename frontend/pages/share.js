// SpiderGPT screen module: share
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageShare(...(ctx.args || []));
}

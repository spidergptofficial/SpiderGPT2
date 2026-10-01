// SpiderGPT screen module: settings
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageSettings(...(ctx.args || []));
}

// SpiderGPT screen module: history
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageHistory(...(ctx.args || []));
}

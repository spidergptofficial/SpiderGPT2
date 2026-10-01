// SpiderGPT screen module: usage
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageUsage(...(ctx.args || []));
}

// SpiderGPT screen module: profile
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageProfile(...(ctx.args || []));
}

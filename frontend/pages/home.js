// SpiderGPT screen module: home
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageHome(...(ctx.args || []));
}

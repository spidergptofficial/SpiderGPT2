// SpiderGPT screen module: saved
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageSaved(...(ctx.args || []));
}

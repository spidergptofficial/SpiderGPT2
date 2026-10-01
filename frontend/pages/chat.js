// SpiderGPT screen module: chat
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageChat(...(ctx.args || []));
}

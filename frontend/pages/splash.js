// SpiderGPT screen module: splash
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageSplash(...(ctx.args || []));
}

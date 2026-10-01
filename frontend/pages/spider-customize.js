// SpiderGPT screen module: spider-customize
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageCustomize(...(ctx.args || []));
}

// SpiderGPT screen module: themes
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageThemes(...(ctx.args || []));
}

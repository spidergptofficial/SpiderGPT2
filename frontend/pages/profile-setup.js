// SpiderGPT screen module: profile-setup
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageProfileSetup(...(ctx.args || []));
}

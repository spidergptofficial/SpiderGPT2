// SpiderGPT screen module: billing
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageBilling(...(ctx.args || []));
}

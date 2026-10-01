// SpiderGPT screen module: payment-success
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageSuccess(...(ctx.args || []));
}

// SpiderGPT screen module: checkout
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageCheckout(...(ctx.args || []));
}

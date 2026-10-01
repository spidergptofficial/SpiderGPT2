// SpiderGPT screen module: spider
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageSpider(...(ctx.args || []));
}

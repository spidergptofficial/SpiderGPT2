// SpiderGPT screen module: create-spider
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageCreateSpider(...(ctx.args || []));
}

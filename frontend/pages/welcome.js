// SpiderGPT screen module: welcome
// The application shell and backend state remain centralized in app.js.
export function renderScreen(ctx) {
  return ctx.pageWelcome(...(ctx.args || []));
}

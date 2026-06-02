// Minimal Worker — all requests served from [assets] directory
export default {
  async fetch(request, env, ctx) {
    // Assets are served automatically by the runtime
    // This handler only runs if no asset matches
    const url = new URL(request.url);

    // Redirect /index to /
    if (url.pathname === "/index" || url.pathname === "/index.html") {
      return Response.redirect(url.origin + "/", 301);
    }

    // 404 for everything else
    return new Response("Not found", { status: 404 });
  },
};

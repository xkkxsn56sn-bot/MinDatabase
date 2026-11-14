// Worker del sito pubblicato con Cloudflare Workers Static Assets
// (wrangler.site.toml). Riproduce il comportamento di GitHub Pages.
//
// Con html_handling = "none" gli asset rispondono solo al percorso esatto:
// /scholars.html risponde 200 senza rinvii, come su GitHub Pages, e i link
// interni del sito, che usano tutti .html, non fanno salti. Questo Worker
// gira soltanto quando nessun file corrisponde al percorso richiesto, e
// ricostruisce il resto:
//
//   /x   -> serve x.html (200), se esiste
//   /x   -> 301 a /x/, se esiste x/index.html (es. /glossary -> /glossary/)
//   /x/  -> serve x/index.html (200)
//   altrimenti la pagina 404.html del sito, con stato 404
//
// La query string viaggia nel rinvio (gli UTM della newsletter); l'hash non
// arriva al server e il browser lo conserva da solo nel 301.

const NOT_FOUND_PAGE = "/404.html";

async function findAsset(env, request, url, pathname) {
  const target = new URL(url);
  target.pathname = pathname;
  const response = await env.ASSETS.fetch(new Request(target, request));
  // 304: l'asset esiste e il browser ne ha gia' una copia valida.
  return response.status === 200 || response.status === 304 ? response : null;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const lastSegment = path.slice(path.lastIndexOf("/") + 1);

    if (path.endsWith("/")) {
      const index = await findAsset(env, request, url, `${path}index.html`);
      if (index) return index;
    } else if (!lastSegment.includes(".")) {
      const page = await findAsset(env, request, url, `${path}.html`);
      if (page) return page;
      const folder = await findAsset(env, request, url, `${path}/index.html`);
      if (folder) {
        const location = new URL(url);
        location.pathname = `${path}/`;
        return Response.redirect(location.toString(), 301);
      }
    }

    const notFound = await env.ASSETS.fetch(
      new Request(new URL(NOT_FOUND_PAGE, url), { method: "GET" }),
    );
    return new Response(request.method === "HEAD" ? null : notFound.body, {
      status: 404,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "max-age=600",
      },
    });
  },
};

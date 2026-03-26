/**
 * Cloudflare Worker — Bitunix API Reverse Proxy
 * Deploy ke: https://dash.cloudflare.com → Workers & Pages → Create Worker
 *
 * Cara pakai:
 *   1. Deploy worker ini
 *   2. Set BITUNIX_GATEWAY_URL=https://your-worker.workers.dev di Railway/.env
 *   3. (Optional) Set GATEWAY_SECRET di Worker env + BITUNIX_GATEWAY_SECRET di Railway
 *
 * PENTING: Di Cloudflare Dashboard → Security → Bots → matikan "Bot Fight Mode"
 * agar request dari Railway/server tidak diblokir challenge page.
 */

const TARGET = "https://fapi.bitunix.com";

// Header yang dikirim ke Bitunix — pakai browser UA supaya tidak diblokir
const FORWARD_HEADERS_WHITELIST = [
  "content-type",
  "api-key",
  "nonce",
  "timestamp",
  "sign",
];

export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
          "Access-Control-Allow-Headers": "*",
        },
      });
    }

    // Optional: secret key check
    if (env.GATEWAY_SECRET) {
      const clientSecret = request.headers.get("x-gateway-secret");
      if (clientSecret !== env.GATEWAY_SECRET) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      }
    }

    const url = new URL(request.url);
    const targetUrl = TARGET + url.pathname + url.search;

    // Hanya forward header yang diperlukan Bitunix, buang sisanya
    const newHeaders = new Headers();
    for (const key of FORWARD_HEADERS_WHITELIST) {
      const val = request.headers.get(key);
      if (val) newHeaders.set(key, val);
    }
    // Pakai browser User-Agent agar tidak diblokir Bitunix
    newHeaders.set(
      "User-Agent",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    );
    newHeaders.set("Accept", "application/json");
    newHeaders.set("Origin", "https://www.bitunix.com");
    newHeaders.set("Referer", "https://www.bitunix.com/");

    const newRequest = new Request(targetUrl, {
      method: request.method,
      headers: newHeaders,
      body:
        request.method !== "GET" && request.method !== "HEAD"
          ? request.body
          : undefined,
    });

    try {
      const response = await fetch(newRequest);
      const responseBody = await response.text();

      return new Response(responseBody, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          "Content-Type": response.headers.get("Content-Type") || "application/json",
          "Access-Control-Allow-Origin": "*",
          // Beritahu Cloudflare ini bukan halaman HTML biasa — skip bot check
          "X-Robots-Tag": "noindex",
        },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
};

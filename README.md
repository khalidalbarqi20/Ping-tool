# Gaming Server Monitor v14

## What this version adds
- Browser-originated RTT measurement to a user-deployed Cloudflare Worker WebSocket echo endpoint.
- Measurement follows the device's currently active Internet connection (Wi-Fi, cellular, or Ethernet).
- Displays RTT, rolling average, approximate jitter, and sample count.
- Clearly labels this as **nearest Cloudflare Edge RTT**, not game-server ping.
- Preserves the existing game/region reference metadata and refuses to invent per-game values.

## Deploy the edge probe (free tier)
1. Sign in to Cloudflare Dashboard.
2. Open Workers & Pages -> Create -> Worker.
3. Create a Worker named `gaming-ping-edge-probe`.
4. Replace the starter code with the complete contents of `probe-worker/worker.js`.
5. Deploy. Keep the default `workers.dev` subdomain enabled.
6. The endpoint will be `wss://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/ws`.
7. Open the Render-hosted Gaming Server Monitor, paste that URL into the probe field, and press Save and Start once. It is saved in that browser and reconnects on later visits.
8. Health check: `https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/health`.

## Important accuracy boundary
Cloudflare Workers run on Cloudflare's edge network and this endpoint measures the route from the browser to the Cloudflare edge location selected for that request. It does not pin a Worker to Bahrain, Europe, or Asia and does not measure a game match server. Do not label this result as PUBG/Fortnite/EA FC/COD ping.

## Existing Render service
The existing Python service remains the static/config backend. It does not perform client measurements and does not need a paid Render plan for this feature. Keep Render's current service and let GitHub auto-deploy after pushing the updated files.

## Free-tier considerations
Cloudflare Workers supports WebSockets. Free Workers have usage limits; check current dashboard limits and usage. The browser sends roughly one small WebSocket message per second while the page is open. This is an on-demand client probe, not a 24/7 background monitor.

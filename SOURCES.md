# Sources and measurement semantics

- Epic Games regional ping endpoint reference: https://www.epicgames.com/help/c-34254770/c-37371353/a22355516
- Cloudflare WebSockets support: https://developers.cloudflare.com/network/websockets/
- Cloudflare Workers WebSocket runtime: https://developers.cloudflare.com/workers/runtime-apis/websockets/
- Cloudflare Workers limits: https://developers.cloudflare.com/workers/platform/limits/

The new RTT value is measured by the browser to the configured Cloudflare Worker WebSocket endpoint. It is not a game-server measurement. Region-specific game ping remains unavailable until a genuine browser-reachable probe is deployed in that region or the game publisher exposes a suitable measurement endpoint.

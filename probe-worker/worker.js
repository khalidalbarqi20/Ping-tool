/**
 * Global edge RTT echo probe.
 * This measures browser <-> nearest Cloudflare edge, NOT a game match server.
 */
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '*';
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ok:true, service:'gaming-ping-edge-probe', scope:'nearest-cloudflare-edge', timestamp:Date.now()}), {
        headers: {'content-type':'application/json; charset=utf-8','access-control-allow-origin':origin,'cache-control':'no-store'}
      });
    }
    if (url.pathname !== '/ws') return new Response('Not found', {status:404});
    if (request.headers.get('Upgrade') !== 'websocket') return new Response('WebSocket upgrade required', {status:426});
    const pair = new WebSocketPair();
    const client = pair[0];
    const server = pair[1];
    server.accept();
    server.addEventListener('message', event => {
      // Echo payload immediately. Client measures elapsed time using performance.now().
      try { server.send(event.data); } catch (_) {}
    });
    server.addEventListener('close', () => { try { server.close(); } catch (_) {} });
    server.addEventListener('error', () => { try { server.close(1011, 'probe error'); } catch (_) {} });
    return new Response(null, {status:101, webSocket:client});
  }
};

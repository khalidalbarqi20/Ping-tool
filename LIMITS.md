# v14 limitations

- Cloudflare Worker routing is edge-based; this setup does not pin a worker to a requested game region.
- RTT is browser-to-Cloudflare-edge, not ICMP ping and not game-match ping.
- Browser JavaScript cannot create raw ICMP/UDP sockets to arbitrary game server IPs.
- Measurement runs only while the page is active; mobile browsers may throttle timers in background tabs.
- The probe URL must be configured once per browser/device. localStorage is device/browser-specific.
- The Worker free plan has quotas and limits; see https://developers.cloudflare.com/workers/platform/limits/.

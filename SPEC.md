# v14 measurement specification

1. The browser opens a secure WebSocket (`wss://`) to a user-configured echo probe.
2. The browser timestamps each outgoing message with `performance.now()`.
3. The probe echoes the same message immediately.
4. The browser calculates round-trip time (RTT) locally.
5. Average and jitter are calculated from the last 60 successful samples.
6. The measurement is explicitly labeled nearest Cloudflare Edge RTT.
7. No result is presented as game-match ping.
8. Game region cards remain unavailable until region-specific probes are independently verified.

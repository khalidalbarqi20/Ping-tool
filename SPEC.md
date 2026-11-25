# v15.0 measurement specification

1. Existing Cloudflare WebSocket RTT remains separate and unchanged.
2. Regional HTTP test is initiated manually by the user.
3. Exactly 16 AWS region IDs are allowlisted in `regions.json`; Israel `il-central-1` is not present and is explicitly listed as excluded in API metadata.
4. Three GET fetch attempts per region; maximum six concurrent requests; 2500 ms timeout.
5. Requests use `mode: no-cors`, `cache: no-store`, `credentials: omit`; each request includes a unique query value.
6. Timing ends when fetch resolves, i.e. response availability to the browser, not body completion or proof of successful HTTP status.
7. Display latest successful duration, median of successful durations, sample counts and failed attempts. Failed/time-out requests are unavailable, never zero.
8. Results are regional HTTP estimates, not game-server RTT, ICMP ping, UDP packet loss or matchmaking quality.
9. Test aborts when stopped or when the document becomes hidden.

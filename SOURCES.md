# Sources and measurement boundaries

- AWS regional endpoint list: https://docs.aws.amazon.com/general/latest/gr/rande.html
- AWS region reference and opt-in status: https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-regions.html
- Instant Speed Test methodology: https://instantspeedtest.net/ar/how-we-test/
- Instant Speed Test PUBG Mobile method example: https://instantspeedtest.net/ar/gamer-hub/pubg-mobile-ping-test/

The browser measures HTTP fetch timing to regional AWS DynamoDB API endpoints. This is not the game match server and does not measure UDP packet loss. Browser no-cors responses are opaque; status codes are not visible.

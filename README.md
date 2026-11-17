# OOTTO Instagram MCP (starter)

This is a starter MCP server for Claude using the Python MCP SDK and Streamable HTTP.

## Important prerequisites

- An Instagram **Professional** account (Business or Creator).
- A Meta developer app configured for the Instagram API product/use case.
- Required permissions and app review/Advanced Access where applicable.
- A valid access token and the Instagram professional account ID.
- Publicly reachable HTTPS media URLs for publishing images/Reels.

The starter uses a server-side access token from Render environment variables. Do not paste tokens into chat, GitHub, source files, or client-side code.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; on macOS/Linux use: cp .env.example .env
python server.py
```

Set the variables from `.env` in your shell or use a local dotenv loader before running. The MCP endpoint is `/mcp`.

## Deploy on Render

1. Push this project to a GitHub repository named `OOTTO`.
2. In Render choose **New + → Web Service** and connect that repository.
3. Render can use `render.yaml` (Blueprint) or enter:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python server.py`
4. Add environment variables in Render:
   - `META_GRAPH_VERSION`
   - `INSTAGRAM_ACCESS_TOKEN`
   - `INSTAGRAM_USER_ID`
5. Deploy. Your MCP URL will be `https://YOUR-SERVICE.onrender.com/mcp`.

## Connect Claude

In Claude, add a custom connector / remote MCP server and use the deployed HTTPS `/mcp` URL. Exact menu labels depend on your Claude plan and product.

## Tools included

- `instagram_profile`
- `instagram_recent_media`
- `instagram_media_insights`
- `instagram_account_insights`
- `instagram_publish_image`
- `instagram_publish_reel`
- `instagram_list_comments`
- `instagram_reply_to_comment`
- `instagram_get_conversations`
- `instagram_get_conversation_messages`
- `instagram_send_dm`
- `health_check`

## API and policy caveats

This is a starter, not a production-ready multi-user OAuth integration. It uses one server-side account token. Messaging and publishing require the right account type, permissions, app configuration, and Meta policy eligibility. DM automation is constrained by Meta's messaging window, recipient eligibility, and platform rules; it is not an unrestricted cold-DM/bulk-messaging tool.

The Graph API version is configurable. Confirm the currently supported version and the required permissions/metrics in Meta's official docs before production. Insights metrics vary by media type, API version, and account eligibility. The initial code is intentionally a basic scaffold and may need small API-specific adjustments after Meta app setup/testing.

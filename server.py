import os
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OOTTO", stateless_http=True, json_response=True)

GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v23.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

def _token() -> str:
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("INSTAGRAM_ACCESS_TOKEN is not configured on the server.")
    return token

def _ig_user_id() -> str:
    user_id = os.getenv("INSTAGRAM_USER_ID")
    if not user_id:
        raise RuntimeError("INSTAGRAM_USER_ID is not configured on the server.")
    return user_id

async def graph_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = dict(params or {})
    query["access_token"] = _token()
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{GRAPH_BASE}/{path.lstrip('/')}", params=query)
        response.raise_for_status()
        return response.json()

async def graph_post(path: str, data: dict[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    payload["access_token"] = _token()
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{GRAPH_BASE}/{path.lstrip('/')}", data=payload)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def instagram_profile() -> dict[str, Any]:
    """Read the connected Instagram professional account profile."""
    return await graph_get(_ig_user_id(), {"fields": "id,username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url"})

@mcp.tool()
async def instagram_recent_media(limit: int = 10) -> dict[str, Any]:
    """Read recent Instagram media. Limit is clamped to 1..50."""
    limit = max(1, min(limit, 50))
    return await graph_get(f"{_ig_user_id()}/media", {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "limit": limit,
    })

@mcp.tool()
async def instagram_media_insights(media_id: str) -> dict[str, Any]:
    """Read insights for one media item. Available metrics depend on media type and API permissions."""
    return await graph_get(f"{media_id}/insights", {"metric": "reach,impressions,likes,comments,saved,shares"})

@mcp.tool()
async def instagram_account_insights(period: str = "day") -> dict[str, Any]:
    """Read account insights. Supported period commonly includes day or week; metrics depend on account/API access."""
    return await graph_get(f"{_ig_user_id()}/insights", {
        "metric": "reach,views,profile_views,total_interactions",
        "period": period,
    })

@mcp.tool()
async def instagram_publish_image(image_url: str, caption: str = "") -> dict[str, Any]:
    """Publish an image from a publicly accessible HTTPS URL to the connected account."""
    created = await graph_post(f"{_ig_user_id()}/media", {
        "image_url": image_url,
        "caption": caption,
    })
    creation_id = created.get("id")
    if not creation_id:
        return created
    return await graph_post(f"{_ig_user_id()}/media_publish", {"creation_id": creation_id})

@mcp.tool()
async def instagram_publish_reel(video_url: str, caption: str = "") -> dict[str, Any]:
    """Publish a Reel from a publicly accessible HTTPS video URL."""
    created = await graph_post(f"{_ig_user_id()}/media", {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
    })
    creation_id = created.get("id")
    if not creation_id:
        return created
    # Meta media processing can be asynchronous. Check status before publishing.
    status = await graph_get(creation_id, {"fields": "status_code"})
    if status.get("status_code") not in ("FINISHED", "PUBLISHED"):
        return {"creation_id": creation_id, "status": status, "message": "Media is still processing; retry publishing after processing finishes."}
    return await graph_post(f"{_ig_user_id()}/media_publish", {"creation_id": creation_id})

@mcp.tool()
async def instagram_list_comments(media_id: str, limit: int = 25) -> dict[str, Any]:
    """Read comments on a media item."""
    limit = max(1, min(limit, 100))
    return await graph_get(f"{media_id}/comments", {"fields": "id,text,username,timestamp", "limit": limit})

@mcp.tool()
async def instagram_reply_to_comment(comment_id: str, message: str) -> dict[str, Any]:
    """Reply to a comment. This sends a public reply on Instagram."""
    return await graph_post(f"{comment_id}/replies", {"message": message})

@mcp.tool()
async def instagram_send_dm(recipient_igsid: str, message: str) -> dict[str, Any]:
    """Send a DM to a user who is eligible under Meta's messaging rules and has an Instagram-scoped ID."""
    payload = {
        "recipient": json_dumps({"id": recipient_igsid}),
        "message": json_dumps({"text": message}),
        "messaging_type": "RESPONSE",
    }
    return await graph_post(f"{_ig_user_id()}/messages", payload)

def json_dumps(value: Any) -> str:
    import json
    return json.dumps(value, separators=(",", ":"))

@mcp.tool()
async def instagram_get_conversations(limit: int = 20) -> dict[str, Any]:
    """List conversations available to the connected professional account, subject to messaging permissions."""
    limit = max(1, min(limit, 50))
    return await graph_get(f"{_ig_user_id()}/conversations", {"platform": "instagram", "limit": limit})

@mcp.tool()
async def instagram_get_conversation_messages(conversation_id: str, limit: int = 25) -> dict[str, Any]:
    """Read messages from a conversation available to the connected professional account."""
    limit = max(1, min(limit, 100))
    return await graph_get(conversation_id, {"fields": "messages.limit(" + str(limit) + "){id,created_time,from,to,message}"})

@mcp.tool()
async def health_check() -> dict[str, str]:
    """Check that the OOTTO MCP service is running. Does not test Meta credentials."""
    return {"status": "ok", "service": "OOTTO MCP"}

if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = int(os.getenv("PORT", "10000"))
    mcp.run(transport="streamable-http")

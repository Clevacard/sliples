#!/usr/bin/env python3
"""
Example MCP client for Sliples streaming API.

Demonstrates:
- Listing active sessions with filters
- Connecting to WebSocket stream
- Processing events in real-time
- Error monitoring and rage-click detection
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional, Dict, List
from collections import defaultdict

try:
    import aiohttp
    import websockets
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install aiohttp websockets")
    sys.exit(1)


class SliplesStreamClient:
    """Client for Sliples streaming API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        ws_url: str = "ws://localhost:8000",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.ws_url = ws_url

    async def list_sessions(
        self,
        domain: Optional[str] = None,
        user_agent: Optional[str] = None,
        max_age_seconds: Optional[int] = None,
        status: str = "recording",
        limit: int = 50,
    ) -> List[Dict]:
        """List active recording sessions."""
        params = {
            "status": status,
            "limit": limit,
        }
        if domain:
            params["domain"] = domain
        if user_agent:
            params["user_agent"] = user_agent
        if max_age_seconds:
            params["max_age_seconds"] = max_age_seconds

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/stream/sessions",
                headers={"X-API-Key": self.api_key},
                params=params,
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"API error: {resp.status} - {await resp.text()}")
                return await resp.json()

    async def get_stream_stats(self) -> Dict:
        """Get statistics about active streams."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/stream/stats",
                headers={"X-API-Key": self.api_key},
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"API error: {resp.status} - {await resp.text()}")
                return await resp.json()

    async def stream_session(
        self,
        session_id: str,
        include_historic: bool = True,
        event_callback: Optional[callable] = None,
    ):
        """Stream events from a session in real-time."""
        uri = f"{self.ws_url}/api/v1/stream/sessions/{session_id}/ws"
        uri += f"?include_historic={str(include_historic).lower()}"

        async with websockets.connect(
            uri,
            extra_headers={"X-API-Key": self.api_key},
        ) as websocket:

            # Keepalive task
            async def keepalive():
                while True:
                    await asyncio.sleep(30)
                    try:
                        await websocket.send("ping")
                    except:
                        break

            keepalive_task = asyncio.create_task(keepalive())

            try:
                async for message in websocket:
                    if message == "pong":
                        continue

                    data = json.loads(message)

                    if event_callback:
                        await event_callback(data)

                    # Auto-exit on session stopped
                    if data.get("type") == "session_stopped":
                        print(f"\n✓ Session stopped: {data['event']['event_count']} total events")
                        break

            except websockets.exceptions.ConnectionClosed as e:
                print(f"\n⚠️  Connection closed: {e}")
            finally:
                keepalive_task.cancel()


class EventAnalyzer:
    """Analyzes events for patterns and issues."""

    def __init__(self):
        self.event_count = 0
        self.events_by_type = defaultdict(int)
        self.click_history = []  # (timestamp, target) tuples
        self.errors = []
        self.navigation_path = []

    async def analyze(self, message: Dict):
        """Process and analyze a message."""
        msg_type = message.get("type")

        if msg_type == "connected":
            session = message.get("session", {})
            print(f"\n✓ Connected to session: {session.get('name')}")
            print(f"  URL: {session.get('url')}")
            print(f"  Domain: {session.get('domain')}")
            print(f"  Status: {session.get('status')}")
            print(f"  Events: {session.get('event_count')}")
            print(f"  Historic: {message.get('include_historic')}")
            print()

        elif msg_type == "historic_complete":
            count = message.get("count", 0)
            print(f"✓ Historic replay complete: {count} events")
            print("⏳ Watching for live events...\n")

        elif msg_type in ["historic_event", "live_event"]:
            event = message.get("event", {})
            self.event_count += 1
            event_type = event.get("type", "unknown")
            self.events_by_type[event_type] += 1

            # Show live events
            if msg_type == "live_event":
                self._print_event(event)

            # Analyze click patterns for rage clicks
            if event_type == "click":
                await self._check_rage_click(event)

            # Track navigation
            if event_type == "navigation":
                self.navigation_path.append(event.get("url"))

            # Alert on errors
            if event_type in ["js_error", "network_error"]:
                self.errors.append(event)
                self._print_error(event)

    def _print_event(self, event: Dict):
        """Pretty-print a live event."""
        timestamp = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M:%S")

        event_type = event["type"]
        target = event.get("target", "")
        label = event.get("label", "")
        value = event.get("value", "")

        # Format based on event type
        if event_type == "click":
            print(f"🖱️  [{time_str}] Click: {target} {f'({label})' if label else ''}")
        elif event_type == "input":
            print(f"⌨️  [{time_str}] Input: {target} = '{value[:50]}'")
        elif event_type == "navigation":
            url = event.get("url", "")
            print(f"🔗 [{time_str}] Navigate: {url}")
        elif event_type == "submit":
            print(f"📨 [{time_str}] Submit: {target}")
        elif event_type == "keydown":
            key_info = event.get("key", {})
            key = key_info.get("key", "")
            print(f"⌨️  [{time_str}] Key: {key}")
        else:
            print(f"📝 [{time_str}] {event_type}: {target}")

    def _print_error(self, event: Dict):
        """Print error event with details."""
        timestamp = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M:%S")

        event_type = event["type"]
        extra = event.get("extra", {})

        if event_type == "js_error":
            message = extra.get("message", "Unknown error")
            filename = extra.get("filename", "")
            lineno = extra.get("lineno", "")
            print(f"\n❌ [{time_str}] JavaScript Error:")
            print(f"   {message}")
            if filename:
                print(f"   at {filename}:{lineno}")

        elif event_type == "network_error":
            url = extra.get("url", "")
            status = extra.get("status", "")
            error = extra.get("error", "")
            print(f"\n❌ [{time_str}] Network Error:")
            print(f"   {url}")
            if status:
                print(f"   HTTP {status}")
            if error:
                print(f"   {error}")

    async def _check_rage_click(self, event: Dict):
        """Detect rage clicking (rapid repeated clicks on same element)."""
        now = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
        target = event.get("target", "")

        # Add to click history
        self.click_history.append((now, target))

        # Keep only last 5 seconds
        cutoff = now.timestamp() - 5
        self.click_history = [
            (ts, t) for ts, t in self.click_history
            if ts.timestamp() > cutoff
        ]

        # Check for 3+ clicks on same element within 2 seconds
        if len(self.click_history) >= 3:
            recent = self.click_history[-3:]
            targets = [t for _, t in recent]
            timestamps = [ts for ts, _ in recent]

            if len(set(targets)) == 1:  # Same element
                time_span = (timestamps[-1] - timestamps[0]).total_seconds()
                if time_span < 2:
                    print(f"\n⚠️  RAGE CLICK DETECTED: {targets[0]}")
                    print(f"   {len(recent)} clicks in {time_span:.1f}s")
                    print()

    def print_summary(self):
        """Print analysis summary."""
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total events: {self.event_count}")
        print(f"\nEvents by type:")
        for event_type, count in sorted(self.events_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"  {event_type}: {count}")

        if self.errors:
            print(f"\n⚠️  Errors detected: {len(self.errors)}")
            js_errors = [e for e in self.errors if e["type"] == "js_error"]
            net_errors = [e for e in self.errors if e["type"] == "network_error"]
            if js_errors:
                print(f"  JavaScript errors: {len(js_errors)}")
            if net_errors:
                print(f"  Network errors: {len(net_errors)}")

        if self.navigation_path:
            print(f"\nNavigation path ({len(self.navigation_path)} pages):")
            for i, url in enumerate(self.navigation_path[:10], 1):
                print(f"  {i}. {url}")
            if len(self.navigation_path) > 10:
                print(f"  ... and {len(self.navigation_path) - 10} more")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Sliples Stream Client")
    parser.add_argument("--api-key", required=True, help="Sliples API key")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--ws-url", default="ws://localhost:8000", help="WebSocket base URL")
    parser.add_argument("--domain", help="Filter by domain")
    parser.add_argument("--user-agent", help="Filter by user agent")
    parser.add_argument("--max-age", type=int, help="Max session age in seconds")
    parser.add_argument("--session-id", help="Specific session ID to stream")
    parser.add_argument("--no-historic", action="store_true", help="Skip historic events")
    parser.add_argument("--list-only", action="store_true", help="List sessions and exit")

    args = parser.parse_args()

    client = SliplesStreamClient(
        api_key=args.api_key,
        base_url=args.url,
        ws_url=args.ws_url,
    )

    try:
        # List sessions
        print("📡 Fetching active sessions...")
        sessions = await client.list_sessions(
            domain=args.domain,
            user_agent=args.user_agent,
            max_age_seconds=args.max_age,
        )

        if not sessions:
            print("No active sessions found.")
            return

        print(f"\n✓ Found {len(sessions)} active session(s):\n")
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session['name']}")
            print(f"   ID: {session['id']}")
            print(f"   URL: {session['url']}")
            print(f"   Domain: {session['domain']}")
            print(f"   Age: {session['age_seconds']}s")
            print(f"   Events: {session['event_count']}")
            print(f"   Watchers: {session['active_streams']}")
            print()

        if args.list_only:
            return

        # Choose session to stream
        if args.session_id:
            session_id = args.session_id
        else:
            session_id = sessions[0]["id"]
            print(f"→ Streaming first session: {sessions[0]['name']}\n")

        # Stream events
        analyzer = EventAnalyzer()

        try:
            await client.stream_session(
                session_id,
                include_historic=not args.no_historic,
                event_callback=analyzer.analyze,
            )
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")

        # Print summary
        analyzer.print_summary()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

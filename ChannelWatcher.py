import websockets
import asyncio
import aiohttp
import json


class ChannelWatcher:

    def __init__(self, user, url, msg):
        self.topic = "video-playback." + user.lower()
        self.ws = None
        self.p = 0
        self.quit = False
        self.recon = False
        self.session = None
        self.url = url
        self.msg = msg

    async def connect(self):
        self.ws = await websockets.connect("wss://pubsub-edge.twitch.tv")
        await self.ws.send(json.dumps({"type": "LISTEN", "data": {"topics": [self.topic]}}))
        self.session = aiohttp.ClientSession()
        asyncio.ensure_future(self.ping())

    async def ping(self):
        while True:
            self.p = 0
            await self.ws.send(json.dumps({'type': 'PING'}))
            await asyncio.sleep(12)
            if self.p != 1:
                self.recon = True
                return
            else:
                await asyncio.sleep(180)

    async def poll(self):
        while True:
            r = await self.ws.recv()
            r = json.loads(r)
            m_type = r.get("type")
            print(r)
            if m_type == "PONG":
                self.p = 1
            elif m_type == "MESSAGE":
                t = json.loads(r.get("data").get("message")).get("type")
                if t == "stream-up":
                    print("Live!")
                    await self.session.post(self.url, data={"content": self.msg}, headers={"User-Agent": "Twitch Channel Watcher Script"})
                elif t == "stream-down":
                    print("Stream down")

    async def run(self):
        await self.connect()
        while self.recon is False:
            await self.poll()
        await self.ws.close()
        self.ws = None
        self.p = 0
        self.quit = False
        self.recon = False
        self.session.close()
        self.session = None
        return

    def start(self):
        while self.quit is False:
            asyncio.get_event_loop().run_until_complete(self.run())

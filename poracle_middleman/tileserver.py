from __future__ import annotations

from .config import config
from aiohttp import web, ClientSession, ClientResponse
from discord import Webhook, File, WebhookMessage
from io import BytesIO
from urllib.parse import urljoin


class Tileserver:
    def __init__(self):
        self.index: int = 0
        self.webhooks: list[Webhook] = []
        self.templates: dict[str, str] = {}

    async def prepare(self):
        self.webhooks = [Webhook.from_url(u, session=ClientSession()) for u in config.tileserver.webhooks]

    async def upload_image(self, content: bytes) -> str:
        self.index = (self.index + 1) % len(self.webhooks)
        webhook = self.webhooks[self.index]

        try:
            with BytesIO(content) as stream:
                message = await webhook.send(file=File(stream, filename="map.png"), wait=True)
        except Exception as e:
            print(f"Exception while sending Webhook {e}")
            return ""

        if not message:
            return ""

        return message.attachments[0].url

    def get_template_data(self, name: str) -> str:
        data = self.templates.get(name)

        if not data:
            with open(config.tileserver.templates_path, "r", encoding="utf-8") as f:
                data = f.read()
            self.templates[name] = data

        return data

    async def handle_request(self, request: web.Request, template_name: str | None = None) -> web.Response:
        if not self.webhooks and config.tileserver.webhooks:
            await self.prepare()

        data = dict(request.query)

        for key, value in data.items():
            try:
                value = float(value)
            except ValueError:
                pass

            try:
                value = int(value)
            except ValueError:
                pass

            data[key] = value

        if request.body_exists:
            body = await request.json()
            data.update(body)
        map_kind = request.match_info["map_kind"]

        url = urljoin(config.tileserver.url, map_kind)
        if template_name:
            if template_name in config.tileserver.replace:
                template_name = config.tileserver.replace[template_name]
            url += "/" + template_name

        async with ClientSession() as session:
            async with session.post(url, json=data) as resp:
                if resp.status >= 400 or not self.webhooks:
                    body = await resp.read()
                    return web.Response(body=body, status=resp.status, headers=resp.headers)

                response = await resp.read()

        url = await self.upload_image(response)

        return web.Response(body=url)

    async def endpoint_straight(self, request: web.Request) -> web.Response:
        return await self.handle_request(request)

    async def endpoint_template(self, request: web.Request) -> web.Response:
        template_name = request.match_info["template"]
        return await self.handle_request(request, template_name=template_name)

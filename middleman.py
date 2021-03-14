from flask import Flask, request
import requests
import json
from io import BytesIO
import discord

with open("config.json", "r") as config_file:
    config = json.load(config_file)

webhook_urls = config["webhooks"]
webhooks = []
for webhook_url in webhook_urls:
    webhook = discord.Webhook.from_url(
        url=webhook_url,
        adapter=discord.RequestsWebhookAdapter()
    )
    webhooks.append(webhook)

pos = [0]
def get_webhook():
    pos[0] += 1
    if pos[0] > len(webhooks) - 1:
        pos[0] = 0
    return webhooks[pos[0]]

def get_data(request):
    data = {}
    body_data = request.get_json()
    if body_data:
        data = body_data
    arg_data = request.args
    if arg_data:
        data = {**data, **arg_data}
    return data

def test_vars(var):
    try:
        var = float(var)
    except:
        pass
    try:
        var = int(var)
    except:
        pass

    return var

def gen_staticmap(request, map_kind, template=None):
    data = get_data(request)
    data = {k: test_vars(v) for k, v in data.items()}

    extra_template = ""
    if template:
        extra_template = "/" + template
    response = requests.post(f"{config['tileserver_url']}{map_kind}{extra_template}", json=data)
    
    if response.status_code >= 400:
        return response.content

    stream = BytesIO(response.content)

    webhook = get_webhook()
    message = webhook.send(wait=True, file=discord.File(stream, filename="map.png"))
    stream.close()

    return message.attachments[0].url

app = Flask(__name__)

@app.route('/<map_kind>/<template>', methods=['GET', 'POST'])
def templating(map_kind, template):
    return gen_staticmap(request, map_kind, template)

@app.route('/<map_kind>', methods=['GET', 'POST'])
def straight_map(map_kind):
    return gen_staticmap(request, map_kind)

app.run(port=config["port"])

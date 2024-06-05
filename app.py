import asyncio
from pprint import pprint

from fastapi import FastAPI, Request
from pydantic import BaseModel
from slack_sdk import WebClient

# from slack_data import SlackEvent, create_slack_event
from slack import send_to_channel, create_slack_event

from agent import SoftwareEngineeringManagerAgent

github_agent = SoftwareEngineeringManagerAgent()

app = FastAPI()


async def run_agent(user_prompt: str, origin_channel: str):
    result = github_agent.execute(user_prompt)
    send_to_channel(origin_channel, result)


class SlackRequest(BaseModel):
    challenge: str = None
    token: str


@app.post("/slack/events")
async def slack_events(request: Request):
    data = await request.json()

    pprint(data)
    if challenge := data.get('challenge', ''):
        print(challenge)
        return {"challenge": challenge}

    # We filter out any events sent by bots (avoids endless loops)
    if 'bot_id' in data['event']:
        print("Filtered out bot event")
        return {"status": "received"}

    slack_event = create_slack_event(data['event'])

    asyncio.create_task(run_agent(slack_event.text, slack_event.channel))

    return {"status": "received"}

@app.post("/slack/interaction")
async def slack_interaction(request: Request):
    form = await request.form()
    pprint(form)

    return {"status": "received"}

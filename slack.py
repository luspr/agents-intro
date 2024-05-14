import os
from pprint import pprint
from typing import Generator
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv, find_dotenv
from dataclasses import dataclass, fields


load_dotenv(find_dotenv())

SLACK_TOKEN = os.environ.get('SLACK_API_KEY')


@dataclass
class SlackEvent:
    type: str
    team: str
    user: str
    channel: str
    text: str


def create_slack_event(event_data: dict):
    """
    Create slack event, supports multiple different types of events,
    at least mention and direct message.
    """
    datafields = [f.name for f in fields(SlackEvent)]
    print(datafields)
    event = SlackEvent(
        **{k: event_data[k] for k in datafields}
    )
    return event


def get_user_id_by_email(email):
    client = WebClient(token=SLACK_TOKEN)
    try:
        # Lookup for the user by email
        response = client.users_lookupByEmail(email=email)
        user_id = response['user']['id']
        return user_id
    except SlackApiError as e:
        print(f"Got an error retrieving Slack user ID: {e.response['error']}")
        return None 


def get_all_users() -> Generator[dict, None, None]:
    """
    Gets all users from Slack, returning their user nuclino_data as dictionaries (as per Slack's API)

    """
    client = WebClient(token=SLACK_TOKEN)
    try:
        # TODO: use pagination for larger slack workspaces
        result = client.users_list()
    
        # @SPEED
        for user in result['members']:
            yield user

    except SlackApiError as e:
        print(f"Error fetching users: {e.response['error']}")



def send_to_channel(channel_id: str, message: str):
    client = WebClient(token=SLACK_TOKEN)
    try:
        response = client.chat_postMessage(channel=channel_id, text=message, as_user=True)
        print("Message sent to channel: ", response["message"]["text"])
    except SlackApiError as e:
        print(f"Error: {e}")


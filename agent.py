import json
import os
import time
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler

import github


from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
client = OpenAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_all_issues_for_repo",
            "description": "Gets all issues for a specified repository owened by a certain github user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Owner of the repo",
                    },
                    "repo": {
                        "type": "string",
                        "description": "The name of the repository",
                    },
                },
                "required": ["owner", "repo"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_repo_by_name",
            "description": "Find repositories by name. The returned repos will include this substring (case insensitive).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "String that we query github for repos.",
                    }
                },
                "required": ["query"]
            },
        }
    },
]


def _retrieve_id(thread_id, run):
    return client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run.id
    )

def get_last_n_messages(thread_id, n=1, start=0, as_string=True):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    ret = []
    end = start + n
    for i, m in enumerate(messages):
        if end > i >= start:
            ret.append(m.content[0].text.value)
    if as_string:
        return '\n'.join(ret)
    return ret



class Agent:

    def __init__(self):
        self.thread = thread = client.beta.threads.create()
        self.assistant = client.beta.assistants.create(
            name="Github assistant",
            instructions="You help people navigate github in natural language. You have two tools: find issues in a certain repo, find a repo by query (substring)",
            tools=tools,
            model="gpt-4-turbo", # Try out other models
        )


    def execute(self, prompt: str) -> str:
        message = client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=prompt
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )
        
        while(run.status != 'completed'):
            time.sleep(0.1)

            run = _retrieve_id(self.thread.id, run)
        
            # Define the list to store tool outputs
            tool_outputs = []
            if run.status == 'failed':
                print(f"Run failed. Exiting.")
                break

            if run.status == 'requires_action':
                # Loop through each tool in the required action section
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    func_name = tool_call.function.name
                    kwargs = json.loads(tool_call.function.arguments)
                    func_to_call = getattr(github, func_name)
                    print("Calling tool", func_name, " with ", kwargs)
                    output = str(func_to_call(**kwargs))
                    print(output)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": str(output)
                    })

                if tool_outputs:
                    client.beta.threads.runs.submit_tool_outputs
                    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                    )
                    print("Tool outputs submitted successfully.")
            print(run.status)
        
        return get_last_n_messages(thread_id=self.thread.id)



if __name__ == '__main__':
    agent = Agent()
    print(agent.execute('Give me repos about hackbay'))
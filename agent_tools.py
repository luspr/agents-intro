import os
from dataclasses import dataclass

import requests
from azure.devops.connection import Connection
from azure.devops.v7_0.work_item_tracking.models import Wiql, JsonPatchOperation
from dotenv import load_dotenv, find_dotenv
from msrest.authentication import BasicAuthentication



load_dotenv(find_dotenv())
token = os.environ['GITHUB_TOKEN']

def get_all_issues_for_repo(owner, repo):
    """
    Get all issues for a specified repository.
    
    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param token: GitHub personal access token for authentication.
    :return: List of issues.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        issues = response.json()
        return [f"{i['title']} - {i['url']}" for i in issues]
    else:
        response.raise_for_status()

def find_repo_by_name(query):
    """
    Find repositories by name.
    
    :param query: The search query string.
    :param token: GitHub personal access token for authentication.
    :return: List of repositories matching the search query.
    """
    url = f"https://api.github.com/search/repositories"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'q': query
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        repositories = response.json()['items']
        return [f"{r['full_name']} - {r['url']}" for r in repositories]

    else:
        response.raise_for_status()

@dataclass
class AzureWorkItem:
    work_item_type: str
    ado_id: int
    name: str
    resource_email: str
    link: str
    # start_date: Optional[str]
    # end_date: Optional[str]
    # area: str
    # parent_id: Optional[int] = None
    # child_ids: List[int] = field(default_factory=list)

organization = os.environ['AZURE_ORG']
project = os.environ['AZURE_PROJECT']
pat = os.environ.get('AZURE_TOKEN')
credentials = BasicAuthentication('', pat)
connection = Connection(base_url=f"https://dev.azure.com/{organization}", creds=credentials)
ado_client = connection.clients.get_work_item_tracking_client()

def _fetch_work_item_details(id):
    work_item = ado_client.get_work_item(id, expand='All')
    fields = work_item.fields
    azure_work_item = AzureWorkItem(
        work_item_type=fields.get('System.WorkItemType', ''),
        ado_id=work_item.id,
        name=fields.get('System.Title', ''),
        resource_email=fields.get('System.AssignedTo', {}).get('uniqueName', ''),
        link=f"https://dev.azure.com/{organization}/{project}/_workitems/edit/{work_item.id}",
    )

    return azure_work_item.__dict__

def query_azure_devops(wiql_query):
    query = Wiql(query=wiql_query)
    work_items_result = ado_client.query_by_wiql(query).work_items
    work_item_ids = [wi.id for wi in work_items_result]
    work_items = [_fetch_work_item_details(id) for id in work_item_ids]
    return work_items



if __name__ == '__main__':
    # Quick tests
    from pprint import pprint
    # owner = 'octocat'
    # repo = 'hello-world'
    # issues = get_all_issues_for_repo(owner, repo)
    # pprint(issues)

    # query = 'Hackbay'
    # repositories = find_repo_by_name(query)
    # pprint(repositories)

    query = """SELECT
    [System.Id],
    [System.Title],
    [System.State],
    [System.AssignedTo],
    [System.CreatedDate]
FROM workitems
WHERE
    [System.WorkItemType] = 'Feature'
    AND [System.AssignedTo] = 'lukas.spranger@netzsch.com'
    AND [System.State] <> 'Closed'
ORDER BY
    [System.CreatedDate] DESC"""
    work_items = query_azure_devops(query)

    pprint(work_items)

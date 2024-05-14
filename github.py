import os

import requests
from dotenv import load_dotenv, find_dotenv



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



if __name__ == '__main__':
    # Quick tests
    from pprint import pprint
    owner = 'octocat'
    repo = 'hello-world'
    issues = get_all_issues_for_repo(owner, repo)
    pprint(issues)

    query = 'Hackbay'
    repositories = find_repo_by_name(query)
    pprint(repositories)

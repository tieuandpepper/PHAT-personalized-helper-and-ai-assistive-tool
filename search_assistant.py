import requests
from ollama_server import OllamaServer
import utils
import os,re, inspect

MAX_ITERATION=10
# current directory
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
VERBAL_LEVEL = utils.SILENT
API_KEY = "AIzaSyBEYTzdkLTEUYtAONf2S5boZq9rcNq-qlA"  # Replace with your actual Google API key
CSE_ID = "b293369424e1a4b6c"  # Replace with your Custom Search Engine ID
GG_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

def search_google(query):
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": 10,
    }

    response = requests.get(GG_ENDPOINT, params=params)
    if response.status_code == 200:
        search_results = response.json()
        return search_results.get('items', [])
    else:
        print(f"Error: {response.status_code}")
        return []

# Example usage
# query = "latest advancements in AI"
# results = search_google(query)

# # Print the first few results
# for result in results[:3]:
#     print(f"Title: {result['title']}")
#     print(f"Snippet: {result['snippet']}")
#     print(f"Link: {result['link']}\n")

def search_assistant(model: OllamaServer, request):
    iteration = 0
    while True:
        iteration =iteration+1
        if iteration>MAX_ITERATION:
            break
        prompt = f"""
You are my search assistant. You have access to SearchGoogle:
    Its function is to search online content through google.
    Its Input is a string.

If I ask you to search the web, please respond with the following format exactly:
  Thought: you should always think about what to do
  Query: the input to the SearchGoogle function. The input ends with a newline.
Here are some important note:
    Be precise and don't be wordy when coming up with the Query.
    Always generate Thought and Query Input. Missing them will produce an error!

Begin!

Search Task:
{request}

Thought:
"""
        llm_output = model.invoke_model(prompt)
        utils.print_level(f"\n===============\nLLM output: {llm_output}\n===============\n",VERBAL_LEVEL)
        regex = r"Query\s*\d*\s*:\s*(.*)"
        match = re.search(regex, llm_output)
        if match:
            search_query = match.group(1)
            print(f"Search Query: '{search_query}'")
            results = search_google(search_query)
            for result in results[:5]:
                print(f"Title: {result['title']}")
                print(f"Snippet: {result['snippet']}")
                print(f"Link: {result['link']}\n")
            print("Search successfully.")
            return
        else:
            print("No search query found.")
            tool_output = "Feedback: Search query cannot be found in "+f"'{llm_output}. Try again with the correct syntax: Query: search_query\n'"
    
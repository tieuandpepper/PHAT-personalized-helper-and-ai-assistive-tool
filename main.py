from ollama_server import OllamaServer
from email_assistant import email_assistant
from calendar_assistant import calendar_assistant
from search_assistant import search_assistant
from pdf_assistant import pdf_assistant
from personal_assistant import personal_assistant
import utils
import yaml, os, inspect,re 
from datetime import datetime
VERBAL_LEVEL = utils.SILENT
MAX_ITERATION = 3
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
current_datetime = datetime.now()
current_datetime_str = current_datetime.strftime("%B %d %Y %H:%M:%S")
day_of_week = current_datetime.strftime("%A")
prompt = f"""
You are an intelligent and helpful assistant. Today is {day_of_week} {current_datetime_str}. You have access to the following tools:
    EmailAssistant: "use this to do things related to email on my behalf."
    CalendarAssistant: "use this to create new meeting for user."
    SearchAssistant: "use this to search the Internet for user."
    PDFAssistant: "use this to read local PDF files"
    PersonalAssistant: "use this to communicate with user about personal requests."
    GeneralAssistant: "use this to communicate with user about general things. Input is what you want to ask/communicate about."
The Input for these tools are is the request from user in this prompt.
If I request you to do something, please respond with the following format exactly:
    Thought: you should always think about what to do
    Action: the action to take, should be one of [EmailAssistant,CalendarAssistant,SearchAssistant,PDFAssistant,PersonalAssistant]. The action is ended with a newline.
    Action Input: the input to the action (my initial prompt). The input action is ended with a newline.
Here are some important note:
    Be precise. Don't be wordy.
    The program only takes one action at a time, so don't give 2 actions in 1 output.
    This Thought/Action/Action Input can repeat several times. So 1 action for each prompt.
    Feedback from the program is generated as one of the inputs for your next iteration. Pay attention to the feedback.
    Always generate Action and Action Input. Missing them will produce an error!

Begin!

Request:
user_prompt

Thought:
"""

def main():
    global prompt
    model = OllamaServer()
    print("I am your AI assistant. Let me know how can I help you!")
    llm_request = ""
    while True:
        user_request = ""
        user_answer = ""
        if len(llm_request) > 1:
            user_answer = input(llm_request)
            llm_input = f"{prompt}\nModel request: {llm_request}. User answer: {user_answer}"
            llm_request = ""
        else:
            user_request = input("Enter your request here or enter bye to exit: ")
            llm_input = prompt.replace("user_prompt",user_request)
        if 'bye' in user_request.lower():
            break

        llm_output = model.invoke_model(llm_input)
        regex = (
            r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        )
        action_match = re.search(regex, llm_output, re.DOTALL)
        utils.print_level(f"\n===============\nLLM output: {llm_output}\n===============\n",VERBAL_LEVEL)
        if action_match:
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip("\n")
            if llm_output.startswith("Thought:"):
                prompt = prompt+llm_output[8:]
            else:
                prompt = prompt+llm_output

            utils.print_level(f"\n-------\ntool: {action} input: {tool_input}\n-------\n",VERBAL_LEVEL)
            llm_request = ""
            if action == "EmailAssistant":
                email_assistant(model,tool_input)
            elif action == "CalendarAssistant":
                calendar_assistant(model,tool_input)
            elif action == "SearchAssistant":
                search_assistant(model,tool_input)
            elif action == "PDFAssistant":
                pdf_assistant(model,tool_input)
            elif action == "PersonalAssistant":
                personal_assistant(model,tool_input)
            elif action == "GeneralAssistant":
                llm_request = tool_input
            else:
                tool_output = "Error: Action "+f"'{action}' is not a valid!"
                print(tool_output)
        
    print(f"\n{model.stop_model()}")


if __name__ == "__main__":
    main()
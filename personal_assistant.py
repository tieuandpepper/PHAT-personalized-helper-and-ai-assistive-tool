import os,inspect,re,json
from ollama_server import OllamaServer
import utils
MAX_ITERATION = 10
VERBAL_LEVEL = utils.SILENT
# current directory
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
personal_data_file = os.path.join(current_dir,"data","personal_data.txt")

def read_personal_data():
    with open(personal_data_file,"r") as f:
        content = f.read()
    return content

def write_personal_data(data):
    with open(personal_data_file, "a") as f:
        f.write(data)

def ask_user(question):
    user_answer = input(question)
    return user_answer

def personal_assistant(model:OllamaServer, question:str):
    prompt = f"""
You are my personal assistant. You know about my private data and can communicate with me using those.

You have access to the following tools:
    ReadPersonalData: "read my personal_data file"
    WritePersonalData: "write to my personal_data file for long-time storage. The Input is the information you want to remember about me when I communicate with you."
    AskUser: "Ask or communicate with user. The input is the question you have for me. Make it shorter than 100 tokens."

If I ask you to answer my question or you want to store some private information about me, please respond with the following format exactly:
  Thought: you should always think about what to do
  Action: the action to take, should be one of [ReadPersonalData, WritePersonalData,AskUser]. The action is ended with a newline.
  Action Input: the input to the action. The input action is ended with a newline.

Here are some important note:
  Be precise. Don't be wordy.
  The program only takes one action at a time, so don't give 2 actions in 1 output.
  This Thought/Action/Action Input can repeat several times. So 1 action for each prompt.
  Feedback from the program is generated as one of the inputs for your next iteration. Pay attention to the feedback.
  When you are done, generate this message exactly: "Thought: I have now completed the task. Done: the final message to the task"
  Always generate Action and Action Input. Missing them will produce an error!

Begin!

Question:
{question}

Thought:
"""
    iteration = 0
    while True:
        iteration =iteration+1
        if iteration>MAX_ITERATION:
            break
        utils.print_level(f"\n************\nPrompt #{iteration}: {prompt}\n************\n",VERBAL_LEVEL)
        llm_output = model.invoke_model(prompt)
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
            if action == "ReadPersonalData":
                read_personal_data()
                break
            elif action == "WritePersonalData":
                write_personal_data(tool_input)
                break
            elif action == "AskUser":
                tool_output = ask_user(tool_input)
                print("---------> AsKUser was invoked. tool_ouput is ", tool_output)
            else:
                tool_output = "Error: Action "+f"'{action}' is not a valid!"
                prompt = prompt+"\nFeedback: "+str(tool_output)+"\n"
                continue
        elif 'Done:' in llm_output:
            print(f"\n\n-------\n{llm_output}\n-------\n\n")
            return
        else:  
            tool_output = f"Error: wrong LLM response\n{llm_output}"
            print(f"\n-------\nError: wrong LLM response\n{llm_output}\n-------\n")
        
        prompt = prompt = prompt+"\nResponses: "+str(tool_output)+ "\n"
        

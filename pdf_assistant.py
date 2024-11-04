import pymupdf
import os,inspect,re,json
from ollama_server import OllamaServer
import utils

MAX_ITERATION = 10
VERBAL_LEVEL = utils.SILENT
# current directory
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
data_dir = os.path.join(current_dir,"data")
def pdf_read_all(folder_path=data_dir):
    extracted_text = ""
    
    # List all files in the folder
    for filename in os.listdir(folder_path):
        # Check if the file is a PDF
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            
            # Open the PDF and extract text
            with pymupdf.open(pdf_path) as doc:
                for page in doc:
                    extracted_text += page.get_text() + "\n"
    
    return extracted_text


def get_pdf_filenames(folder_path=data_dir):
    pdf_filenames = []
    
    # List all files in the folder
    for filename in os.listdir(folder_path):
        # Check if the file is a PDF
        if filename.lower().endswith('.pdf'):
            pdf_filenames.append(filename)
    
    return pdf_filenames

def extract_text_from_pdf(filename, folder_path=data_dir):
    extracted_text = ""
    pdf_path = os.path.join(folder_path,filename)
    # Open the PDF and extract text
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            extracted_text += page.get_text() + "\n"
    
    return extracted_text

def pdf_assistant(model:OllamaServer, question:str):
    pdf_list = get_pdf_filenames(data_dir)
    prompt = f"""
You are my PDF document assistant. Here is the list of all PDFs I have: {pdf_list}

You have access to the following tools:
    ReadPDF: "read only 1 PDF file that you believe containing the information for my question. The input is the file name of the PDF. Remember to include ".pdf""
    ReadAll: "read all PDFs in the folder. This is not recommended since it requires a significant amount of memory"

To answer my question, you should use ReadPDF first, so that you can process data efficiently and effectively.
If you need more information, you can invoke ReadPDF sequentially.

If I ask you to answer my question, please respond with the following format exactly:
  Thought: you should always think about what to do
  Action: the action to take, should be one of [ReadPDF, ReadAll]. The action is ended with a newline.
  Action Input: the input to the action. The input action is ended with a newline.

Here are some important note:
  Don't answer using the information that is not from those PDFs. Unless I don't specify using only my PDFs.
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
            if action == "ReadPDF":
                try:
                    # patch_json_content = json.loads(tool_input)
                    # filename = patch_json_content["filename"]
                    filename = tool_input
                    tool_output = extract_text_from_pdf(filename)
                except Exception as e:
                    tool_output = f"This is the wrong format: {tool_input}. Quotation marks are not needed"
                    prompt = prompt+"\nFeedback: "+str(tool_output)+"\n"
                    continue
            elif action == "ReadAll":
                tool_output = pdf_read_all()
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
        
        # invoke llm to search for answer
        llm_query = f"Here is the data you have: {tool_output}\nHere is the question: {question}\n. Give the answer to the question. The answer should be limited to 500 tokens"
        llm_answer = model.invoke_model(llm_query)
        utils.print_level(f"LLM query: {llm_query}",VERBAL_LEVEL)
        print(f"\n======\n{llm_answer}\n======\n")
        human_feedback = input("Is this answer satisfactory? Your answer here (yes or feedback): ")
        if 'yes' in human_feedback.lower():
            print(f"Thank you. It was a successful job :)")
            return
        
        prompt = prompt = prompt+"\nData: "+str(tool_output)+ "\nUser Feedback: " + str(human_feedback)+"\n"
        

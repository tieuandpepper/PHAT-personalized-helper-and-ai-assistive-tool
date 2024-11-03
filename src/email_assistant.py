import base64
from email.message import EmailMessage
import os,re, inspect
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import time
from ollama_server import OllamaServer
import utils
# Set scopes for Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
MAX_ITERATION = 5
VERBAL_LEVEL = utils.SILENT

# current directory
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def send_email(receiver_email:str, email_subject:str, email_content:str, sender_email="kevin.tieu.tamu@gmail.com")->str:
  creds = None
  # Load pre-authorized user credentials from the environment.
  if os.path.exists('google_kevin_tieu_tamu_gmail_auth.json'):
    # Use OAuth flow to get credentials
    flow = InstalledAppFlow.from_client_secrets_file(
        'google_kevin_tieu_tamu_gmail_auth.json', SCOPES)
    creds = flow.run_local_server(port=0)

  try:
    # create gmail api client
    service = build("gmail", "v1", credentials=creds)

    message = EmailMessage()
    message.set_content(email_content)

    message["To"] = receiver_email
    message["From"] = sender_email
    message["Subject"] = email_subject

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"message": {"raw": encoded_message}}
    # pylint: disable=E1101
    email = (
      service.users()
      .drafts()
      .create(userId="me", body=create_message)
      .execute()
    )

    # print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

  except HttpError as error:
    output = f"An error occurred: {error}"
    return output

  email_id = email["id"]
  sent_message = service.users().drafts().send(userId="me", body={"id": email_id}).execute()
  output = "Email successfully sent! Log: " + str(sent_message)
  return output

# print(send_email("kevin.tieu.tamu@gmail.com","phattieuthien@gmail.com","Automated message", "This is a test email message."))

def find_email(model: OllamaServer, name:str) ->str:
  with open(os.path.join(current_dir,'email_contacts.json'), 'r') as f:
    contacts_list = json.load(f)
  utils.print_level(f"--- find_email input: {name} in {contacts_list}",VERBAL_LEVEL)
  prompt = f"""
You are my email-finding assistant. Return what was asked. Additional tokens are not permitted.
Here is the list of names and email addresses of my contacts:{contacts_list}
Read the list and find the email of {name}.
If you cannot find the email, return exactly this: None.
"""
  email_addr = model.invoke_model(prompt)
  email_addr = email_addr.replace('"', '').replace("'", "")
  utils.print_level(f"--- find_email output : {email_addr}",VERBAL_LEVEL)
  return email_addr

def email_assistant(model: OllamaServer,request):
    prompt = f"""
You are my email assistant. You have access to the following tools:
    
FindEmail: "find the email address of my contacts. Input is enclosed by the character < and >" 
SendEmail: "Send email tool. Input is a json object with {{"receiver_email": str, "subject": str, "body": str}}."

To craft an email, you should use FindEmail first to find correct email addresses (receiver_email) from my contacts.

If I ask you to send an email, please respond with the following format exactly:
  Thought: you should always think about what to do
  Action: the action to take, should be one of [FindEmail, SendEmail]. The action is ended with a newline.
  Action Input: the input to the action. The input action is ended with a newline.

Here are some important note:
  Be precise. Don't be wordy. Don't assume and create new things.
  The program only takes one action at a time, so don't give 2 actions in 1 output.
  This Thought/Action/Action Input can repeat several times. So 1 action for each prompt.
  Feedback from the program is generated as one of the inputs for your next iteration. Pay attention to the feedback.
  When you are done, generate this message exactly: "Thought: I have now completed the task. Done: the final message to the task"
  Always generate Action and Action Input. Missing them will produce an error!

Begin!

Task:
{request}

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

            if action=="SendEmail":
                try:
                    patch_json_content = json.loads(tool_input)
                    to_addr = patch_json_content["receiver_email"]
                    subject = patch_json_content["subject"]
                    body = patch_json_content["body"]
                    tool_output = send_email(to_addr,subject,body)
                except Exception as e:
                    tool_output = f"This is the wrong json format: {tool_input}"
                if "Email successfully sent!" in tool_output:
                    print(f"The Email Assistant successfully sent your email to {to_addr} with the content\nSubject: {subject}\nContent: {body}")
                    return
            elif action=="FindEmail":
                input_match = re.search(r"<(.*?)>", tool_input)
                if input_match:
                    tool_input = input_match.group(1)
                    tool_output = find_email(model,tool_input)
                    tool_output = f"FindEmail successfully ran. Here is the email for {tool_input}: {tool_output}. Use it"
                else:
                    tool_output = f"Error: input {tool_input} does not follow the valid structure of <email>"
            else:
                tool_output = "Error: Action "+f"'{action}' is not a valid!"

            utils.print_level(f"\n------- tool_output ------- \n{tool_output}\n-------\n",VERBAL_LEVEL)

        elif 'Done:' in llm_output:
            print(f"\n\n-------\n{llm_output}\n-------\n\n")
            return
        else:  
            tool_output = f"Error: wrong LLM response\n{llm_output}"
            print(f"\n-------\nError: wrong LLM response\n{llm_output}\n-------\n")

        prompt = prompt+"\Feedback: "+str(tool_output)+"\n"
    print(f"The Email Assistant failed to send your email. Here is the log: {prompt}")
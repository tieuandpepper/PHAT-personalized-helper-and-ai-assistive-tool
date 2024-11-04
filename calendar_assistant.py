from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
import datetime
from ollama_server import OllamaServer
import utils,inspect,os,re,json
from datetime import datetime
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
MAX_ITERATION = 10
VERBAL_LEVEL = utils.SILENT
# current directory
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
current_timezone = 'America/Chicago'
# Get the current datetime (or use a specific datetime)
current_datetime = datetime.now()
current_datetime_str = current_datetime.strftime("%B %d %Y %H:%M:%S")
day_of_week = current_datetime.strftime("%A")
offset_utc="-6:00"
calendar_credentials = None

def calendar_get_creds():
    creds = None
    # Load pre-authorized user credentials from the environment.
    path_auth = os.path.join(current_dir,"src","google_kevin_tieu_tamu_gmail_auth.json")
    if os.path.exists(path_auth):
    # Use OAuth flow to get credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            path_auth, SCOPES)
        creds = flow.run_local_server(port=0)
    return creds

# Create a calendar event
def calender_create_event(event_details):
    global calendar_credentials
    if calendar_credentials is None:
        calendar_credentials = calendar_get_creds()
    try:
        service = build('calendar', 'v3', credentials=calendar_credentials)
        event = {
            'summary': event_details['summary'],
            'start': {
                'dateTime': event_details['start_time'],
                'timeZone': current_timezone,
            },
            'end': {
                'dateTime': event_details['end_time'],
                'timeZone': current_timezone,
            },
            # 'attendees': [{'email': email} for email in event_details['attendees']],
        }
    except HttpError as error:
        output = f"An error occurred: {error}"
        return output
    # events = calendar_check_conflict(service,event_details)
    # utils.print_level(f"Calendar check status: {events}",VERBAL_LEVEL)
    # if events is not None:
        # output = f"The event {event_details} has conflict with other {events}. Please reschedule."
        # return output

    event = service.events().insert(calendarId='primary', body=event).execute()
    output = f"Event successfully created: {event.get('htmlLink')}"
    utils.print_level(output,VERBAL_LEVEL)
    return output

# Check for conflicting events
def calendar_check_conflict(event_details):
    global calendar_credentials
    if calendar_credentials is None:
        calendar_credentials = calendar_get_creds()
    utils.print_level("Check for time conflict",VERBAL_LEVEL)
    service = build('calendar', 'v3', credentials=calendar_credentials)
    local_tz = pytz.timezone(current_timezone)
    start_time = datetime.strptime(event_details['start_time'], "%Y-%m-%dT%H:%M:%S")
    start_time_local = local_tz.localize(start_time).isoformat()
    end_time = datetime.strptime(event_details['end_time'], "%Y-%m-%dT%H:%M:%S")
    end_time_local = local_tz.localize(end_time).isoformat()
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_time_local,
        timeMax=end_time_local,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Check if there are any events that conflict
    # utils.print_level(output,VERBAL_LEVEL)
    return events

# Main function to schedule a meeting
def calendar_assistant(model:OllamaServer, request):
    prompt = f"""
You are my calendar assistant. Your task is to organize my meetings on my calendar.The date and time at this moment is {day_of_week}, {current_datetime_str}.
You have access to the following tools:
    CheckSchedule: "check the calendar for potential time conflict with another meeting. Input is a json object with {{"summary": str, "start_time": str, "end_time":str}}. The date and time must follow the format: YYYY-MM-DDTHH:MM:SS. Example: 2024-11-10T15:00:00 means 15:00:00, November 10, 2024)"
    ScheduleEvent: "schedule a meeting. Input is a json object with {{"summary": str, "start_time": str, "end_time":str}}. The date and time must follow the format: YYYY-MM-DDTHH:MM:SS. Example: 2024-11-10T15:00:00 means 15:00:00, November 10, 2024)"

To schedule an event, here are the steps:
    First: Use CheckSchedule first for potential time conflict.
    If no schedule conflict: you can use ScheduleEvent when the calendar is available. Otherwise, the program will take care of it.

If I ask you to schedule a meeting or event, please respond with the following format exactly:
    Thought: you should always think about what to do
    Action: the action to take, should be one of [ScheduleEvent,CheckSchedule]. The action is ended with a newline.
    Action Input: the input to the action. The input action is ended with a newline.

Here are some important note:
  Be precise. Don't be wordy. Don't assume and create new things.
  The program only takes one action at a time, so don't give 2 actions in 1 output. Also, schedule 1 event at a time.
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
            if action == "ScheduleEvent":
                try:
                    patch_json_content = json.loads(tool_input)
                    event_details = {
                        "summary": patch_json_content["summary"],
                        "start_time": patch_json_content["start_time"],
                        "end_time": patch_json_content["end_time"]
                    }
                    tool_output = calender_create_event(event_details)
                except Exception as e:
                    tool_output = f"This is the wrong json format: {tool_input}"
                if "Event successfully created" in tool_output:
                    print(f"The Calendar Assistant sucessfully created the event: {event_details}")
                    return
            elif action == "CheckSchedule":
                try:
                    patch_json_content = json.loads(tool_input)
                    event_details = {
                        "start_time": patch_json_content["start_time"],
                        "summary": patch_json_content["summary"],
                        "end_time": patch_json_content["end_time"],
                    }
                except Exception as e:
                    tool_output = f"This is the wrong json format: {tool_input}"
                    prompt = prompt+"\nFeedback: "+str(tool_output)+"\n"
                    continue
                tool_output = calendar_check_conflict(event_details)
                if tool_output:
                    tool_output = f"Conflict events in calendar: {tool_output[0]}.\n==>>>Please change the time."
                    print(tool_output)
                    return
                tool_output = "No conflict in schedule."
            else:
                tool_output = "Error: Action "+f"'{action}' is not a valid!"
            utils.print_level(f"\n------- tool_output ------- \n{tool_output}\n-------\n",VERBAL_LEVEL)
        
        elif 'Done:' in llm_output:
            print(f"\n\n-------\n{llm_output}\n-------\n\n")
            return
        else:  
            tool_output = f"Error: wrong LLM response\n{llm_output}"
            print(f"\n-------\nError: wrong LLM response\n{llm_output}\n-------\n")
        prompt = prompt+"\nFeedback: "+str(tool_output)+"\n"
    print(f"The Calendar Assistant failed to create an event. Here is the log: {prompt}")
    print(f"You can retry again. Thank you")

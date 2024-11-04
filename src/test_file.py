import yaml,json
import os, inspect,re
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
path_to_contact = os.path.join(current_dir,"email_contacts.json")

contacts_list = [
    {"name": "Personal Email", "email": "phattieuthien@gmail.com"},
    {"name": "Amazon Email", "email": "tieuthienphat@gmail.com"},
    {"name": "Work Email", "email": "ptieu28@tamu.edu"},
    {"name": "Alias Work Email", "email": "phat.tieu@tamu.edu"},
]
contacts_list = sorted(contacts_list, key=lambda contact: contact['name'])
# Save to YAML
with open(path_to_contact, 'w') as f:
    json.dump(contacts_list, f, indent=4)

# Load from YAML
with open(path_to_contact, 'r') as f:
    contacts_list = json.load(f)
    print(contacts_list)


# def find_email(name:str) ->str:
#   with open(os.path.join(current_dir,'email_contacts.yaml'), 'r') as f:
#     contacts_list = yaml.safe_load(f)
  
#   for contact in contacts_list:
#     # Search with lower case name and strip all white space
#     if re.sub(f"\s+","",contact["name"].lower()) == re.sub(f"\s+","",name.lower()):
#       return contact["email"]
#   return None


# print(find_email("personAL\n\temail"))
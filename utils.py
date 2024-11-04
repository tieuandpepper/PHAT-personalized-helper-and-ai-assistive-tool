
SILENT = 0
VERBOSE = 1

def print_level(text:str, level:int) -> None:
    if level == SILENT:
        return
    elif level == VERBOSE:
        print(text)

def human_input(prompt:str) -> str:
    prompt = f"PHAT needs human assistance\n{prompt}\nEnter your feedback/instruction here: "
    return input(prompt)
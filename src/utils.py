
SILENT = 0
VERBOSE = 1

def print_level(text:str, level:int) -> None:
    if level == SILENT:
        return
    elif level == VERBOSE:
        print(text)


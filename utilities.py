import time

def safeFormat(string, values):
    try:
        return string.format(**values) if any(f"{{{key}}}" in string for key in values) else string
    except Exception as e:
        print(e)
        return string

def log(string: str, note = "Log"):
    """Logs a message to the log file."""
    try:
        timeStamp = time.strftime("%H:%M:%S", time.localtime())
        with open(f"log/current_log.txt", "a") as log:
            log.write(f"[{note}] ({timeStamp}) {string}\n")
        return True
    except Exception as e:
        print(e)
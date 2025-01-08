import subprocess, time, os, utilities
import terminal as trm
from terminal import reboot

def main():
    terminal = trm.TerminalUI()

    while True:
        try:
            terminal.main()
        except reboot as e:
            print("Rebooting terminal...")
            subprocess.Popen(["python", "main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            os._exit(0)
        except Exception as e:
            utilities.log(e)
            print(e)
            input("")
            break

if __name__ == "__main__":
    main()
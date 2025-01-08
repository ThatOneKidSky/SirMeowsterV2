import os, json, sys, subprocess, time, threading, variables, socket, utilities
from variables import constants

commandFile = "terminal/commands.json"

class TerminalUI:
    def __init__(self):
        self.commandFile = commandFile
        self.commands = self.loadCommands()
        self.debugMode = variables.constants["DEBUG"]
        
        self.host = variables.constants["host"]
        self.port = variables.constants["port"]

        print("Welcome to the Sir Meowster UI.\nRun help for commands.")
        if self.debugMode:
            print("Currently running debug mode!")
        utilities.log("Terminal init.")
    
    #region File Management
    def loadFile(self, file):
        try:
            with open(file, "r") as oFile:
                return oFile.read()
        except FileNotFoundError:
            utilities.log(f"The file {file} was not found", "Error")
            print(f"Error: The file '{file}' was not found.")

    def loadJson(self, file):
        content = self.loadFile(file)
        if content is not None:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                utilities.log(f"Failed to load {file}.")
                print(f"Error: Json from '{file}' failed to load.", "Error")

    def loadCommands(self):
        file = self.loadJson(self.commandFile)
        return file
    #endregion

    #region Command Utils
    def handleSubcommand(self, command, subcommand):
        if isinstance(subcommand, tuple):
            subcommand = list(subcommand)
        
        matches = []
        for alias in subcommand:
            for subcommands in self.commands[command]["subcommands"]:
                if alias in subcommands["alias"]:
                    matches.append(subcommands["call"])
        
        return matches if matches else ''

    def callBotFunction(self, command, args = []):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
                clientSocket.connect((constants["host"], constants["port"]))
                clientSocket.sendall(json.dumps({"function":f"{command}","args":args}).encode())

                resonse = clientSocket.recv(1024)
                print(f"{resonse.decode()}")
                return resonse.decode()
        except WindowsError:
            return False
        except Exception as e:
            utilities.log(e, "Error")
            if self.debugMode:
                print(e)
            return False
    #endregion

    #region Commands
    def requestStatus(self, *subcommands):
        utilities.log("Bot ping called")
        ping = self.callBotFunction("ping")
        if ping:
            if "-silent" not in subcommands:
                print("Pong")
            utilities.log("Bot responded")
            return True
        else:
            if "-silent" not in subcommands:
                print("No pong recieved")
            utilities.log("Bot did not respond")
            return False

    def botStart(self, *subcommands):
        utilities.log("Bot called to start")
        call = self.handleSubcommand("start", subcommands)

        if "-ignore" not in subcommands:
            if self.requestStatus("-silent"):
                print("Bot is already running.")
                utilities.log("Bot is already running")
                return False

        utilities.log("Bot starting...")
        if "debug" in call:
            print("Starting bot in debug mode.")
            subprocess.Popen(["python", "meowster.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            return True
        
        print("Starting bot.")
        subprocess.Popen(["pythonw", "meowster.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return True
        
    def botStop(self, *subcommands):
        utilities.log("Bot stop called.")
        if self.callBotFunction("stop"):
            print("Stopped bot.")
        elif "-silent" not in subcommands:
            print("Bot is not running.")
    
    def restart(self, *subcommands):
        call = self.handleSubcommand("reset", subcommands)

        if isinstance(call, list) and call[0] == "bot":
            utilities.log("Restarting bot...")
            self.botStop("-silent")
            time.sleep(1)

            if len(call) > 1 and call[1] == "debug":
                self.botStart("-debug", "-ignore")
            else:
                self.botStart("-ignore")
            return True
        
        if isinstance(call, list) and call[0] == "terminal":
            utilities.log("Restarting terminal...")
            print("Rebooting terminal...")
            time.sleep(1)
            raise reboot

        print("Missing or incorrect subcommands.")
        return False

    def printHelp(self, *subcommands):
        for _, data in self.commands.items():
            helpText = data.get('help', 'Has not help data.')
            helpAlias = data.get('alias', None)

            if helpAlias is None:
                continue

            print(f"{helpAlias} - {helpText}")
            
            subcommand = data.get('subcommands', [])
            if subcommand:
                for subcmd in subcommand:
                    subHelp = subcmd.get('help', 'Has no help data.')
                    subAlias = subcmd.get('alias', ['Has no alias.'])

                    if subAlias is None:
                        continue

                    print(f"  {subAlias} - {subHelp}")

            print()
    
    def clearLog(self, *subcommands):
        utilities.log("Clearing log.")
        try:
            print("Do you wish to save the log in another file?")
            print("Please give the file a name, or leave empty to delete.")
            name = input("> ")

            print("Clearing logs")
            if name != "":
                with open("log/current_log.txt", "r") as file:
                    with open(f"log/{name}.txt", "w") as save:
                        save.write(f"{file.read()}")
            
            os.remove("log/current_log.txt")
            print("Finished")
        except WindowsError:
            print("There is no crash file.")
        except Exception as e:
            utilities.log(e, "Error")
            print(e)

    def givePoints(self, *subcommands):
        print("User id:")
        userId = str(input("> ").strip())

        print("Points")
        points = int(input("> ").strip())

        if self.callBotFunction("givePoints", args=[userId, points]):
            print("Points sent!")
        else:
            print("Bot is not running.")

    def botSay(self, *subcommands):
        print("What is Sir Meowster saying?")
        message = str(input("> ").strip())

        if self.callBotFunction("say", args=[message]):
            return True
        print("Bot is not running.")

    def botSave(self, *subcommands):
        if self.callBotFunction("botSave"):
            return True
        print("Bot is not running.")

    def botLoad(self, *subcommands):
        if self.callBotFunction("botLoad"):
            return True
        print("Bot is not running.")

    def horseRoll(self, *subcommands):
        if self.callBotFunction("botRoll"):
            return True
        print("Bot is not running.")

    def botTest(self, *subcommands):
        if self.callBotFunction("botTest"):
            return True
        print("Bot is not running.")

    #endregion

    #region Main
    def execute(self, command):
        parts = command.split()
        command = parts[0]
        subcommands = parts[1:]

        status = False
        for cmd in self.commands:
            if command in self.commands[cmd]["alias"]:
                call = self.commands[cmd]['call']
                utilities.log(f"Terminal called {call}.")
                try:
                    status = True
                    method = getattr(self, call)
                    method(*subcommands)
                    break
                except reboot:
                    raise reboot()
                except Exception as e:
                    utilities.log(f"Call failed {e}")
                    print(e)
                break
        if status == False:
            print("Command not recognised.")
    
    def main(self):
        inp = input("> ").strip()
        self.execute(inp)
    #endregion

class close(Exception):
    def __init__(self, message="Closing..."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"

class reboot(Exception):
    pass
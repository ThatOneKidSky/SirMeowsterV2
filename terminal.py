import os, json, subprocess, time, variables, socket, utilities
from variables import constants

commandFile = "terminal/commands.json"

class TerminalUI:
    """The terminal, it awaits for commands and handles them without blocking the bot process."""
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
        """Loads a file and returns the content. (not string)"""
        try:
            with open(file, "r") as oFile:
                return oFile.read()
        except FileNotFoundError:
            utilities.log(f"The file {file} was not found", "Error")
            print(f"Error: The file '{file}' was not found.")

    def loadJson(self, file):
        """Loads json from a file name, then returns as string."""
        content = self.loadFile(file)
        if content is not None:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                utilities.log(f"Failed to load {file}.")
                print(f"Error: Json from '{file}' failed to load.", "Error")

    def loadCommands(self):
        """Loads all the commands the terminal can use. (may not actually link to a function)"""
        file = self.loadJson(self.commandFile)
        return file
    #endregion

    #region Command Utils
    def handleSubcommand(self, command, subcommand):
        """Handle the subcommands for a command."""
        if isinstance(subcommand, tuple):
            subcommand = list(subcommand)
        
        matches = []
        for alias in subcommand:
            for subcommands in self.commands[command]["subcommands"]:
                if alias in subcommands["alias"]:
                    matches.append(subcommands["call"])
        
        return matches if matches else ''

    def callBotFunction(self, command, args = []):
        """Attempts to send a function request to the bot with json."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
                clientSocket.connect((constants["host"], constants["port"]))
                clientSocket.sendall(json.dumps({"function":f"{command}","args":args}).encode())

                resonse = clientSocket.recv(1024)
                if self.debugMode:
                    print(f"[debug] {resonse.decode()}")
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
        """Requests the online status of the bot. (waits a bit if the bots offline)"""
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
        """Attempts to start the bot."""
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
        """Attempts to stop the bot, if its online."""
        utilities.log("Bot stop called.")
        if self.callBotFunction("stop"):
            print("Stopped bot.")
        elif "-silent" not in subcommands:
            print("Bot is not running.")
    
    def restart(self, *subcommands):
        """Calls a restart for either the terminal, or the bot. Can handle debug mode, still broken tho."""
        call = self.handleSubcommand("reset", subcommands)

        if isinstance(call, list) and call[0] == "bot":
            utilities.log("Restarting bot...")
            self.botStop("-silent")
            time.sleep(1)

            if len(call) > 1 and call[1] == "debug":
                self.botStart("-debug -ignore")
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
        """Prints the help data for all the terminal commands. (the loaded ones)"""
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
        """Clears the log, and gives the option to save it as another file."""
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
        """Gives a user (with user id) a given amount of points."""
        print("User id:")
        userId = str(input("> ").strip())

        print("Points")
        points = int(input("> ").strip())

        if self.callBotFunction("givePoints", args=[userId, points]):
            print("Points sent!")
        else:
            print("Bot is not running.")

    def botSay(self, *subcommands):
        """Says something through the bot."""
        print("What is Sir Meowster saying?")
        message = str(input("> ").strip())

        if self.callBotFunction("say", args=[message]):
            print("message sent!")
        else:
            print("Bot is not running.")

    #endregion

    #region Main
    def execute(self, command):
        """Attempts to call a terminal function if it matches an alias in the commands list."""
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
        """The main loop, waits for input then attempts to run it."""
        inp = input("> ").strip()
        self.execute(inp)
    #endregion

class close(Exception): #Added so a raise exception can be raised to the main.py
    def __init__(self, message="Closing..."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"

class reboot(Exception): #Added so the main.py actually knows its supposed to open again
    pass
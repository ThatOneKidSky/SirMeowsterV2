import discord, socket, json, threading, os, time, random, utilities, horse, datetime, asyncio, stable, math
from discord.ext import commands
from variables import constants, playerData, shoopPages
from shoop import shoop

intents = discord.Intents.all()

class Bot:
    #region Main
    def __init__(self):
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        # Load token and channel ids
        self.token         = constants["SECRET"]["TOKEN"]
        self.mainChannelId = constants["generalChannel"]

        self.shoops = {}

        self.bot.event(self.on_ready)
        self.bot.event(self.on_raw_reaction_add)
        self.bot.event(self.on_raw_reaction_remove)
        self.bot.event(self.on_interaction)

        self.add_commands()

    async def on_ready(self):
        utilities.log("Bot logged in.")
        print(f"Logged in as {self.bot.user}.")
        self.mainChannel = self.bot.get_channel(self.mainChannelId)
        self.bot.loop.create_task(self.waitTillMidnight())

    def run(self):
        self.bot.run(self.token)
    #endregion

    #region Events
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            customId = interaction.data["custom_id"]
            user = interaction.user
            userId = str(user.id)

            splitData = customId.split(":")
            if len(splitData) != 3:
                print(f"interaction id is missing tags: {splitData}")
                await interaction.message.delete()
                return

            discriminator, page, buttonId = customId.split(":")

            if "shoop" not in discriminator:
                print(f"interaction is not modern or isnt shoop interaction")
                await interaction.message.delete()
                return

            if page not in shoopPages:
                print(f"page '{page}' not found")
                await interaction.message.delete()
                self.shoops[userId] = shoop(user)
                await self.shoops[userId].open()
                return
            

            if userId not in self.shoops:
                self.shoops[userId] = shoop(user, page)

            await interaction.response.defer()
            if self.shoops[userId].lock == True:
                return
            self.shoops[userId].lock = True
            utilities.log(f"User {user.name} shoop locked", "Info")

            if self.shoops[userId].message is not interaction.message:
                self.shoops[userId].message = interaction.message

            if buttonId == "back":
                await self.shoops[userId].backArrow(interaction, page)
                return

            await self.shoops[userId].onClick(self.bot, interaction, page, buttonId)
            return
    
    async def waitTillMidnight(self):
        now = datetime.datetime.now()
        midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"Midnight in: {(midnight - now).total_seconds()} seconds")
        await asyncio.sleep((midnight - now).total_seconds())
        await self.onMidnight()
        self.bot.loop.create_task(self.waitTillMidnight())

    async def onMidnight(self):
        channel = self.bot.get_channel(constants["horseChannel"])
        if channel is None:
            print(f"Error: Channel not found. Check the ID or permissions.")
            return  # Exit if the channel couldn't be found

        Win, Loss, Lost, Div = horse.getRNG()
        winlosslost = f"W{Win}/L{Loss}/L{Lost}"
        print(winlosslost)

        horse.stepRNG()
        Win, Loss, Lost, Div = horse.getRNG()
        winlosslost = f"W{Win}/L{Loss}/L{Lost}"
        print(winlosslost)

        await self.setTopic(channel, winlosslost)
        return

    #endregion

    #region Channel Utils
    async def setTopic(self, channel, topic):
        while True:
            try:
                await channel.edit(topic=topic)
            except discord.Forbidden:
                print("Cannot Edit Channels Topic")
            except discord.HTTPException as e:
                print(f"Failed to update topic: {e}")
            except Exception as e:
                print(f"Unknown error: {e}")
            finally:
                break
        return


    #endregion

    #region Terminal Commands
    def ping(self, *args):
        return "Pong"

    def givePoints(self, *args):
        try:
            if len(args) != 2:
                print("There are less than or more than 2 args.")
                return "There are less than or more than 2 args."
            if not isinstance(args[1], int):
                print("Arg 1 is not an int.")
                return "Arg 1 is not an int."

            user = asyncio.run_coroutine_threadsafe(self.bot.fetch_user(args[0]), self.bot.loop).result()
            channel = asyncio.run_coroutine_threadsafe(self.bot.fetch_channel(constants["generalChannel"]), self.bot.loop).result()
            addedPoints = args[1]
            meow = "877408930941259776" # The id for sir meowster

            userId = str(user.id)
            playerData[userId] = playerData.get(userId, {})
            playerData[userId]["points"] = playerData[userId].get("points", 0) + addedPoints
            playerData[userId]["pointHistory"] = playerData[userId].get("pointHistory", {})
            playerData[userId]["pointHistory"][meow] = playerData[userId]["pointHistory"].get(meow, 0) + addedPoints

            asyncio.run_coroutine_threadsafe(channel.send(content=f"<@{userId}> enjoy {addedPoints} points."), self.bot.loop).result()

            playerData.save()

            return "Added"
        except Exception as e:
            print(e)
            return f"{e}"

    def say(self, *args):
        try:
            if len(args) != 1:
                print("There are less than or more than 1 args.")
                return "There are less than or more than 1 args."
            channel = asyncio.run_coroutine_threadsafe(self.bot.fetch_channel(constants["generalChannel"]), self.bot.loop).result()
            asyncio.run_coroutine_threadsafe(channel.send(content=args[0]), self.bot.loop).result()
            
            return "Said"
        except Exception as e:
            print(e)
            return e

    def stop(self, *args):
        serverThread = threading.Thread(target=stopBot)
        serverThread.start()
        return "Stopping"
    
    def botSave(self, *args):
        playerData.save()
        return "Saved"

    def botLoad(self, *args):
        playerData.reload()
        return "Loaded"

    def botRoll(self, *args):
        return "Rolled"
    
    def botTest(self, *args):
        asyncio.run_coroutine_threadsafe(self.onMidnight(), self.bot.loop).result()
        return "True"
    #endregion

    #region Reactions
    async def on_raw_reaction_add(self, payload):
        await self.handleReaction(payload, True)

    async def on_raw_reaction_remove(self, payload):
        await self.handleReaction(payload, False)
        
    async def handleReaction(self, payload, add = True):
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return False

        try:
            if not hasattr(payload.emoji, "id"):
                raise ValueError("Payload does not contain 'id' attribute.")

            reaction = payload.emoji.id
            if reaction == constants["reactionAdd"]:
                counterChange = 1 if add else -1
            elif reaction == constants["reactionRemove"]:
                counterChange = -1 if add else 1
            else:
                return False
            
            message = await channel.fetch_message(payload.message_id)
            user = self.bot.get_user(payload.user_id)

            if user is None or user.bot or message.author.id == payload.user_id:
                await message.remove_reaction(payload.emoji, user)
                return False
            
            senderId = str(message.author.id)
            reactorId = str(payload.user_id)

            playerData[senderId] = playerData.get(senderId, {})
            playerData[senderId]["points"] = playerData[senderId].get("points", 0)
            playerData[senderId]["pointHistory"] = playerData[senderId].get("pointHistory", {})

            
            playerData[senderId]["points"] += counterChange
            playerData[senderId]["pointHistory"][reactorId] = playerData[senderId]["pointHistory"].get(reactorId, 0) + counterChange

            playerData.save()

            print(f"{user.name} {'added to' if counterChange > 0 else 'removed from'} {message.author.name}")
            print(playerData[senderId]["points"])
            return True
        except Exception as e:
            print(f"Error handling reaction: {e}")
            return False
    #endregion

    #region Bot Commands
    def add_commands(self):
        @self.bot.command(name="openshoop", pass_context = True)
        async def cmdopenShoop(ctx):
            userId = str(ctx.author.id)
            if userId in self.shoops:
                await self.shoops[userId].close()
            
            self.shoops[userId] = shoop(ctx.author)
            await self.shoops[userId].open()
                
        @self.bot.command(name="daily", pass_context = True)
        async def cmddaily(ctx):
            userId = str(ctx.author.id)
            playerData[userId] = playerData.get(userId, {})

            today = int(datetime.datetime.now().strftime("%Y%m%d"))
            yesterday = int((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"))

            dailyTime = playerData[userId].get("daily", 0)

            if today != dailyTime:
                utilities.log(f"Daily called for {userId}.")
                playerData[userId]["daily"] = today

                if dailyTime == yesterday:
                    playerData[userId]["dailyCombo"] = playerData[userId].get("dailyCombo", 0) + 1
                else:
                    playerData[userId]["dailyCombo"] = 1
                
                await ctx.send(f"Daily called!\nCombo! {playerData[userId]['dailyCombo']}")
                await horse.roll(userId, self.bot, aDiv=playerData[userId]["dailyCombo"])
            else:
                await ctx.send("Nah, you aint ready yet.")
                    
        @self.bot.command(name="stable", pass_context = True)
        async def cmdstable(ctx):
            await stable.open(ctx.author, ctx.channel)
            
        @self.bot.command(name="whatsmypunishment", pass_context = True)
        async def cmdpunishment(ctx):
            if not ctx:
                print("No CTX")
                return False
            
            rand = random.randint(0,6)

            if rand == 0:
                await ctx.send("mrrrow")
            elif rand == 1:
                await ctx.send("meow")
            elif rand == 2:
                await ctx.send("prrrr")
            elif rand == 3:
                await ctx.send(">:[")
            elif rand == 4:
                await ctx.send(";-;")
            elif rand == 5:
                await ctx.send("HSSSSS")
            elif rand == 6:
                await ctx.send("death")
    #endregion

def stopBot(save = True):
    if save:
        pass
        #Save
    time.sleep(0.5)
    os._exit(0)

#region Communication Management
def handleMessage(message):
    try:
        message = json.loads(message)
        func = message.get("function")
        args = message.get("args", [])

        if hasattr(meowster, func) and callable(getattr(meowster, func)):
            return getattr(meowster, func)(*args)
        else:
            print(f"Could not find function {func}")
            return f'[debug] Function {func} not found'
    except json.JSONDecodeError:
        return f"[debug] Invalid JSON"
    except Exception as e:
        print(e)
        print(message)
        return f"Error in handling: {e}"

def handleClient(conn):
    with conn:
        data = conn.recv(1024)
        if data:
            response = handleMessage(data.decode())
            print(data.decode())
            conn.sendall(response.encode())

def startBotServer():
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((constants["host"], constants["port"]))
        serverSocket.listen(1)
        utilities.log(f"Terminal <-> Bot connection online")

        while True:
            conn, addr = serverSocket.accept()
            print("Connection from terminal.")
            client = threading.Thread(target=handleClient, args=(conn,))
            client.start()
    except socket.error as e:
        try:
            utilities.log(e, "Error")
        finally:
            stopBot(False)
#endregion

meowster = Bot()
serverThread = threading.Thread(target=startBotServer)
serverThread.start()
meowster.run()
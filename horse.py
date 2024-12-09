import random, discord, utilities, asyncio
import discord.types
from variables import playerData, horseData, constants
from utilities import safeFormat

#region Main
async def roll(userId: str, bot: discord.Client):
    """Rolls a horse for a given {userId}. {bot} is needed for sending messages after a roll."""
    try:
        utilities.log(f"Called roll for {userId}")
        # Get and set win chances, userRNG + baseRNG
        uWin, uLss, uLst, uDiv = getUserRNG(userId)
        Win, Lss, Lst, Div = getRNG()

        winChance = max(uWin + Win, 1)
        lossChance = max(uLss + Lss, 1)
        lostChance = max(uLst + Lst, 1)

        # Make a random roll
        choice = random.randint(0, winChance + lossChance + lostChance)

        if choice < winChance: # If the user wins
            await rollWin(userId, bot, uDiv + Div)
        elif choice < winChance + lossChance: # If the user loses
            await rollLoss(userId, bot)
        elif choice < winChance + lossChance + lostChance: # If the user lost
            await rollLost(userId, bot)

        return True
    except Exception as e:
        utilities.log(f"Error in horse.roll: {e}", "Error")
        print(e)
        return False
#endregion

#region Utils
def getRNG():
    """Returns the W/L/L/D as set in data/horse.json."""
    try:
        win = horseData["RNG"]["win"]
        lss = horseData["RNG"]["loss"]
        lst = horseData["RNG"]["lost"]
        div = horseData["RNG"]["divisor"]
        
        return max(int(win), 1), max(int(lss), 1), max(int(lst), 1), float(div)
    except Exception as e:
        utilities.log(f"Error in horse.getRNG: {e}", "Error")
        print(e)
        return 0, 0, 0, 0

def getUserRNG(userId: str):
    """Returns the W/L/L/D of a user."""
    try:
        playerData[userId] = playerData.get(userId, {})
        playerData[userId]["horse"] = playerData[userId].get("horse", {})
        playerData[userId]["horse"]["RNG"] = playerData[userId]["horse"].get("RNG", {
            "win": 0,
            "loss": 0,
            "lost": 0,
            "divisor": 0
        })

        win = playerData[userId]["horse"]["RNG"].get("win", 0)
        lss = playerData[userId]["horse"]["RNG"].get("loss", 0)
        lst = playerData[userId]["horse"]["RNG"].get("lost", 0)
        div = playerData[userId]["horse"]["RNG"].get("divisor", 0)
        
        return max(int(win), 0), max(int(lss), 0), max(int(lst), 0), float(div)
    except Exception as e:
        utilities.log(f"Error in horse.getUserRNG: {e}", "Error")
        print(e)
        return 0, 0, 0, 0

def getUserHorses(userId: str, includeNonLoseables = True, includeLoseables = True):
    """Returns a dictionary of all horses a user has, with the option to exclude loseables or nonloseables."""
    try:
        playerData[userId] = playerData.get(userId, {})
        playerData[userId]["horse"] = playerData[userId].get("horse", {})
        playerData[userId]["horse"]["count"] = playerData[userId]["horse"].get("count", {})

        horses = {}
        for key, data in playerData[userId]["horse"]["count"].items():
            canLose = data.get("canLose", True)

            if (includeLoseables and canLose) or (includeNonLoseables and not canLose):
                horses[key] = data

        return horses
    except Exception as e:
        utilities.log(f"Error in horse..getUserHorses: {e}", "Error")
        print(f"Error in horse.getUserHorses: {e}")
        return {}

def addHorse(userId: str, horse: dict):
    """Adds a horse to a given user"""
    utilities.log(f"Adding {horse['type']} to {userId}.")
    try:
        playerData[userId] = playerData.get(userId, {})
        playerData[userId]["horse"] = playerData[userId].get("horse", {})
        playerData[userId]["horse"]["count"] = playerData[userId]["horse"].get("count", {})

        horseCount = playerData[userId]["horse"]["count"]

        horseCount[horse["type"]] = horseCount.get(horse["type"], {
            "display": horse.get("display", True),
            "count": 0,
            "canLose": horse.get("canLose", True),
            "special": horse.get("special", False)
        })
        horseCount[horse["type"]]["count"] += 1

        playerData.save()
        return True
    except Exception as e:
        print(f"Error in horse.addHorse: {e}")
        return False

def removeHorse(userId: str, horse: str):
    """Removes a horse from a user and pops the index if horse count drops below 1."""
    utilities.log(f"Removing {horse} from {userId}.")
    try:
        if horse not in playerData.get(userId).get("horse").get("count"):
            return False
        
        playerData[userId]["horse"]["count"][horse]["count"] -= 1
        if playerData[userId]["horse"]["count"][horse]["count"] <= 0:
            playerData[userId]["horse"]["count"].pop(horse)
        
        playerData.save()
        return True
    except Exception as e:
        utilities.log(f"Error in horse.removeHorse: {e}", "Error")
        print(f"Error in horse.removeHorse: {e}")
        return False

async def handleCombo(userId: str, roll: dict, bot: discord.Client, formatValues: dict):
    """A utility function for handling horse combos"""
    utilities.log(f"Handling combo for {userId}.")
    try:
        horseChannel = bot.get_channel(constants["horseChannel"])

        playerData[userId] = playerData.get(userId, {})
        playerData[userId]["horse"] = playerData[userId].get("horse", {})
        playerData[userId]["horse"]["combo"] = playerData[userId]["horse"].get("combo", {})

        combo = roll["combo"]
        comboInto = combo["into"]
        comboDisplay = combo["display"]

        if comboInto not in playerData[userId]["horse"]["combo"]:
            playerData[userId]["horse"]["combo"][comboInto] = {
                "display": comboDisplay,
                "count": 0
            }
        playerData[userId]["horse"]["combo"][comboInto]["count"] += 1
        comboIndex = playerData[userId]["horse"]["combo"][comboInto]["count"]

        comboText = combo["order"][comboIndex-1]
        rolledText = safeFormat(roll["text"] + comboText, formatValues)
        await horseChannel.send(content=rolledText)

        if comboIndex >= len(combo["order"]):
            await asyncio.sleep(3)
            playerData[userId]["horse"]["combo"][comboInto]["count"] = 0
            completeMessage = safeFormat(horseData["secret"][comboInto]["result"]["text"], formatValues)
            addHorse(userId, horseData["secret"][comboInto]["result"])
            await horseChannel.send(content=completeMessage)
        playerData.save()
        return True
    except Exception as e:
        utilities.log(f"Failed to handle combo for {userId}: {e}", "Error")
        return False
#endregion

#region Win/Lose/Lost
async def rollWin(userId: str, bot: discord.Client, div: float):
    """Rolls a winning horse for a given user with a divisor. High div = rarer horses"""
    utilities.log(f"Winning roll called for {userId} with a {div} divisor.")
    try:
        divisor = div + 1 if div >= 0 else 1 / (1 - div)
        userData = playerData.get(userId, {})

        totalWeight = 0
        for horse in horseData["win"]:
            if "combo" in horse and userData.get("horse"):
                if horse["combo"]["into"] in userData["horse"].get("count", {}):
                    if horse["combo"].get("isLoopable", False):
                        continue
            
            totalWeight += int(max(horse["weight"] / divisor, 1))
        
        roll = random.randint(0, totalWeight)
        for horse in horseData["win"]:
            roll -= int(max(horse["weight"] / divisor, 1))
            if roll <= 0:
                rolledHorse = horse
                break
        
        if rolledHorse is None:
            rolledHorse = horseData["win"][0]

        formatValues = {"user": f"<@{userId}>"}

        if "combo" in rolledHorse:
            await handleCombo(userId, rolledHorse, bot, formatValues)
        else:
            addHorse(userId, rolledHorse)

            message = safeFormat(rolledHorse["text"], formatValues)
            horseChannel = bot.get_channel(constants["horseChannel"])
            await horseChannel.send(content=message)
    except Exception as e:
        utilities.log(f"Error in horse.rollWin: {e}", "Error")
        print(f"Error in horse.rollWin: {e}")
        return False

async def rollLoss(userId: str, bot: discord.Client):
    """Rolls a loss horse for a given user."""
    utilities.log(f"Loss roll called for {userId}.")
    try:
        roll = random.choice(horseData["loss"])
        
        formatValues = {"user": f"<@{userId}>"}

        if "combo" in roll:
            await handleCombo(userId, roll, bot, formatValues)
        else:
            message = safeFormat(roll["text"], formatValues)
            horseChannel = bot.get_channel(constants["horseChannel"])
            await horseChannel.send(content=message)
        return True
    except Exception as e:
        utilities.log(f"Error in horse.rollLoss: {e}", "Error")
        print(f"Error in horse.rollLoss: {e}")
        return False

async def rollLost(userId: str, bot: discord.Client):
    """Rolls a lost horse for a given user."""
    utilities.log(f"Lost roll called for {userId}.")
    try:
        if getUserHorses(userId, False) == {}:
            await rollLoss(userId, bot)
            return True


        roll = random.choice(horseData["loss"])
        lostKey, lostHorse = random.choice(list(getUserHorses(userId, False).items()))
        
        formatValues = {"user": f"<@{userId}>", "lost": lostHorse["display"]}
        removeHorse(userId, lostKey)
        
        message = safeFormat(roll["text"], formatValues)
        horseChannel = bot.get_channel(constants["horseChannel"])
        await horseChannel.send(content=message)

        if "combo" in roll:
            await handleCombo(userId, roll, bot, formatValues)
        return True
    except Exception as e:
        utilities.log(f"Error in horse.rollLost: {e}", "Error")
        print(f"Error in horse.rollLost: {e}")
        return False
#endregion   
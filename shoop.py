import discord, asyncio, utilities, horse
from discord.ui import Button, View
from variables import shoopPages, shoopData, playerData
from utilities import safeFormat

class shoop():
    def __init__(self, author, page="default"):
        self.user   = author
        self.userId = str(self.user.id)
        self.page   = page
        self.message = None
        self.lock = False
    
    #region Page updates
    async def open(self):
        pageData = shoopPages[self.page]

        embed = discord.Embed(
            title=pageData["title"],
            color=discord.Color.from_rgb(*tuple(int(pageData["color"][i:i+2],16) for i in (1, 3, 5)))
        )

        buttons = []    
        if "backArrow" in pageData and pageData["backArrow"]:
            button = Button(
                label="",
                emoji=shoopData["shoopArrowEmoji"],
                custom_id=f"shoop:{self.page}:back"
            )

            buttons.append(button)
        
        for item in pageData["items"]:
            embed.add_field(
                name=f"# {item['name']} #",
                value=item["description"],
                inline=True
            )
            
            label, disabled = self.handleButtonPrice(item)
            
            button = Button(
                label=label,
                emoji=item["emoji"],
                custom_id=f"shoop:{self.page}:{item['name']}",
                disabled=disabled
            )

            buttons.append(button)
        
        
        view = View()
        for button in buttons:
            view.add_item(button)

        if self.message:
            await self.message.edit(embed=embed, view=view)
        else:
            self.message = await self.user.send(embed=embed, view=view)
            playerData[self.userId]["messageId"] = self.message.id
            playerData.save()
    
    async def goto(self, page):
        self.page = page
        await self.open()
    #endregion

    #region Utils
    def handleButtonPrice(self, item):
        label = ""
        disabled = item["locked"]

        if not item.get("price"):
            return label, disabled
        
        price = item["price"]
        
        playerData[self.userId] = playerData.get(self.userId, {})

        if price.get("points"):
            cost = price.get("points")
            label += f"{cost['count']}ᑭ"

            if playerData[self.userId].get("points", 0) < cost["count"]:
                if not cost.get("acceptDebt", False):
                    disabled = True

        if price.get("horse"):
            cost = price.get("horse", 0)
            label += f"{cost['count']}♞"

            userHorses = horse.getUserHorses(self.userId, False)

            totalHorses = 0
            for key, data in userHorses.items():
                totalHorses += data["count"]

            if totalHorses < cost["count"]:
                if not cost.get("acceptDebt", False):
                    disabled = True
        
        return label, disabled
    #endregion

    #region Buttons
    async def backArrow(self, interaction, page):
        if page == "CLOSE":
            self.message.delete()
            return

        await self.goto(shoopPages[page]["backArrow"])
        self.lock = False

    async def onClick(self, bot, interaction, page, buttonId):
        utilities.log(f"User {self.user.name} clicked {buttonId}", "Info")
        buttonData = next((i for i in shoopPages[page]["items"] if i["name"] == buttonId), None)

        if buttonData is None:
            print(f"Failed to load: {page} - {buttonId}")
            return

        call = buttonData["call"]

        if "goto" in call:
            await self.goto(call["goto"])

        if "function" in call:
            try:
                utilities.log(f"User {self.user.name} called {call['function']}", "Info")
                await getattr(self, call["function"])(bot, interaction, buttonData)
            except Exception as e:
                utilities.log(f"User {self.user.name} call failed: {e}", "Error")
                await self.goto(page)
        
        await asyncio.sleep(0.5)
        self.lock = False
        utilities.log(f"User {self.user.name} shoop unlocked.", "Info")
    #endregion

    #region Buy functions
    async def horseRoll(self, bot, interaction, buttonData):
        try:
            playerPoints = playerData[self.userId]["points"]
            rollCost = buttonData["price"]["points"]["count"]

            if playerPoints - rollCost >= 0:
                
                await horse.roll(self.userId, bot)
                playerData[self.userId]["points"] -= rollCost
                playerData.save()

                if playerPoints - rollCost >= 0:
                    await self.open()

                await interaction.followup.send(f"{playerPoints - rollCost}ᑭ", ephemeral=True)
            else:
                await self.open()
                await interaction.followup.send(f"Not enough ᑭ to afford this.", ephemeral=True)
        except Exception as e:
            utilities.log(f"Error in shoop.horseRoll: {e}", "Error")
            print(e)
    #endregion

    #region Closers
    async def closeButton(self, bot, interaction, buttonData):
        if self.message:
            try:
                await interaction.message.delete()
            except discord.NotFound:
                pass
            
            self.message = None

    async def close(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
            
            self.message = None
    #endregion

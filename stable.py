import discord, random
from horse import getUserHorses

async def open(user, channel):
    userId = str(user.id)
    horses = getUserHorses(userId)

    embed = discord.Embed(
            title=f"{user.global_name}'s Stable",
            color=discord.Color.from_rgb(random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
        )
    for key, data in horses.items():
        embed.add_field(
            name=f"# {data['display']}: {data['count']}",
            value=f"",
            inline=False
        )

    await channel.send(embed=embed)
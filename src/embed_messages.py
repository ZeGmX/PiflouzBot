import asyncio
import copy
from interactions import Color, Embed, EmbedAttachment, EmbedField, MaterialColors, RoleColors
from math import ceil
import os
import random

from constant import Constants
from database import db
import events
from piflouz_generated import get_stat_str
import seasons
import socials
from user_profile import get_active_profiles
import utils
from wordle import Wordle


def get_embeds_help_message():
    """
    Returns the embed message with help for every command

    Returns
    -------
    embeds (List[interactions.Embed]):
        the embeds (there is more than 25 fields so we need to paginate)
    """
    embeds = [
        Embed(
            title="Need help?",
            color=MaterialColors.RED,
            thumbnail=EmbedAttachment(url=Constants.PIBOU4LOVE_URL),
            fields=[
                EmbedField(
                    name="`/help`",
                    value="Show this message",
                    inline=False
                ),
                EmbedField(
                    name="`/profile`",
                    value="Check all the data from your profile",
                    inline=False
                ),
                EmbedField(
                    name="`/hello`",
                    value="Say hi!",
                    inline=False
                ),
                EmbedField(
                    name="`/is-live streamer_name`",
                    value="Check if a certain streamer is live!",
                    inline=False
                ),
                EmbedField(
                    name="`/setup-channel [twitch|main]`",
                    value="Change the channel where I send messages",
                    inline=False
                ),
                EmbedField(
                    name="`/joke`",
                    value="To laugh your ass off (or not, manage your expectations)",
                    inline=False
                ),
                EmbedField(
                    name="`/donate @user amount`",
                    value="Be generous to others",
                    inline=False
                ),
                EmbedField(
                    name="`/get`",
                    value="Get some piflouz!",
                    inline=False
                ),
                EmbedField(
                    name="`$tarpin`",
                    value="What could that be? Can be used in any channel",
                    inline=False
                ),
                EmbedField(
                    name="`/raffle n`",
                    value="Buy raffle tickets to test your luck ⚠️ Only works during a raffle event ",
                    inline=False
                ),
                EmbedField(
                    name="`/store`",
                    value="Buy fun upgrades",
                    inline=False
                ),
                EmbedField(
                    name="`/giveaway n`",
                    value="Drop a pibox with your own money",
                    inline=False
                ),
                EmbedField(
                    name="`/duel [challenge|play|status]`",
                    value="Earn piflouz by winning challenges against others",
                    inline=False
                ),
                EmbedField(
                    name="`/role [get|remove]`",
                    value="Get a specific notification role",
                    inline=False
                ),
                EmbedField(
                    name="`/achievements list`",
                    value="Check what you need to do to get some achievements",
                    inline=False
                ),
                EmbedField(
                    name="`/wordle guess`",
                    value="Try to solve today's wordle ⚠️ Only works during wordle events",
                    inline=False
                ),
                EmbedField(
                    name="`/wordle status`",
                    value="Check how your wordle is going ⚠️ Only works during wordle events",
                    inline=False
                ),
                EmbedField(
                    name="`/birthday`",
                    value="Check how your baking skills are going ⚠️ Only works during birthday events",
                    inline=False
                ),
            ]
        ),

        Embed(
            title="Need help?",
            color=MaterialColors.RED,
            thumbnail=EmbedAttachment(url=Constants.PIBOU4LOVE_URL),
            fields=[
                EmbedField(
                    name="`/wouldyourather`",
                    value="Create a 'Would you rather?' poll",
                    inline=False
                ),
                EmbedField(
                    name="`/otter`",
                    value="Finally something good in this world",
                    inline=False
                ),
                EmbedField(
                    name="`/set-profile birthday year month day`",
                    value="Set your birthday date for a yearly reminder on the server",
                    inline=False
                ),
                EmbedField(
                    name="`/clear-profile birthday`",
                    value="Remove your birthday date from the database",
                    inline=False
                ),
                EmbedField(
                    name="`/match guess [guess]`",
                    value="Try to solve today's match moving challenge ⚠️ Only works during match moving events",
                    inline=False
                ),
                EmbedField(
                    name="`/subseq guess [word]`",
                    value="Try to solve today's subsequence challenge ⚠️ Only works during subsequence events",
                    inline=False
                ),
                EmbedField(
                    name="`/chess guess [word]`",
                    value="Try to solve today's chess challenge ⚠️ Only works during chess events",
                    inline=False
                ),
                EmbedField(
                    name="Things I do in the background",
                    value=f"- I will send a message everytime the greatest streamers go live on Twitch\n\
- I can give you {Constants.PIFLOUZ_EMOJI} if you click on the button below the piflouz message\n\
- I spawn random gifts from time to time. Be the first to react to earn more {Constants.PIFLOUZ_EMOJI}\n\
- I update the roles\n\
- I create events every day\n\
- I send a cute otter picture everyday\n\
- I randomize some nicknames\n\
- I wish happy birthday to people",
                    inline=False
                )
            ]
        )
    ]

    return embeds


def get_embed_piflouz():
    """
    Creates an embed message containing the explanation for the piflouz game and the balance

    Returns
    -------
    embed (interactions.Embed)
    """
    desc = f"This is the piflouz mining message, click every {Constants.REACT_TIME_INTERVAL} seconds to gain more {Constants.PIFLOUZ_EMOJI}.\n\n\
You just need to click on the {Constants.PIFLOUZ_EMOJI} button below or use the `/get` command.\n\
If you waited long enough ({utils.seconds_to_formatted_string(Constants.REACT_TIME_INTERVAL)}), you will earn some {Constants.PIFLOUZ_EMOJI}! The amount depends on the current event, your powerups, your mining combo and your accuracy to use `/get`.\n\n\
This season will end on <t:{seasons.get_season_end_timestamp()}>.\nYour goal is to earn, donate and flex with as much piflouz as possible. You will earn rewards based on the amount of piflouz you earn and your different rankings."

    embed = Embed(title=f"Come get some {Constants.PIFLOUZ_EMOJI}!", description=desc, thumbnail=EmbedAttachment(url=Constants.PIFLOUZ_URL), color=MaterialColors.AMBER)

    # Rankings
    profiles = get_active_profiles()
    if len(profiles) > 0:
        d_piflouz = [(user_id, profile["piflouz_balance"]) for user_id, profile in profiles.items() if profile["piflouz_balance"] > 0]
        d_piflex = [(user_id, len(profile["discovered_piflex"])) for user_id, profile in profiles.items() if len(profile["discovered_piflex"]) > 0]
        d_donations = [(user_id, profile["donation_balance"]) for user_id, profile in profiles.items() if profile["donation_balance"] > 0]

        ranking_balance = get_ranking_str(d_piflouz)
        ranking_piflex = get_ranking_str(d_piflex)
        ranking_donations = get_ranking_str(d_donations)

        stats = get_stat_str()
        embed.add_field(name="Season statistics", value=stats, inline=False)

        if ranking_balance != "":
            embed.add_field(name="Balance", value=ranking_balance, inline=True)
        if ranking_piflex != "":
            embed.add_field(name="Piflex Discovery", value=ranking_piflex, inline=True)
        if ranking_donations != "":
            embed.add_field(name="Donations", value=ranking_donations, inline=False)

    return embed


def get_ranking_str(list):
    """
    Returns a string representing the ranking for a given score

    Parameters
    ----------
    list (List[(str, int)]):
        (user id, score)

    Returns
    -------
    res (str)
    """
    res = ""
    previous_val, previous_index = 0, 0
    vals = sorted(list, key=lambda key_val: -key_val[1])

    if len(vals) == 0:
        return res

    for i, (user_id, val) in enumerate(vals):
        if i == 10: break  # The embed has a limited size so we limit the amount of user in each ranking

        index = i if val != previous_val else previous_index
        previous_val, previous_index = val, index
        res += f"{index + 1}: <@{user_id}> - {val}\n"
    return res


def get_embed_piflex(user):
    """
    Returns an embed message corresponding to the piflex message

    Parameters
    ----------
    user (interactions.User/Member):
        the user requesting the piflex

    Returns
    -------
    embed (interactions.Embed)
    index (int):
        index of the image/gif
    """
    index = random.randrange(0, len(Constants.PIFLEX_IMAGES_URL))
    image_url = Constants.PIFLEX_IMAGES_URL[index]

    embed = Embed(
        title="PIFLEX",
        description=f"Look how much piflouz {user.mention} has. So much piflouz that they are flexing on you poor peasants! They are so cool and rich that they can just take a bath in piflouz. You mad?",
        color=MaterialColors.AMBER,
        thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL),
        images=[EmbedAttachment(url=image_url)]
    )

    print(f"Piflex with {image_url}")
    return embed, index


def get_embed_store_ui(balance, price_multiplier):
    """
    Returns an embed message corresponding to the store message

    Parameters
    ----------
    balance (int):
        the current balance of the user
    price_multiplier (float):
        the current price multiplier

    Returns
    -------
    embed (interactions.Embed)
    """
    embed = Embed(
        title="Piflouz shop",
        description=f"Here you can buy useful upgrades!\n\n**Your balance: {balance} {Constants.PIFLOUZ_EMOJI}**",
        color=RoleColors.DARK_MAGENTA,
    )

    for emoji, powerup in Constants.POWERUPS_STORE.items():
        powerup = copy.copy(powerup)
        powerup.price = ceil(price_multiplier * powerup.price)
        embed.add_field(name=emoji, value=powerup.get_store_str(), inline=True)

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(name=Constants.PIFLOUZ_EMOJI, value=f"Flex with a custom rank\nCosts {ceil(Constants.PIFLEXER_COST * price_multiplier)} {Constants.PIFLOUZ_EMOJI}, lasts for {utils.seconds_to_formatted_string(Constants.PIFLEX_ROLE_DURATION)}", inline=True)
    embed.add_field(name=Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI, value=f"Piflex: when you have too much piflouz\nCosts {ceil(Constants.PIFLEX_COST * price_multiplier)} {Constants.PIFLOUZ_EMOJI}", inline=True)

    return embed


async def get_embed_otter(title="Otter image of the day!"):
    """
    Returns an embed corresponding to a random otter image

    Parameters
    ----------
    title (str):
        title of the embed

    Returns
    -------
    embed (interactions.Embed)
    """
    url = await socials.get_otter_image()

    embed = Embed(title=title, color=Color.from_rgb(101, 67, 33), images=[EmbedAttachment(url=url)])  # Brown color
    return embed


async def get_embed_end_season(bot):
    """
    Returns an embed announcing the end of a season

    Parameters
    ----------
    bot (interactions.Client)

    Returns
    -------
    embed (interactions.Embed)
    """
    channel = await bot.fetch_channel(db["out_channel"])
    msg = await channel.fetch_message(db["piflouz_message_id"])
    url = msg.jump_url

    embed = Embed(
        title="The season is over!",
        description=f"The last season has ended! Use the `/profile` to see what you earned. Congratulations to every participant!\nThe final rankings are available [here]({url})",
        color=MaterialColors.PURPLE,
        thumbnail=EmbedAttachment(url=Constants.TURBO_PIFLOUZ_ANIMATED_URL)
    )

    return embed


async def get_embed_end_raffle(bot, winner_id, prize):
    """
    Returns an embed announcing the end of a raffle

    Parameters
    ----------
    bot (interactions.Client)
    winner_id (str/int)
    prize (int)

    Returns
    -------
    embed (interactions.Embed)
    """
    msg = await events.fetch_event_message(bot, events.EventType.PASSIVE)
    url = msg.jump_url

    embed = Embed(
        title="The raffle is over!",
        description=f"The raffle has ended! Congratulations to <@{winner_id}> for winning the raffle, earning {prize} {Constants.PIFLOUZ_EMOJI}!\nClick [here]({url}) to see the final participation",
        color=Color.random(),
        thumbnail=EmbedAttachment(url=Constants.PIBOU4STONKS_URL)
    )

    return embed


async def get_embed_wordle(solution, guesses, header_str, user_id):
    """
    Generates the wordle image, host it on imgur and put it in an embed

    Parameters
    ----------
    solution (str):
        the solution of the wordle
    guesses (List[str]):
        the guesses
    header_str (str):
        message written on the embed
    user_id (int):
        id of the guesser
    """
    wordle = Wordle(solution)

    path = f"wordle_tmp_{user_id}.png"
    await asyncio.to_thread(wordle.generate_image, guesses, path)
    url = utils.upload_image_to_imgur(path)
    os.remove(path)

    color = MaterialColors.AMBER
    if len(guesses) > 0 and guesses[-1] == solution:
        color = RoleColors.DARK_GREEN
    elif len(guesses) == Wordle.NB_ATTEMPTS:
        color = RoleColors.DARK_RED

    embed = Embed(title="Wordle", description=header_str, color=color, images=[EmbedAttachment(url=url)])
    return embed

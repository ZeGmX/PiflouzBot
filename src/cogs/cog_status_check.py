from interactions import Extension, OptionType, slash_command, slash_option, auto_defer
from my_database import db

from constant import Constants
from markdown import escape_markdown
import powerups # Used for eval
import socials
import user_profile
import utils


class Cog_status_check(Extension):
    """
    Cog containing all the interactions related to checking information about the user
    --
    Slash commands:
        /is-live
        /balance
        /pilord
        /powerups
        /ranking
        /season-result
    """
  
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="is-live", description="Check if a certain streamer is live", scopes=Constants.GUILD_IDS)
    @slash_option(name="streamer_name", description="The name of the streamer you want to check", opt_type=OptionType.STRING, required=True)
    @auto_defer()
    @utils.check_message_to_be_processed
    async def is_live_cmd(self, ctx, streamer_name):
        """
        Callback for the isLive command
        --
        input:
            ctx: interactions.SlashContext
            streamer_name: str
        """
        stream = socials.get_live_status(streamer_name)
        if stream is not None:
            # The streamer is live
            msg = escape_markdown(f"{streamer_name} is currently live on \"{stream.title}\", go check out on https://www.twitch.tv/{streamer_name} ! {Constants.FUEGO_EMOJI}")
            await ctx.send(msg)
        else:
            # The streamer is not live
            msg = escape_markdown(f"{streamer_name} is not live yet. Follow https://www.twitch.tv/{streamer_name} to stay tuned ! {Constants.FUEGO_EMOJI}")
            await ctx.send(msg)
    

    @slash_command(name="balance", description="Check how many piflouz you have", scopes=Constants.GUILD_IDS)
    @slash_option(name="user", description="The person you want to check. Leave empty to check your own balance", opt_type=OptionType.USER, required=False)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def balance_cmd(self, ctx, user=None):
        """
        Callback for the balance command
        --
        input:
            ctx: interactions.SlashContext
        """
        if user is None: user = ctx.author

        user_id = str(user.id)
        profile = user_profile.get_profile(user_id)
        
        balance = profile["piflouz_balance"]
        content = f"Balance of {user.mention}:\n{balance} {Constants.PIFLOUZ_EMOJI}"

        content += f"\n{profile["turbo_piflouz_balance"]} {Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI}"

        content += f"\n{len(profile["discovered_piflex"])} / {len(Constants.PIFLEX_IMAGES_URL)} piflex images discovered"

        await ctx.send(content, ephemeral=True)


    @slash_command(name="pilord", description="See how much you need to farm to flex with your rank", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def pilord_cmd(self, ctx):
        """
        Callback for the pilord command
        --
        input:
            ctx: interactions.SlashContext
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)

        if user_id in db["current_pilords"]:
            await ctx.send("You are currently a pilord. Kinda flexing right now!", ephemeral=True)
        else:
            amount = profile["piflouz_balance"]
            max_amount = db["profiles"][db["current_pilords"][0]]["piflouz_balance"]
            await ctx.send(f"You need {max_amount - amount} {Constants.PIFLOUZ_EMOJI} to become pilord!", ephemeral=True)  
    

    @slash_command(name="powerups", description="See how powerful you are", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def powerups_cmd(self, ctx):
        """
        Callback for the powerups command
        --
        input:
            ctx: interactions.SlashContext
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)
        content = "Here is the list of powerups you have at the moment:\n"
        has_any_powerup = False

        for powerup_str in profile["powerups"]:
            powerup = eval(powerup_str)
            info = powerup.get_info_str()
            if info != "": 
                content +=  info + "\n"
                has_any_powerup = True

        if not has_any_powerup:
            content = "You don't have any power up at the moment. Go buy one, using `/store`!"   
        await ctx.send(content, ephemeral=True)

    
    @slash_command(name="ranking", description="See how worthy you are", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def ranking_cmd(self, ctx):
        """
        Callback for the ranking command
        --
        input:
        ctx: interactions.SlashContext
        """
        d_piflouz = dict(user_profile.get_inverted("piflouz_balance"))
        d_piflex = dict(user_profile.get_inverted("discovered_piflex"))
        d_donations = dict(user_profile.get_inverted("donation_balance"))
        
        res = ""
        user_id = str(ctx.author.id)

        if user_id in d_piflouz.keys():
            amount_user = d_piflouz[user_id]
            rank = len([val for val in d_piflouz.values() if val > amount_user]) + 1
            res += f"Piflouz ranking: {rank} with {amount_user} {Constants.PIFLOUZ_EMOJI}\n"

        if user_id in d_piflex.keys():
            amount_user = len(d_piflex[user_id])
            rank = len([val for val in d_piflex.values() if len(val) > amount_user]) + 1
            res += f"Piflex discovery ranking: {rank} with {amount_user} discovered piflex images\n"

        if user_id in d_donations.keys():
            amount_user = d_donations[user_id]
            rank = len([val for val in d_donations.values() if val > amount_user]) + 1
            res += f"Piflouz donation ranking: {rank} with {amount_user} {Constants.PIFLOUZ_EMOJI}\n"
        
        if res == "":
            await ctx.send("You are not part of any ranking", ephemeral=True)
        else:
            await ctx.send(res, ephemeral=True)
        

    @slash_command(name="season-result", description="See how much you earned in the last season", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def seasonresult_cmd(self, ctx):
        """
        Callback for the seasonresult command
        --
        input:
        ctx: interactions.SlashContext
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)
        await utils.custom_assert(len(profile["season_results"]) > 0, "You did not participate to the previous season", ctx)

        lines = ["Last season you earned the following:"]
        total = 0
        for key, val in profile["season_results"].items():
            if key.endswith("ranking"):
                score, rank = val
                lines.append(f"{key} - {score} {Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI} - rank {rank + 1}")
                total += score
            else:
                lines.append(f"{key} - {val} {Constants.TURBO_PIFLOUZ_ANIMATED_EMOJI}")
                total += val
        lines.append(f"Total - {total}")
    
        msg = "\n".join(lines)
        await ctx.send(msg, ephemeral=True)
            

def setup(bot):
    Cog_status_check(bot)
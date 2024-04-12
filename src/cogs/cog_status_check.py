import asyncio
from interactions import Extension, OptionType, slash_command, slash_option, auto_defer
from io import BytesIO
from math import sqrt
import matplotlib.pyplot as plt
from my_database import db
import os
from PIL import Image
import requests
from time import time

from constant import Constants
from markdown import escape_markdown
import piflouz_handlers
import powerups # Used for eval
from seasons import bonus_ranking, reward_balance, reward_piflex
import socials
import user_profile
import utils


class Cog_status_check(Extension):
    """
    Cog containing all the interactions related to checking information about the user
    --
    Slash commands:
        /is-live
        /powerups
        /profile
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
        

    @slash_command(name="profile", description="Have a look at all your stats", scopes=Constants.GUILD_IDS)
    @slash_option(name="user", description="The person you want to check. Leave empty to check your own profile", opt_type=OptionType.USER, required=False)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def profile_cmd(self, ctx, user=None):
        """
        Callback for the profile command
        --
        input:
            ctx: interactions.SlashContext
            user: interactions.Member
        """
        member = ctx.author if user is None else user
        path = f"profile_{member.id}.png"
        await asyncio.to_thread(self.save_profile_image, member, path)
        self.save_profile_image(member, path)
        await ctx.send(file=path, ephemeral=True)
        os.remove(path)
        
    
    @staticmethod
    def save_profile_image(member, path):
        """
        Generates and saves the profile image of a member
        --
        input:
            member: interactions.Member
            path: str
        """
        ### Creating the background
        background = Image.open("src/cogs/assets/profile.png")    
        _, ax = plt.subplots()
        plt.axis("off")
        plt.xlim(0, 1600)
        plt.ylim(0, 900)
        ax.invert_yaxis()
        ax.imshow(background)
        
        user_id = str(member.id)
        
        ### Inserting the avatar
        avatar_url = member.display_avatar.url
        response = requests.get(avatar_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # Making the avatar round
        r = img.size[0] // 2
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                d = (x - r) ** 2 + (y - r) ** 2
                if d > r ** 2:
                    img.putpixel((x, y), (255, 255, 255, 0))
                elif r - sqrt(d) < 6:
                    red, greed, blue, _ = img.getpixel((x, y))
                    alpha = int(255 * (r - sqrt(d)) / 6)
                    img.putpixel((x, y), (red, greed, blue, alpha))    
        
        # Inserting the avatar at the correct position
        r_avatar = 99
        avatar_center = (138, 147)
        ax.imshow(img, extent=(avatar_center[0] - r_avatar, avatar_center[0] + r_avatar, avatar_center[1] + r_avatar, avatar_center[1] - r_avatar))


        ### Adding the username
        name_center_pos = (500, 147)
        user_name = member.username
        max_len = 15
        displayed_name = f"@{user_name}" if len(user_name) <= max_len else f"@{user_name[:max_len - 3]}..."
        ax.text(*name_center_pos, displayed_name, fontsize=12, color="white", fontweight="bold", verticalalignment="center", horizontalalignment="center")


        ### Richies
        profile = user_profile.get_profile(user_id)

        # Getting the piflouz image
        response = requests.get(Constants.PIFLOUZ_URL)
        piflouz_img = Image.open(BytesIO(response.content))

        # Getting the turbo piflouz image
        response = requests.get(Constants.TURBO_PIFLOUZ_ANIMATED_URL)
        turbo_piflouz_img = Image.open(BytesIO(response.content))        

        r_piflouz = 25
        msg_piflouz_left_pos, piflouz_emoji_center = (110, 405), (80, 405)
        msg_turbo_piflouz_left_pos, turbo_piflouz_emoji_center = (110, 463), (80, 463)
        ax.imshow(piflouz_img, extent=(piflouz_emoji_center[0] - r_piflouz, piflouz_emoji_center[0] + r_piflouz, piflouz_emoji_center[1] + r_piflouz, piflouz_emoji_center[1] - r_piflouz))
        ax.imshow(turbo_piflouz_img, extent=(turbo_piflouz_emoji_center[0] - r_piflouz, turbo_piflouz_emoji_center[0] + r_piflouz, turbo_piflouz_emoji_center[1] + r_piflouz, turbo_piflouz_emoji_center[1] - r_piflouz))
        ax.text(*msg_piflouz_left_pos, f": {profile["piflouz_balance"]}", fontsize=8, color="white", verticalalignment="center", horizontalalignment="left")
        ax.text(*msg_turbo_piflouz_left_pos, f": {profile["turbo_piflouz_balance"]}", fontsize=8, color="white", verticalalignment="center", horizontalalignment="left")


        ### Mining
        cooldown = user_profile.get_timer(user_id, time())
        daily_bonus = piflouz_handlers.get_current_daily_bonus(user_id, time())
        cooldown_left_pos = (960, 125)
        combo_left_pos = (960, 173)
        daily_bonus_left_pos = (960, 221)
        cooldown_msg = "• Cooldown: " + (utils.seconds_to_formatted_string(cooldown) if cooldown > 0 else "ready to mine!")
        combo_msg = f"• Combo: {profile["mining_combo"]} / {piflouz_handlers.get_max_rewardable_combo(user_id)}"
        daily_bonus_msg = f"• Daily bonus: {daily_bonus} / {Constants.DAILY_BONUS_MAX_STREAK}"

        ax.text(*cooldown_left_pos, cooldown_msg, fontsize=8, color="white", verticalalignment="center", horizontalalignment="left")
        ax.text(*combo_left_pos, combo_msg, fontsize=8, color="white", verticalalignment="center", horizontalalignment="left")
        ax.text(*daily_bonus_left_pos, daily_bonus_msg, fontsize=8, color="white", verticalalignment="center", horizontalalignment="left")


        ### Ranking & Roles  
        d_piflouz = dict(user_profile.get_inverted("piflouz_balance"))
        d_piflex = dict(user_profile.get_inverted("discovered_piflex"))
        d_donations = dict(user_profile.get_inverted("donation_balance"))
        
        msg_piflouz = msg_piflex = msg_donations  = ""
        rank_piflouz = rank_piflex = rank_donations = -1

        if user_id in d_piflouz.keys():
            amount_user = d_piflouz[user_id]
            if amount_user <= 0:
                msg_piflouz = "Piflouz ranking: N/A\n"
            else:
                rank_piflouz = len([val for val in d_piflouz.values() if val > amount_user]) + 1
                rank_piflouz_str = str(rank_piflouz) if rank_piflouz <= 10 else "10+"
                msg_piflouz = f"Piflouz ranking: {rank_piflouz_str}\n"
                if rank_piflouz != 1: msg_piflouz += f"{max(d_piflouz.values()) - amount_user} below #1"

        if user_id in d_piflex.keys():
            amount_user = len(d_piflex[user_id])
            if amount_user <= 0:
                msg_piflex = "Piflex ranking: N/A\n"
            else:
                rank_piflex = len([val for val in d_piflex.values() if len(val) > amount_user]) + 1
                rank_piflex_str = str(rank_piflex) if rank_piflex <= 10 else "10+"
                msg_piflex = f"Piflex ranking: {rank_piflex_str}\n"
                if rank_piflex != 1: msg_piflex += f"{max(len(val) for val in d_piflex.values()) - amount_user} below #1"

        if user_id in d_donations.keys():
            amount_user = d_donations[user_id]
            if amount_user <= 0:
                msg_donations = "Donation ranking: N/A\n"
            else:
                rank_donations = len([val for val in d_donations.values() if val > amount_user]) + 1
                rank_donations_str = str(rank_donations) if rank_donations <= 10 else "10+"
                msg_donations += f"Donation ranking: {rank_donations_str}\n"
                if rank_donations != 1: msg_donations += f"{max(d_donations.values()) - amount_user} below #1"
        
        piflouz_left_pos = (410, 430)
        piflex_left_pos = (785, 430)
        donations_left_pos = (1160, 430)
        
        ax.text(*piflouz_left_pos, msg_piflouz, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")
        ax.text(*piflex_left_pos, msg_piflex, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")
        ax.text(*donations_left_pos, msg_donations, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")
        
        
        ### Season
        # Piflex
        piflex_message = f"• {len(profile["discovered_piflex"])} / {len(Constants.PIFLEX_IMAGES_URL)} piflex images discovered"
        piflex_left_pos = (70, 665)
        ax.text(*piflex_left_pos, piflex_message, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left") 
        
        # Expected reward this season
        tot_reward = reward_balance(profile["piflouz_balance"]) + reward_piflex(len(profile["discovered_piflex"]))
        if 1 <= rank_piflouz <= len(bonus_ranking): tot_reward += bonus_ranking[rank_piflouz - 1]
        if 1 <= rank_piflex <= len(bonus_ranking): tot_reward += bonus_ranking[rank_piflex - 1]
        if 1 <= rank_donations <= len(bonus_ranking): tot_reward += bonus_ranking[rank_donations - 1]
        season_message = f"• Expected reward this season: {tot_reward}"
        season_reward_left_pos = (70, 705)
        ax.text(*season_reward_left_pos, season_message, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")
        turbo_piflouz_emoji_center = (605 + 20 * len(str(tot_reward)), 705)
        ax.imshow(turbo_piflouz_img, extent=(turbo_piflouz_emoji_center[0] - r_piflouz, turbo_piflouz_emoji_center[0] + r_piflouz, turbo_piflouz_emoji_center[1] + r_piflouz, turbo_piflouz_emoji_center[1] - r_piflouz))
        
        # Previous season results
        results = profile["season_results"]
        prev_season_txt = "• Last season results (     ):"
        if len(results) == 0: prev_season_txt += " you did not participate"
        prev_season_left_pos = (70, 745)
        ax.text(*prev_season_left_pos, prev_season_txt, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")
        turbo_piflouz_emoji_center = (445, 745)
        ax.imshow(turbo_piflouz_img, extent=(turbo_piflouz_emoji_center[0] - r_piflouz, turbo_piflouz_emoji_center[0] + r_piflouz, turbo_piflouz_emoji_center[1] + r_piflouz, turbo_piflouz_emoji_center[1] - r_piflouz))

        if len(results) > 0:  # Actually participated in the previous season
            col1 = ["", "Balance", "Rank"]
            col2 = ["Piflouz", f"{results["Balance"]}", "N/A"]
            if "Balance ranking" in results.keys(): col2[2] = f"{results["Balance ranking"][0]} (#{results["Balance ranking"][1] + 1})"
            col3 = ["Piflex", f"{results["Discovered piflex"]}", "N/A"]
            if "Piflex ranking" in results.keys(): col3[2] = f"{results["Piflex ranking"][0]} (#{results["Piflex ranking"][1] + 1})"
            col4 = ["Donations", "", "N/A"]
            if "Donation ranking" in results.keys(): col4[2] = f"{results["Donation ranking"][0]} (#{results["Donation ranking"][1] + 1})"
            
            initial_left_pos = (70, 820)
            col_offset = 180
            for i, col in enumerate([col1, col2, col3, col4]):
                s = "\n".join(col)
                pos = (initial_left_pos[0] + i * col_offset, initial_left_pos[1])
                ax.text(*pos, s, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")


        ### Powerups
        content = ""
        for powerup_str in profile["powerups"]:
            powerup = eval(powerup_str)
            info = powerup.get_info_str()
            if info != "": 
                L = info.split("\n")
                content += f"• {L[0]}\n  {L[1]}\n"

        if len(content) == 0: content = "You don't have any active powerup\nUse /store to buy one!"
        else: content = content[:-1]
        
        content_left_pos = (955, 760)
        ax.text(*content_left_pos, content, fontsize=7, color="white", verticalalignment="center", horizontalalignment="left")
        
        plt.savefig(path, bbox_inches="tight", pad_inches=0, dpi=300)
        
                    

def setup(bot):
    Cog_status_check(bot)
from interactions import Extension, auto_defer, slash_command
from interactions.ext.paginators import Paginator
from math import ceil

from achievement_handler import get_achievements_list
from constant import Constants
import user_profile
import utils


class CogAchievements(Extension):
    """
    Cog containing all the interactions related to purchasing things
    ---
    fields:
        bot: interactions.Client
        achievements_per_page: int
        achievements: Achievement list
        nb_pages: int
    --
    Slash commands:
        /achievements list
    Components:
        page_achievements_list-{i}, i = 0...self.pages - 1
    """

    ACHIEVEMENTS_PER_PAGE = 10

    def __init__(self, bot):
        self.bot = bot
        self.achievements = get_achievements_list()
        self.nb_pages = ceil(len(self.achievements) / self.ACHIEVEMENTS_PER_PAGE)

    @slash_command(name="achievements", description="TBD", sub_cmd_name="list", sub_cmd_description="Check your achievements", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def achiev_list_cmd(self, ctx):
        """
        Callback for the achievements list command

        Parameters
        ----------
        ctx (interactions.SlashContext)
        page (int)
        """
        user_id = str(ctx.author.id)
        profile = user_profile.get_profile(user_id)

        user_achievements = profile["achievements"]

        # Getting the string for each achievement
        res = []
        for a in self.achievements:
            emoji = "✅" if a.to_str() in user_achievements else "❌"
            res.append(f"{emoji} • **{a.name}** • {a.reward} {Constants.PIFLOUZ_EMOJI}\n{a.description}")

        prefix = f"**Progress: {len(user_achievements)} / {len(self.achievements)} achievements unlocked!**\n\n"
        p = Paginator.create_from_list(client=self.bot, content=res, prefix=prefix, page_size=920)  # Using 920, we have exactly 10 achievements per page
        await p.send(ctx, ephemeral=True)

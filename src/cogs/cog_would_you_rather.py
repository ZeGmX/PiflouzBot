from interactions import Extension, Modal, ShortText, auto_defer, message_context_menu, modal_callback, slash_command

from constant import Constants
from database import db
import utils


class CogWouldYouRather(Extension):
    """
    Commands for the "Would you rather?"
    --
    fields:
        bot: interactions.Client
    --
    Slash commands:
        /wouldyourather
    Message commands:
        WYR - edit
    Modals:
        wyr
    """

    MODAL_NAME = "wyr"

    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="wouldyourather", description="Create a custom wouldyourather", scopes=Constants.GUILD_IDS)
    async def wouldyourather_cmd(self, ctx):
        """
        Custom wouldyourather commend for easier formating

        Parameters
        ----------
        ctx (interactions.SlashContext)
        """
        modal = self.get_wyr_modal()

        if str(ctx.author.id) in db["wyr_edit"].keys():
            del db["wyr_edit"][str(ctx.author.id)]

        await ctx.send_modal(modal=modal)

    @message_context_menu(name="WYR - edit", scopes=Constants.GUILD_IDS)
    async def edit_would_you_rather_app(self, ctx):
        """
        Message context application for editing a "Would you rather?" message by Pibot

        Parameters
        ----------
        ctx (ctx)
        """
        start = "> **Would you rather...**\n"
        await utils.custom_assert(self.check_if_wyr_message(ctx.target), "This is not a Pibot-generated 'Would you rather?'", ctx)

        separator = "\n> **or**\n"
        content = ctx.target.content[len(start):].split(separator)
        values = [line[4:] for line in content]

        modal = self.get_wyr_modal(values=values)
        await ctx.send_modal(modal)

        db["wyr_edit"][str(ctx.author.id)] = int(ctx.target.id)

    @modal_callback(MODAL_NAME)
    @auto_defer(ephemeral=True)
    async def wouldyourather_edit_response(self, ctx, **options):
        """
        Response to the "Would you rather?" modal

        Parameters
        ----------
        ctx (interactions.ModalContext)
        options (InputText list)
        """
        # We remove the blank options
        options = [option for option in options.values() if len(option) > 0]

        channel = await self.bot.fetch_channel(ctx.channel.id)
        txt = self.get_wyr_txt(options)
        msg = None

        # We are editing a WYR
        if str(ctx.author.id) in db["wyr_edit"].keys():
            # We recover the id of the original message we are editing
            id = db["wyr_edit"][str(ctx.author.id)]
            msg = await channel.fetch_message(id)
            await msg.edit(content=txt)
            del db["wyr_edit"][str(ctx.author.id)]
        # We are creating a WYR
        else:
            msg = await channel.send(txt)

        await ctx.send("Done!", ephemeral=True)

        # We update the reaction emojis
        emojis = "🇦🇧🇨🇩🇪"

        bot_reac = []
        if msg.reactions is not None:
            bot_reac = [reac.emoji.name for reac in msg.reactions if reac.me and reac.emoji.name in emojis]
        for i in range(len(options)):
            if emojis[i] not in bot_reac:
                await msg.add_reaction(emojis[i])
        for i in range(len(options), len(emojis)):
            if emojis[i] in bot_reac:
                await msg.clear_reactions(emojis[i])

    def get_wyr_modal(self, values=None):
        """
        Generates the modal object for a "Would you rather?"

        Parameters
        ----------
        values (string list):
            the default value for each wyr option

        Returns
        -------
        modal (interactions.Modal)
        """
        nb_options = 5

        if values is None: values = []
        if len(values) < 5: values += [""] * (5 - len(values))

        option_indexes = "ABCDE"

        # The first two are mandatory, the other ones are not
        components = [ShortText(label=f"Option {option_indexes[i]}", custom_id=f"wyr_option_{i}", value=values[i], placeholder="Type your option here", required=i < 2) for i in range(nb_options)]
        return Modal(*components, title="Would you rather...", custom_id=self.MODAL_NAME)

    def get_wyr_txt(self, options):
        """
        Returns the formatted text for a "Would you rather?"

        Parameters
        ----------
        options (str list)

        Returns
        -------
        res (str)
        """
        emojis = "🇦🇧🇨🇩🇪"

        text_start = "> **Would you rather...**\n"
        text_separator = "\n> **or**\n"
        text_end = text_separator.join([f"> {emojis[i]} {options[i]}" for i in range(len(options)) if len(options[i]) > 0])

        return text_start + text_end

    def check_if_wyr_message(self, msg):
        """
        Checks if the message is a "Would you rather?" message by Pibot

        Parameters
        ----------
        msg (interactions.Message)

        Returns
        -------
        res (bool)
        """
        start = "> **Would you rather...**\n"
        return msg.content.startswith(start) and msg.author.id == int(self.bot.user.id)

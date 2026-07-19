import asyncio
from interactions import Extension, OptionType, SlashCommandChoice, auto_defer, slash_command, slash_option

from constant import Constants
from embed_messages import get_container_TCG_pull
from TCG.tcg import generate_random_pack, get_user_collection
import utils


class CogTCG(Extension):
    """
    Commands for the TCG system
    --
    fields:
        bot: interactions.Client
    --
    Slash commands:
        /pull
        /deck
    Message commands:
    Modals:
    """

    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="pull", description="Open a pack and add cards to your collection", scopes=Constants.GUILD_IDS)
    @slash_option(name="pack_type", description="The type of pack you want to open", opt_type=OptionType.STRING, required=True, choices=[
        SlashCommandChoice(name="bell", value="bell"),
        SlashCommandChoice(name="butterfly", value="butterfly"),
        SlashCommandChoice(name="eye", value="eye"),
        SlashCommandChoice(name="hammer", value="hammer")
    ])
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def pull_pack(self, ctx, pack_type: str):
        """
        Opens a pack and adds the card inside to the user's collection

        Returns
        -------
        list of Card
            the cards inside the pack
        """
        usr_id = str(ctx.author.id)
        # TODO: Payment?

        # Generate the cards in the pack
        # TODO: use pack type to change probabilities?
        pack_cards = generate_random_pack()

        # add cards to the user's collection
        user_collection = get_user_collection(usr_id)
        user_collection.add_cards(pack_cards)

        response = await ctx.send(file=f"src/TCG/assets/pack_animations/{pack_type}.gif")

        await asyncio.sleep(3)  # Wait for the animation to finish

        for i in range(len(pack_cards)):
            await asyncio.sleep(1)  # Wait for the card to be revealed

            sub_pack_cards = pack_cards[:i + 1]

            images = [card.get_image_path(small=False) for card in sub_pack_cards]
            card_names = [str(card) for card in sub_pack_cards]

            container = get_container_TCG_pull(card_names, images, pack_type)
            await response.edit(content=None, components=[container], context=ctx, files=images)

    @slash_command(name="deck", description="Display your card collection", scopes=Constants.GUILD_IDS)
    @slash_option(name="user", description="The person you want to check. Leave empty to check your own profile", opt_type=OptionType.USER, required=False)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def display_deck(self, ctx, user=None):
        """
        Event for the /deck command, renders and display the user's deck
        """
        member = user or ctx.author

        usr_collection = get_user_collection(member.id)

        response_str = f"Here are the cards of {member.nick}:\n"
        response_str += usr_collection.__str__()
        response_str += "\nThis command is a WIP. Visualisation is coming."
        await ctx.send(response_str)

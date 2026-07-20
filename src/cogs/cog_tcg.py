import asyncio
from interactions import Extension, OptionType, SlashCommandChoice, auto_defer, slash_command, slash_option
import os
from PIL import Image

from constant import Constants
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

        await asyncio.sleep(5)  # Wait for the animation to finish

        card_imgs = []
        # Read all images
        for i in range(len(pack_cards)):
            path = pack_cards[i].get_image_path(small=False)
            card_imgs.append(Image.open(path))

        card_img_size = card_imgs[0].size
        padding = 50
        total_width = card_img_size[0] * len(card_imgs) + padding * (len(card_imgs) - 1)
        total_height = card_img_size[1]

        final_img = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 0))
        frames = [final_img.copy()]

        # Paste images onto the new image
        for i, img in enumerate(card_imgs):
            final_img.paste(img, (i * (card_img_size[0] + padding), 0))
            frames.append(final_img.copy())

            print(final_img.getpixel((2635, 830)), frames[-1].getpixel((2635, 830)), frames[-2].getpixel((2635, 830)))  # Debugging line to check pixel values

        # Save the new image
        file = f"src/TCG/assets/tmp/{ctx.author.id}.gif"
        durations = [500] + [2000] * (len(pack_cards) - 1) + [60000]  # 500ms for the first frame, 2000ms for each card reveal, and a long duration for the last frame
        frames[0].save(file, save_all=True, append_images=frames[1:], optimize=False, duration=durations, loop=0)

        txt = f"You opened a {pack_type} pack and got the following cards:"

        await response.edit(content=txt, file=file, context=ctx)

        # delete the temporary file after sending it
        if os.path.exists(file):
            os.remove(file)

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

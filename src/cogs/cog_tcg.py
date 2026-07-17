import utils

from constant import Constants
from database.my_database import ElementList
from interactions import Extension, OptionType, auto_defer, slash_command, slash_option
from tcg import Collection, generate_random_pack
from user_profile import get_profile

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
    
    @staticmethod
    def get_user_collection(user_id):
        """
        Returns the user's collection of cards
        Also creates an empty collection if the user doesn't have one yet.

        Args:
            user_id (int/str): The ID of the user
        """
        profile = get_profile(user_id)
        
        
        if "card_collection" not in profile:
            profile["card_collection"] = Collection.create_empty_collection()
        
        fetched_result = profile["card_collection"]
        
        assert isinstance(fetched_result, ElementList), "Profile is not an ElementList"
        return Collection(fetched_result)
    
    @slash_command(name="pull", description="Open a pack and add cards to your collection", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def pull_pack(self, ctx):
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
        pack_cards = generate_random_pack()
        
        # add cards to the user's collection
        user_collection = self.get_user_collection(usr_id)
        user_collection.add_cards(pack_cards)
        
        # TODO: Play opening animation

        await ctx.send("You opened a pack and got the following cards: " + ", ".join([card.name for card in pack_cards]) + ".\nThis is a very rough message for now, visualisation is a WIP.")
        

    @slash_command(name="deck", description="Display your card collection", scopes=Constants.GUILD_IDS)
    @slash_option(name="user", description="The person you want to check. Leave empty to check your own profile", opt_type=OptionType.USER, required=False)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def display_deck(self, ctx, user=None):
        """
        Event for the /deck command, renders and display the user's deck
        """
        member = user or ctx.author

        usr_collection = self.get_user_collection(member.id)
        
        response_str = f"Here are the cards of {member.nick}:\n"
        response_str += usr_collection.__str__()
        response_str += "\nThis command is a WIP. Visualisation is coming." 
        await ctx.send(response_str)
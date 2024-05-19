from interactions import Extension, Button, ButtonStyle, OptionType, slash_command, auto_defer, slash_option
from interactions.ext.paginators import Paginator
from math import ceil

from achievement_handler import get_achievements_list
from constant import Constants
from my_database import db
import user_profile
import utils
import interactions

class Cog_birthday_tracker(Extension):
    """
    Cog containing all the interactions related to purchasing things
    ---
    fields:
        bot: interactions.Client
    --
    Slash commands: 
        /set-profile birthday
        /clear-profile birthday
    Components:
        months_array: List[str] - List of all the months names.
    """

    months_array = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    def __init__(self, bot):
        self.bot = bot


    @slash_command(name="set-profile", description="#TODO", sub_cmd_name="birthday",sub_cmd_description="Set your birthday date for a yearly reminder on the server", scopes=Constants.GUILD_IDS)
    @slash_option(name="year", description="Your birthday year. Format YYYY", opt_type=OptionType.INTEGER, required=True, min_value=1900)
    @slash_option(name="month", description="Your birthday month. Format MM", opt_type=OptionType.INTEGER, required=True, min_value=1, max_value=12)
    @slash_option(name="day", description="Your birthday day. Format DD", opt_type=OptionType.INTEGER, required=True, min_value=1, max_value=31)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def set_profile_cmd(self, ctx:interactions.SlashContext,year:int,month:int,day:int):
        """
        Stores the birthday date of a user in the database.
        --
        input:
            ctx: interactions.SlashContext
            year: int - Year of birth
            month: int - month of birth
            day: int - day of birth
        """

        is_valid,error_message = self.check_valid_birthday(year=year,month=month,day=day)
        await utils.custom_assert(condition=is_valid,msg=error_message,ctx=ctx)

        date = self.format_date(year=year,month=month,day=day)
        user_id = int(ctx.user.id)
        profile = user_profile.get_profile(user_id=user_id)

        if profile["birthday_date"] != "0000-00-00":
            output_message = f"Updated your birthday from {profile["birthday_date"]} to {date}."
        else:
            output_message = f"Set your birthday to {date}!"
        profile["birthday_date"] = date

        await ctx.send(output_message)


    @slash_command(name="clear-profile", description="#TODO", sub_cmd_name="birthday",sub_cmd_description="Remove your birthday date from the database", scopes=Constants.GUILD_IDS)
    @auto_defer(ephemeral=True)
    @utils.check_message_to_be_processed
    async def clear_profile_cmd(self, ctx:interactions.SlashContext):
        """
        Removes the birthday date of a user from the database.
        --
        input:
            ctx: interactions.SlashContext
        """
        user_id = int(ctx.user.id)
        profile = user_profile.get_profile(user_id=user_id)
        profile["birthday_date"] = "0000-00-00"
        await ctx.send("Removed your birthday from the database!")


    def format_date(self,year:int,month:int,day:int)->str:
        """Formats dates elements into a string, used to store in the database.

        Args:
            year (int)
            month (int)
            day (int)

        Returns:
            str: The formatted date, format "YYYY-MM-DD"
        """
        month_str = str(month)
        if month<10:
            month_str = f"0{month_str}"

        day_str = str(day)
        if day<10:
            day_str = f"0{day_str}"

        return f"{year}-{month_str}-{day_str}"


    def is_leap_year(self,year:int)->bool:
        """Check whether a year is leap

        Args:
            year (int): the year to check

        Returns:
            bool: true if the year is leap
        """
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


    def check_valid_birthday(self,year:int,month:int,day:int)->tuple[bool,str]:
        """Checks weether a given date is a real date

        Args:
            year (int): year of the date
            month (int): month of the date
            day (int): day of the date

        Returns:
            bool: Whether the date is valid
            str: Indicative message of why the 
        """
        if day == 31:
            return month in [1,3,5,7,8,10,12], f"{self.months_array[month-1]} does not have 31 days!"

        if month == 2: # February
            if self.is_leap_year(year=year):
                return (day<=29, f"February {year} only has 29 days!")
            else:
                return (day<29, f"February {year} only has 28 days!")
        return True,""

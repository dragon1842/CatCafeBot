import discord
import cogs.variables as var
from discord.ext import commands
from discord import app_commands
from .ai_generation import ai_response


class counting_game(commands.Cog):
    
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.bot.load_count()
    
    async def status_update(self, bot: commands.Bot):
            channel = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
            bot_embed_colour = discord.Colour.blurple()
            status_embed = discord.Embed(
                title="All bot stats:",
                description=f"Current Count: {self.bot.current_count}\n"
                f"Next: {self.bot.next_number}\n"
                f"Last user: <@{self.bot.last_user_id}>\n"
                f"Reset Point: {(self.bot.current_count // 100) * 100}\n"
                f"Record: {self.bot.counting_record}\n"
                f"Record Holder: <@{self.bot.record_holder}>\n"
                f"Current Streak: {self.bot.current_streak}\n"
                f"Record Streak: {self.bot.record_streak}\n"
                f"Saves Available: {self.bot.count_saves}",
                colour=bot_embed_colour,
            )
            await channel.send(content= "Current status:", embed=status_embed)
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != var.counting_channel:
            return
        if not message.content.isdigit():
            return

        counted_number = int(message.content)

        if message.author.id == self.bot.last_user_id:
            try:
                repeated_user_response = await ai_response(
                    user_prompt="I've counted consequtively knowing that I shouldn't, which has broken the flow of the counting game."
                )
                await message.reply(content=repeated_user_response)
            except Exception as e:
                error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
                await error_reporting.send(content=f"consecutive count response error:\n{e}")
                await message.reply(content="What are you incapable of, following the rules, or reading?")
            if self.bot.count_saves > 0:
                await self.saved_count_handler(message)
            else:
                await self.reset_count_handler(message)
            return

        if counted_number != self.bot.current_count + 1:
            try:
                not_consecutive_response = await ai_response(
                    user_prompt="I've misread the previous number and sent in the wrong one, breaking the flow of the counting game."
                    )
                await message.reply(content=not_consecutive_response)
            except Exception as e:
                error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
                await error_reporting.send(content=f"wrong number response error:\n{e}")
                await message.reply(content=
                    "It appears that you've either forgotten the meaning of 'consecutive' or what the next number is. Pity."
                    )
            if self.bot.count_saves > 0:
                await self.saved_count_handler(message)
            else:
                await self.reset_count_handler(message)
            return

        await self.correct_count_handler(message, counted_number)

    async def saved_count_handler(self, message):
        self.bot.current_streak = 0
        self.bot.count_saves -= 1
        try:
            self.bot.save_count()
        except Exception as e:
            error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
            await error_reporting.send(content=f"save_count error:\n{e}")
            self.status_update()
            pass
        await message.add_reaction(var.error)
        await message.channel.send(content=f"The count has been preserved by a save, try again. The next number is {self.bot.next_number}")
        
    async def reset_count_handler(self, message):
        self.bot.current_count = (self.bot.current_count // 100) * 100
        self.bot.next_number = self.bot.current_count + 1
        self.bot.current_streak = 0
        self.bot.last_user_id = None
        try:
            self.bot.save_count()
        except Exception as e:
            error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
            await error_reporting.send(content=f"save_count error:\n{e}")
            self.status_update()
            pass
        await message.add_reaction(var.counting_cross)
        await message.channel.send(content=f"The next number is {self.bot.next_number}")

    async def correct_count_handler(self, message, counted_number):
        self.bot.current_count = counted_number
        self.bot.next_number = counted_number + 1
        self.bot.last_user_id = message.author.id
        self.bot.latest_message = message.id
        self.bot.record_save(message.author.id)
        try:
            self.bot.save_count()
        except Exception as e:
            error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
            await error_reporting.send(content=f"save_count error:\n{e}")
            await self.status_update()
            pass

        def special_number_checker(counted_number):
            checker_response = []
            # Sequence Checker
            num_digits = list(map(int, str(counted_number)[::-1]))
            if all(
                num_digits[i] - 1 == num_digits[i + 1]
                for i in range(len(num_digits) - 1)
            ) or all(
                num_digits[i] + 1 == num_digits[i + 1]
                for i in range(len(num_digits) - 1)
            ):
                checker_response.append(
                "Hey, that's a perfect sequence[!]"
                "(https://tenor.com/view/thats-it-yes-thats-it-that-right-there-omg-that-thats-what-i-mean-gif-17579879)"
                    )

            # Palindrome Checker
            if str(counted_number) == str(counted_number)[::-1]:
                checker_response.append(
                "Hey, that's a palindrome[!]"
                "(https://tenor.com/view/thats-it-yes-thats-it-that-right-there-omg-that-thats-what-i-mean-gif-17579879)"
                    )

            # SixtyNice Checker
            if "69" in str(counted_number) and "69" not in str(counted_number - 1):
                checker_response.append(
                "https://tenor.com/view/noice-nice-click-gif-8843762"
                )
            # Order 66 Checker
            if "66" in str(counted_number) and "66" not in str(counted_number - 1):
                checker_response.append(
                "https://tenor.com/view/execute-order66-order66-66-palpatine-star-wars-gif-20468321"
                )
            # Devil's Number Checker
            if "666" in str(counted_number) and "666" not in str(counted_number - 1):
                checker_response.append(
                "https://tenor.com/view/hail-satan-gif-25445039"
                )
            return checker_response

        if counted_number % 100 == 0:
            await message.add_reaction(var.hundred_emoji)
        elif counted_number == self.bot.counting_record:
            await message.add_reaction(var.approve_tick)
        else:
            await message.add_reaction(var.non_record_tick)

        for i in special_number_checker(counted_number):
            await message.channel.send(i)


    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.channel.id != var.counting_channel:
            return
        if before.id == self.bot.latest_message:
            try:
                edited_response = await ai_response(
                    user_prompt="I have attempted to deceive the others playing the counting game by editing my message."
                )
                await before.channel.send(content=
                    (f"{edited_response}\nThe number was {self.bot.current_count}.\n"
                    f"The next number is {self.bot.next_number}.")
                    )
            except Exception as e:
                error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
                await error_reporting.send(content=f"edit response error:\n{e}")
                await before.channel.send(content=
                    f"{before.author.mention} has edited their message, the sneaky devil!\n"
                    f"The number was {self.bot.current_count}. The next number is {self.bot.next_number}."
                    )


    @commands.Cog.listener()
    async def on_message_delete(self, message=discord.Message):
        if message.channel.id != var.counting_channel:
            return
        if message.id == self.bot.latest_message:
            try:
                deleted_response = await ai_response(
                    user_prompt="I have attempted to deceive the others playing the counting game by deleting my message."
                    )
                await message.channel.send(content=
                    f"{deleted_response}\nThe number was {self.bot.current_count}.\n"
                    f"The next number is {self.bot.next_number}."
                    )
            except Exception as e:
                error_reporting = self.bot.get_channel(var.testing_channel) or await self.bot.fetch_channel(var.testing_channel)
                await error_reporting.send(content=f"delete response error:\n{e}")
                await message.channel.send(content=
                    f"{message.author.mention} has deleted their message, the sneaky devil!\n"
                    f"Their number was {self.bot.current_count}. The next number is {self.bot.next_number}."
                    )


    # slash commands
    counting_commands = app_commands.Group(name="counting", description="commands related to the counting game")

    @counting_commands.command(name="status", description="A full run-down of the bot's status.")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bot_embed_colour = interaction.user.colour
        bot_guild = self.bot.get_guild(var.guild_id) or await self.bot.fetch_guild(var.guild_id)
        last_user_object = bot_guild.get_member(self.bot.last_user_id) or await bot_guild.fetch_member(self.bot.last_user_id)
        record_holder_object = bot_guild.get_member(self.bot.record_holder) or await bot_guild.fetch_member(self.bot.record_holder)
        statusembed = discord.Embed(
            title="All bot stats:",
            description=f"Current Count: {self.bot.current_count}\n"
            f"Next: {self.bot.next_number}\n"
            f"Last user: {last_user_object.mention}\n"
            f"Reset Point: {(self.bot.current_count // 100) * 100}\n"
            f"Record: {self.bot.counting_record}\n"
            f"Record Holder: {record_holder_object.mention}\n"
            f"Current Streak: {self.bot.current_streak}\n"
            f"Record Streak: {self.bot.record_streak}\n"
            f"Saves Available: {self.bot.count_saves}",
            colour=bot_embed_colour,
        )
        await interaction.followup.send(embed=statusembed)


    @counting_commands.command(name="record", description="Displays this server's counting record.")
    async def record(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bot_embed_colour = interaction.user.colour
        bot_guild = self.bot.get_guild(var.guild_id) or await self.bot.fetch_guild(var.guild_id)
        record_holder_object = bot_guild.get_member(self.bot.record_holder) or await bot_guild.fetch_member(self.bot.record_holder)
        recordmebed = discord.Embed(
            title="Counting Record:",
            description=f"This server's counting record is __**{self.bot.counting_record}**__.\n"
            f"It was achieved by {record_holder_object.mention}.",
            colour=bot_embed_colour,
        )
        await interaction.followup.send(embed=recordmebed)


    @counting_commands.command(
        name="next",
        description="Tells you what the next number is. Because apparently reading is hard.",
    )
    async def nextnumber(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bot_embed_colour = interaction.user.colour
        bot_guild = self.bot.get_guild(var.guild_id) or await self.bot.fetch_guild(var.guild_id)
        last_user_object = bot_guild.get_member(self.bot.last_user_id) or await bot_guild.fetch_member(self.bot.last_user_id)
        nextembed = discord.Embed(
            title="Next Number:",
            description=f"The next number is __**{self.bot.next_number}**__.\n"
            f"The last person to count was {last_user_object.mention}.",
            colour=bot_embed_colour,
        )
        await interaction.followup.send(embed=nextembed)


    @counting_commands.command(
        name="streak", description="Displays the current and record counting streaks."
    )
    async def streakinfo(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bot_embed_colour = interaction.user.colour
        streakembed = discord.Embed(
            title="Streak Information:",
            description=f"The current streak is __**{self.bot.current_streak}**__.\n"
            f"The streak record is __**{self.bot.record_streak}**__.",
            colour=bot_embed_colour,
        )
        await interaction.followup.send(embed=streakembed)


async def setup(bot: commands.Bot):
    cog = (counting_game(bot))
    await bot.add_cog(cog)
    try:
        await bot.tree.add_command(cog.counting_commands)
    except app_commands.CommandAlreadyRegistered:
        pass
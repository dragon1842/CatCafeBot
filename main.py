import discord, json, os
import datetime as dat
import cogs.variables as var
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv


load_dotenv()

class CatCafeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="$", intents=discord.Intents.all(), help_command=None)
        self.current_count = 0
        self.last_user_id = None
        self.latest_message = None
        self.counting_record = 0
        self.record_holder = None
        self.current_streak = 0
        self.record_streak = 0
        self.count_saves = 0

        self.load_count()
        self.next_number = self.current_count + 1

    def load_count(self):
        if os.path.exists("icb_memory.json"):
            with open("icb_memory.json", "r") as f:
                try:
                    data = json.load(f)
                    self.current_count = data.get("current_count", 0)
                    self.last_user_id = data.get("last_user_id", None)
                    self.latest_message = data.get("latest_message", None)
                    self.counting_record = data.get("counting_record", 0)
                    self.record_holder = data.get("record_holder", None)
                    self.current_streak = data.get("current_streak", 0)
                    self.record_streak = data.get("record_streak", 0)
                    self.count_saves = data.get("count_saves", 0)
                except json.JSONDecodeError:
                    self.save_count()

    def save_count(self):
        data = {
            "current_count": self.current_count,
            "last_user_id": self.last_user_id,
            "latest_message": self.latest_message,
            "counting_record": self.counting_record,
            "record_holder": self.record_holder,
            "current_streak": self.current_streak,
            "record_streak": self.record_streak,
            "count_saves": self.count_saves,
        }
        with open("icb_memory.json", "w") as f:
            json.dump(data, f)

    def record_save(self, message_author):
        if self.current_count > self.counting_record:
            self.counting_record = self.current_count
            self.record_holder = message_author
            self.current_streak += 1
            if self.current_streak > self.record_streak:
                self.record_streak = self.current_streak
            if self.current_streak >= (10**(self.count_saves + 2)):
                self.count_saves += 1
    
    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")

    async def on_message(self, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            if not message.author.bot:
                await message.reply(f"{var.error} You can't use the bot here.", delete_after=5)
                pass
        else:
            await bot.process_commands(message)
        
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        return

bot = CatCafeBot()
intents = discord.Intents.all()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        message = f"{var.error} You can't execute this command."
    elif isinstance(error, app_commands.CommandOnCooldown):
        ts_now = dat.datetime.now(dat.timezone.utc).timestamp()
        message = f"{var.error} This command is on cooldown! Try again <t:{int(ts_now + error.retry_after)}:R>."
    elif isinstance(error, app_commands.CheckFailure):
        message = f"{var.error} You do not have permission to use this command."
    elif isinstance(error, app_commands.NoPrivateMessage):
        message  = f"{var.error} You can't use this bot in DMs!"
    else:
        message = f"An unexpected error occured. Please alert the bot owner.\n{error}"
        error_logging_channel = bot.get_channel(var.testing_channel) or await bot.fetch_channel(var.testing_channel)
        await error_logging_channel.send(f"{var.error} Error executing {interaction.command.name}:\n{error}\nUser:{interaction.user.name}")

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    from cogs.nitro_setup import nitro_role_picker
    bot.add_view(nitro_role_picker())
    print("Nitro picker view initialised.")
    from cogs.verification import user_verification_button
    bot.add_view(user_verification_button())
    print("Verification view initialised.")
    try:
        bot.tree.allowed_contexts = app_commands.AppCommandContext(guild=True, private_channel=False, dm_channel=False)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally.")
    except discord.HTTPException as e:
        print(f"Error syncing commands: {str(e)}")

if __name__ == "__main__":
    bot.run(os.getenv("CATCAFE_API_KEY"))
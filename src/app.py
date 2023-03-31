import uvloop

uvloop.install()

import config

from warnings import warn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client as PyrogramClient
from pyrogram import emoji, filters, idle, StopPropagation
from pyrogram.types import (
    BotCommand,
    Message,
)

from context import CONTEXT, UserContext
from database import Database
from modules.file import FileModule

# Modules
from modules.settings import SettingsModule
from modules.webdav import WebdavModule


# Parse acl users
def create_filter():
    u = []
    for user in config.ACL_USERS.split(","):
        user = user.strip()
        if not user.startswith("@"):  # ID
            u.append(int(user))
        else:  # Username
            u.append(user.removeprefix("@"))

    if len(u) == 0 and config.ACL_MODE.lower() == "whitelist":
        warn("No one can access to the bot")

    return filters.user(u)


acl_filter = create_filter()

scheduler = AsyncIOScheduler()
database = Database(db=0)
context = UserContext(db=0)

# Modules instantiation
settings_module = SettingsModule(context, database)
file_module = FileModule(context, database)
webdav_moduele = WebdavModule(context, database, scheduler)

# WARNING: workers parameter pushed because that will run in a 1-CPU
app = PyrogramClient(
    "deverlop",
    api_id=config.TELEGRAM_API_ID,
    api_hash=config.TELEGRAM_API_HASH,
    bot_token=config.TELEGRAM_BOT_TOKEN,
    workers=5,
)


@app.on_message(group=-1)
async def acl_check(_, message: Message):
    r = await acl_filter(_, message)

    if (config.ACL_MODE.lower() == "blacklist" and r) or (
        config.ACL_MODE.lower() == "whitelist" and not r
    ):
        raise StopPropagation()


@app.on_message(filters.command("start"))
async def start(_, message: Message):
    user = message.from_user.id
    context.update(user, CONTEXT["INITIALIZE"])

    if not database.contains_user(user):
        database.add_user(user)
        name = message.from_user.first_name or message.from_user.username

        await app.send_message(user, f"Welcome **{name}**.")
        await app.send_message(
            user, f"To start to use put your configuration in /settings"
        )

        context.update(user, CONTEXT["IDLE"])
    else:
        await app.send_message(user, "You are already logged")


@app.on_message(filters.command("help"))
async def help(_, message: Message):
    user = message.from_user.id

    await app.send_message(user, "**Help:**\n\nComming soon... :)")


# Register all modules callbacks
settings_module.register(app)
file_module.register(app)
webdav_moduele.register(app)


async def main():
    async with app:
        scheduler.start()

        # Set Bot Commands
        await app.set_bot_commands(
            [
                BotCommand("start", f"{emoji.ROBOT} Start the bot"),
                BotCommand("settings", f"{emoji.GEAR} Bot settings"),
                BotCommand("list", f"{emoji.OPEN_FILE_FOLDER} List cloud entries"),
                BotCommand("free", f"{emoji.BAR_CHART} Free space on cloud"),
                BotCommand("wipe", f"{emoji.BROOM} Delete all the files in the cloud"),
                BotCommand("status", f"{emoji.SCROLL} Get bot status"),
                BotCommand("help", f"{emoji.RED_QUESTION_MARK} Help!"),
            ]
        )
        await idle()


if __name__ == "__main__":
    app.run(main())

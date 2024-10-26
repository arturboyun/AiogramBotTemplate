import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from aiogram_dialog import AccessSettings, DialogManager, StartMode, setup_dialogs

from bot.dialogs.menu.dialog import menu_dialog
from bot.config import get_config
from bot.states import Menu

config = get_config()

logging_level = logging.DEBUG if config.DEBUG else logging.INFO
logging.basicConfig(level=logging_level, stream=sys.stdout)
logger = logging.getLogger("MAIN")

key_builder = DefaultKeyBuilder(with_destiny=True)
storage = RedisStorage.from_url(str(config.REDIS_DSN), key_builder=key_builder)
dp = Dispatcher(storage=storage)
main_router = Router()


def register_dialogs(router: Router):
    """
    Register all dialogs in the router
    """
    router.include_router(menu_dialog)


@main_router.message(CommandStart())
async def command_start_handler(
    message: Message, dialog_manager: DialogManager
) -> None:
    logger.info(f"Command /start from {message.from_user.id}")
    await dialog_manager.start(
        Menu.main,
        mode=StartMode.RESET_STACK,
        access_settings=AccessSettings(config.ADMIN_IDS),
    )


@main_router.message(Command("photo_id"))
async def photo_id(message: Message):
    if not message.reply_to_message:
        return await message.answer("Reply to a photo message with this command.")
    logger.info(f"Command /photo_id from {message.from_user.id}")
    await message.answer(
        f"Photo id: <code>{message.reply_to_message.photo[-1].file_id}</code>"
    )


async def main():
    bot = Bot(
        token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp.include_router(main_router)

    register_dialogs(dp)
    setup_dialogs(dp)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())

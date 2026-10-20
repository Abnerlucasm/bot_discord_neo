import asyncio
import logging


def setup_interaction_handler(bot):
    if getattr(bot, "_view_restoration_listener_registered", False):
        return

    from cogs.persistence import restore_views

    restored = False

    async def restore_views_on_ready():
        nonlocal restored
        if restored:
            return

        await asyncio.sleep(1)
        logging.info("Restaurando views persistentes")
        restored = await restore_views(bot)
        if restored:
            logging.info("Views persistentes restauradas")
        else:
            logging.error("Não foi possível restaurar as views persistentes")

    bot.add_listener(restore_views_on_ready, "on_ready")
    bot._view_restoration_listener_registered = True

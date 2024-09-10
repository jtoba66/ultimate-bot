import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.telegram_agent import TelegramAIAgent

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """
    Post initialization hook for the application.
    This is where we'll initialize our TelegramAIAgent.
    """
    jackal_api_url = os.getenv('JACKAL_API_URL', 'https://api.jackalprotocol.com/')
    coingecko_api_url = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3/simple/price')
    llama_api_key = os.getenv('LLAMA_API_KEY')
    telegram_agent = TelegramAIAgent(jackal_api_url, coingecko_api_url, llama_api_key)
    await telegram_agent.initialize()
    
    # Add handlers
    application.add_handler(CommandHandler("start", telegram_agent.start_command))
    application.add_handler(CommandHandler("help", telegram_agent.help_command))
    application.add_handler(CommandHandler("price", telegram_agent.get_jkl_price))
    application.add_handler(CommandHandler("stats", telegram_agent.get_jackal_stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_agent.handle_message))
    
    # Add the new button callback handler
    application.add_handler(CallbackQueryHandler(telegram_agent.button_callback))

def main() -> None:
    # Set up the Telegram bot application
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No token found. Make sure TELEGRAM_BOT_TOKEN is set in your .env file.")
        return

    application = Application.builder().token(token).post_init(post_init).build()

    # Start the bot
    logger.info("Starting Jackal Protocol Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
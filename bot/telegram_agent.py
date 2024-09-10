import re
import logging
import asyncio
import ssl
import json
import difflib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
from datetime import datetime
from jackal_data_fetcher import JackalDataFetcher
from llama_client import LLaMAClient
from embedding_search import EmbeddingSearch
from dynamic_content_manager import DynamicContentManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractiveElements:
    @staticmethod
    def get_main_menu():
        keyboard = [
            [InlineKeyboardButton("🥩 Stake JKL", callback_data='stake_jkl')],
            [InlineKeyboardButton("📈 JKL Stats", callback_data='jkl_stats')],
            [InlineKeyboardButton("🎓 Jackal Tutorials", callback_data='jackal_tutorials')],
            [InlineKeyboardButton("💱 Buy JKL", callback_data='buy_jkl')],
            [InlineKeyboardButton("💰 JKL Price", callback_data='jkl_price')]
        ]
        return InlineKeyboardMarkup(keyboard)

class TelegramAIAgent:
    def __init__(self, jackal_api_url, coingecko_api_url, llama_api_key):
        self.jackal_api_url = jackal_api_url
        self.coingecko_api_url = coingecko_api_url
        self.jackal_data_fetcher = JackalDataFetcher(self.jackal_api_url)
        self.llama_client = LLaMAClient(llama_api_key)
        self.knowledge_base = self.load_knowledge_base('knowledge_base.json')
        self.embedding_search = EmbeddingSearch(self.knowledge_base)
        self.dynamic_content = DynamicContentManager()
        self.greeting_patterns = [
            r'\b(hi|hello|hey|greetings|howdy|hola|ciao|salut)\b',
            r'good\s+(morning|afternoon|evening|day)',
            r'what\'s up',
            r'how are you'
        ]
        self.interactive_elements = InteractiveElements()

    async def initialize(self):
        await self.initialize_dynamic_content()
        asyncio.create_task(self.dynamic_content.run_updates())

    def load_knowledge_base(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return []

    async def initialize_dynamic_content(self):
        await self.dynamic_content.add_content('validators', self.fetch_validators, 600)  # Update every 10 minutes
        await self.dynamic_content.add_content('governance_proposals', self.fetch_governance_proposals, 600)  # Update every 10 minutes

    async def fetch_validators(self):
        return await self.jackal_data_fetcher.get_validator_set()

    async def fetch_governance_proposals(self):
        return await self.jackal_data_fetcher.get_governance_proposals()

    def is_greeting(self, message):
        return any(re.search(pattern, message.lower()) for pattern in self.greeting_patterns)

    async def handle_greeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        greeting_response = f"Hello {user.first_name}! How can I assist you with Jackal Protocol today?"
        formatted_response = await self.llama_client.generate_jackal_response(greeting_response)
        await update.message.reply_text(formatted_response)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome_message = (
            f"Hello {user.mention_html()}! Welcome to the Jackal Protocol AI Community Manager Bot. "
            "I'm here to help you with information about Jackal Protocol. Here are some things I can do:\n\n"
            "• Get the current JKL price\n"
            "• Provide Jackal Protocol network statistics\n"
            "• Answer questions about Jackal Protocol\n\n"
            "Use /help to see all available commands. How can I assist you today?"
        )
        formatted_response = await self.llama_client.generate_jackal_response(welcome_message)
        await update.message.reply_html(formatted_response, reply_markup=self.interactive_elements.get_main_menu())

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_message = (
            "Here are the available commands:\n\n"
            "/start - Start the bot and get a welcome message\n"
            "/help - Show this help message\n"
            "/price - Get the current JKL price\n"
            "/stats - Show Jackal Protocol network statistics\n\n"
            "You can also ask me questions about Jackal Protocol!"
        )
        formatted_response = await self.llama_client.generate_jackal_response(help_message)
        await update.message.reply_text(formatted_response, reply_markup=self.interactive_elements.get_main_menu())

    async def get_jkl_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message=False):
        params = {
            "ids": "jackal-protocol",
            "vs_currencies": "usd"
        }
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession() as session:
                async with session.get(self.coingecko_api_url, params=params, ssl=ssl_context) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data["jackal-protocol"]["usd"]
                        response = f"The current price of JKL is ${price:.4f} USD."
                        formatted_response = await self.llama_client.generate_jackal_response(response)
                        if edit_message:
                            await update.callback_query.edit_message_text(formatted_response)
                        else:
                            await update.message.reply_text(formatted_response)
                    else:
                        error_message = "Sorry, I couldn't fetch the JKL price at the moment. Please try again later."
                        if edit_message:
                            await update.callback_query.edit_message_text(error_message)
                        else:
                            await update.message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Error fetching JKL price: {e}")
            error_message = "An error occurred while fetching the JKL price. Please try again later."
            if edit_message:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def get_jackal_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message=False):
        try:
            # Fetch real-time data
            latest_block = await self.jackal_data_fetcher.get_latest_block()
            previous_block = await self.jackal_data_fetcher.get_block(latest_block['height'] - 1)

            # Get cached data
            validators = await self.dynamic_content.get_content('validators')
            active_proposals = await self.dynamic_content.get_content('governance_proposals')

            if latest_block and previous_block:
                latest_time = datetime.fromisoformat(latest_block['time'].replace('Z', '+00:00'))
                previous_time = datetime.fromisoformat(previous_block['time'].replace('Z', '+00:00'))
                block_time = (latest_time - previous_time).total_seconds()

                stats_message = (
                    "Jackal Protocol Network Stats:\n\n"
                    f"Latest Block Height: {latest_block['height']}\n"
                    f"Block Time: {block_time:.2f} seconds\n"
                    f"Active Validators: {len(validators)}\n"
                    f"Active Proposals: {len([p for p in active_proposals if p['status'] == 'PROPOSAL_STATUS_VOTING_PERIOD'])}\n"
                )
                formatted_response = await self.llama_client.generate_jackal_response(stats_message)
                if edit_message:
                    await update.callback_query.edit_message_text(formatted_response)
                else:
                    await update.message.reply_text(formatted_response)
            else:
                error_message = "Sorry, I couldn't fetch the complete Jackal Protocol stats at the moment. Please try again later."
                if edit_message:
                    await update.callback_query.edit_message_text(error_message)
                else:
                    await update.message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Error fetching Jackal Protocol stats: {e}")
            error_message = "An error occurred while fetching Jackal Protocol stats. Please try again later."
            if edit_message:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text

        if user_message == '/start' or user_message.lower() == 'menu':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Welcome to the Jackal Protocol Bot! What would you like to know about JKL token?",
                reply_markup=self.interactive_elements.get_main_menu()
            )
            return

        if self.is_greeting(user_message):
            await self.handle_greeting(update, context)
            return

        user_message_lower = user_message.lower()
        if "price" in user_message_lower and "jkl" in user_message_lower:
            await self.get_jkl_price(update, context)
        elif "stats" in user_message_lower or "statistics" in user_message_lower:
            await self.get_jackal_stats(update, context)
        else:
            # Try embedding search first
            embedding_result = await self.embedding_search.search(user_message)
            if embedding_result:
                formatted_response = await self.llama_client.generate_jackal_response(embedding_result)
                await update.message.reply_text(formatted_response)
            else:
                # If no good match, use a generic response or direct to admin
                no_match_response = (
                    "I'm sorry, but I don't have a specific answer to your question. "
                    "For detailed information about Jackal Protocol or comparisons with other systems, "
                    "I recommend checking the official Jackal documentation or asking an admin for more information. "
                    "Is there anything specific about Jackal's features you'd like to know more about?"
                )
                formatted_response = await self.llama_client.generate_jackal_response(no_match_response)
                await update.message.reply_text(formatted_response)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'stake_jkl':
            staking_info = await self.fetch_staking_instructions()
            await query.edit_message_text(text=f"Here's where you can stake your JKL tokens:\n\n{staking_info}")
        elif query.data == 'jkl_stats':
            await self.get_jackal_stats(update, context, edit_message=True)
        elif query.data == 'jackal_tutorials':
            tutorials = await self.fetch_jackal_tutorials()
            await query.edit_message_text(text=f"{tutorials}")
        elif query.data == 'buy_jkl':
            exchanges = await self.fetch_jkl_exchanges()
            await query.edit_message_text(text=f"You can buy JKL tokens on the following exchanges:\n\n{exchanges}")
        elif query.data == 'jkl_price':
            await self.get_jkl_price(update, context, edit_message=True)
        
        await query.edit_message_reply_markup(reply_markup=self.interactive_elements.get_main_menu())

    async def fetch_staking_instructions(self):
        return ("You can stake JKL tokens using the following platforms:\n"
                "1. https://jackal.omniflix.co/\n"
                "2. https://ping.pub/jackal")

    async def fetch_jackal_tutorials(self):
        return ("Jackal tutorials: "
                "https://youtube.com/playlist?list=PL8uYUtY_DQ7VfhYZixXuCPC3_QurkYOlk&si=3ptyGfRLZcisdwWw")

    async def fetch_jkl_exchanges(self):
        # Placeholder implementation
        return ("You can buy JKL tokens on the following exchanges:\n"
                "1. Exchange A\n"
                "2. Exchange B\n"
                "3. Exchange C\n"
                "Please check the official Jackal Protocol website for the most up-to-date list of supported exchanges.")
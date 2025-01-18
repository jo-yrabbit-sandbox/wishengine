# src/bot.py
import asyncio
import os
import requests
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from api_client import MessageAPIClient
from parser import Parser
from states import BotStates

load_dotenv()

# Configure logging
MY_BOT_NAME='wishengine'
log_level = os.getenv('LOG_LEVEL', 'INFO')
DEBUG=(log_level.upper() == 'DEBUG')
numeric_level = getattr(logging, log_level.upper(), logging.INFO)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=numeric_level
)
logger = logging.getLogger(MY_BOT_NAME)

# API configuration from environment
API_ENDPOINT = os.getenv('API_ENDPOINT', 'http://localhost')
api = MessageAPIClient(MY_BOT_NAME, API_ENDPOINT)

async def health_check():
    """Check bot's health and API connection."""
    try:
        api_url = f'{API_ENDPOINT}/health'
        logger.info(f'Checking API health at: {api_url}')
        
        response = requests.get(api_url, timeout=5)
        logger.info(f'API Response: {response.status_code} - {response.text}')
        api_status = response.status_code == 200
        
        result = {
            'status': 'healthy',
            'api_connected': api_status,
            'api_endpoint': API_ENDPOINT,
            'api_status_code': response.status_code,
            'api_response': response.text
        }
        logger.info(f'Health check result: {result}')
        return result
    except Exception as e:
        logging.error(f'Health check failed: {str(e)}')
        return {
            'status': 'unhealthy',
            'error': str(e),
            'api_endpoint': API_ENDPOINT
        }

# Docker healthcheck
from aiohttp import web
async def handle_health(request):
    health = await health_check()
    status = 200 if health['status'] == 'healthy' else 500
    return web.json_response(health, status=status)

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(f'Hello! I am your test bot. My name is {MY_BOT_NAME}')

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /ping is issued."""
    health = await health_check()
    await update.message.reply_text('pong! connection to server is {}'.format(health['status']))

async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show last messages in server when the command /fetch is issued."""
    messages_yes = api.get_messages({'limit': 1, 'state': BotStates.POSITIVE.value})
    messages_no  = api.get_messages({'limit': 1, 'state': BotStates.NEGATIVE.value})
    messages_list = [(BotStates.POSITIVE.value, messages_yes),
                     (BotStates.NEGATIVE.value, messages_no)]
    if not messages_list:
        await update.message.reply_text(f'No messages found from me ({MY_BOT_NAME})')
        return

    print_me = []
    for state, messages in messages_list:
        for i,m in enumerate(messages):
            if (type(m) is dict) and ('text' in m.keys()):
                print_me.append('[{}] {}'.format(state, m['text']))
            else:
                logger.error(f'Skipping message_{state}_{i} due to invalid format: {str(m)}')

    lines = [f'Message #{i}:\n{m}' for i,m in enumerate(print_me)]
    await update.message.reply_text('\n\n'.join(lines))

async def answer_if_user_responds_to_claude(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detect if is reply to text chat"""
    message = update.message
    if not message:
        logger.debug('Ignoring latest message due to no content')
        return
    # Check if message is a reply
    if not message.reply_to_message:
        logger.debug(f'Ignoring latest message due to not a reply \'{message.text}\'')
        return

    # Access the original message that was replied to
    prompt = message.reply_to_message.text
    logger.debug(f'Latest message was a reply to prompt \'{prompt}\'')

    # Process it
    p = Parser(debug=DEBUG, logger=logger)
    p.process(prompt, message.text)

    # Respond
    response = p.get_text()
    if not response:
        logger.debug(f'Doing nothing. Response was not generated for user input \'{message.text}\'')

    # Finally, respond to user:
    await update.message.reply_text(response)

    # Store response
    state = str(p.get_state())
    text_clean = p.get_text_clean()
    target = f'[{state}]: {text_clean}'
    try:
        status = api.store_message(text_clean, state)
        if not status:
            raise Exception('POST request to store {} did not return valid status'.format(target))
        logger.info(f'Storage of {target} returned {status=}')
    except Exception as e:
        logger.error('Failed to store {} - {}'.format(target, e.args[0]))

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message

/ping - Check if bot is connected to server
/fetch - Show last messages in server
    """
    await update.message.reply_text(help_text)


def main():
    """Start the bot"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logging.error('No TELEGRAM_TOKEN provided')
        return

    # Create application
    application = Application.builder().token(token).build()

    # Add command handlers (starts with /your-command)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('ping', ping))
    application.add_handler(CommandHandler('fetch', fetch))

    # Handle non commands (e.g. messages from user) - answer in Telegram with parsed response
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_if_user_responds_to_claude))

    # Start health check server
    app = web.Application()
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)

    async def start_health_server():
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()

    # Run both the bot and health server
    asyncio.get_event_loop().run_until_complete(start_health_server())
    application.run_polling()

if __name__ == '__main__':
    main()

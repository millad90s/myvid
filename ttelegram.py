from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from dotenv import load_dotenv
import threading
import os
import logging
from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    CallbackContext,
    PollAnswerHandler,
    PollHandler
)
from datetime import datetime
from functools import wraps
# from handlers.admin_commands  import  ( start_handler,
#                                     help_handler,
#                                     admin_broadcast_message,
#                                     admin_list_users,
#                                     german_words
#                                 )

# Lock to prevent multiple downloads
download_lock = threading.Lock()

keyboards = {
    'menu': [
        [
            InlineKeyboardButton("Bind Subtitle to Video", callback_data='bind_subtitle'),
        ],
        [
            InlineKeyboardButton("Extract Subtitle & translate", callback_data='extract_subtitle'),
        ],
        [
            InlineKeyboardButton("Level Test", callback_data='level_test'),
        ]
    ]
}
# Define a list of poll questions
POLL_QUESTIONS = [
    {"question": "Select a font size for your subtitles:", "options": ["10", "11", "12"], "explanation": "Select a font size for your subtitles:"},
    {"question": "Select a font color for your subtitles:", "options": ["White", "Yellow", "Black"], "explanation": "Select a font color for your subtitles:"},
    {"question": "Select a background color for your subtitles:", "options": ["Black", "Transparent", "White"], "explanation": "Select a background color for your subtitles:"},
]



async def help_handler(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="""
                                   /start - Start the bot
                                   /whoami - Admin information
                                   /reels - Download reels from instagram
                                   """)
async def start_handler(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Telegram bot!")


    
async def whoami(update: Update, context: CallbackContext):
    admins = os.getenv('ADMIN_ID')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'admins are: {admins}, and you are {update.effective_chat.id}')
    print(update)
    print(admins)


### for all polls in POLL_QUESTIONS send them to user
async def send_poll(update: Update, context: CallbackContext):
    for q in POLL_QUESTIONS:
        message =  await context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=q["question"],
            options=q["options"],
            is_anonymous=False,
            explanation=q["explanation"],
            explanation_parse_mode="Markdown",
        )
        payload = {
            message.poll.id: {
                "questions": q,
                "message_id": message.message_id,
                "chat_id": update.effective_chat.id,
                "answers": 0,
            }
        }
        context.bot_data.update(payload)
        
    # Set state so the bot knows the user is expected to answer the poll
    context.user_data['waiting_for_poll'] = True

### save each poll's ansswer into context 
async def handle_poll_answer(update: Update, context: CallbackContext):
    answer = update.poll_answer
    update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    options = questions["options"]
    answer_string = questions["options"][update.poll_answer.option_ids]

    await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])
        
def main():
    load_dotenv()
    
    ### setup logger
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )
    
    application = Application.builder().token(os.getenv('TELEGRAM_API_KEY')).build()  
    logging.debug("Starting bot...")

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("poll", send_poll))
    application.add_handler(PollAnswerHandler(handle_poll_answer))

    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == "__main__":
    main()
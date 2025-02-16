from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from utils import media
import threading
from utils import translation
import os
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    CallbackContext,
    PollAnswerHandler
)
import sqlite3
from datetime import datetime, timedelta
import json
import random, os
import logging
import urllib.request
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
    'main_keyboard': [
        [
            InlineKeyboardButton("⏱️", callback_data='Hello'),
            InlineKeyboardButton("⏱️", callback_data='A1.2'),
        ],
        [
            InlineKeyboardButton("⏱️", callback_data='A2.1'),
            InlineKeyboardButton("A2.2", callback_data='A2.2'),
        ],
        [
            InlineKeyboardButton("Level Test", callback_data='level_test'),
        ]
    ]
}

def generate_filename(prefix="file", extension="txt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}"

def download_reels_instagram(url):
    media.download_insta_reel(url,"share-folder", "")

async def start_handler(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello World!")

async def get_insta_reels(update: Update, context: CallbackContext):
    url = update.message.text.split(" ")[-1]
    # get user name from message
    with download_lock:
        file_name = generate_filename()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="📺")
        media.download_insta_reel(url,"share-folder", str(file_name))
        ### send video to user
        await context.bot.send_video(chat_id=update.effective_chat.id, video="share-folder/output-"+file_name+".mp4")
        extracted_audio = media.extract_audio('share-folder/output-'+file_name+'.mp4')
        language, segments = media.transcribe(audio=extracted_audio)
        
        media.save_segments_to_srt(segments, "share-folder/transcription-"+file_name+".str")
        document1 = open("share-folder/transcription-"+file_name+".str", 'rb')
        await context.bot.send_document(chat_id=update.effective_chat.id, document=document1)
        
        translation.translate_srt("share-folder/transcription-"+file_name+".str", "share-folder/translated-"+file_name+".str")
    
        document2 = open("share-folder/translated-"+file_name+".str", 'rb')
        await context.bot.send_document(chat_id=update.effective_chat.id, document=document2)
    
        ### delete video from system 
        os.remove("share-folder/output-"+file_name+".mp4")
    
async def whoami(update: Update, context: CallbackContext):
    admins = os.getenv('ADMIN_ID')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'admins are: {admins}, and you are {update.effective_chat.id}')
    print(update)
    print(admins)
    
    
def main():
    load_dotenv()
    application = Application.builder().token(os.getenv('TELEGRAM_API_KEY')).build()  
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("reels", get_insta_reels))
    application.add_handler(CommandHandler("whoami", whoami))
    
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == "__main__":
    main()
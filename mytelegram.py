from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from dotenv import load_dotenv
from google import genai
from utils import media
import threading
import time 
import random
from utils import translation
import os
import logging
import asyncio
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

# Define file paths
DOWNLOADS_DIR = "downloads"  # Directory to save files
os.makedirs(DOWNLOADS_DIR, exist_ok=True)  # Ensure the directory exists
subtitle_path = ""
video_path = ""

def generate_filename(prefix="file", extension="txt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}"

def download_reels_instagram(url):
    media.download_insta_reel(url,"share-folder", "")

async def help_handler(update: Update, context: CallbackContext):
    help_text = """
    /start to start 
/reels ارسال ویدیو به همراه زیرنویس اصلی و دو ترحمه 
/whoami to identify
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)
                                   
async def start_handler(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Telegram bot!")

async def get_insta_reels(update: Update, context: CallbackContext):
    
    ### check user id , if it is admin then send reels
    admins = os.getenv('ADMIN_ID').split(",")
    logging.debug(f'admins are {admins}')
    logging.debug(f'user id is {update.effective_chat.id}')
    
    # if str(update.effective_chat.id) not in admins:
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text="you are not allowed 👮 ")
        # return
    url = update.message.text.split(" ")[-1]
    # get user name from message
    with download_lock:
        try: 
            file_name = generate_filename()
            
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📺")
            media.download_insta_reel(url,"share-folder", str(file_name))
            ### send video to user
            video_path = "share-folder/output-"+file_name+".mp4"
            origin_srt_path = "share-folder/transcription-"+file_name+".srt"
            ollama_srt_path = "share-folder/translated-"+file_name+".srt"
            gemeni_srt_path = "share-folder/Gemeni_translated-"+file_name+".srt"
            
            await context.bot.send_video(chat_id=update.effective_chat.id, video=video_path)
            extracted_audio = media.extract_audio(video_path)
            language, segments = media.transcribe(audio=extracted_audio)
            
            media.save_segments_to_srt(segments, origin_srt_path)
            document1 = open(origin_srt_path, 'rb')
            await context.bot.send_document(chat_id=update.effective_chat.id, document=document1)
            
            ### lets test gemeni :) 
            API_KEY = os.getenv('GEM_API_KEY')
            translation.gemeni_translator(API_KEY, origin_srt_path, gemeni_srt_path)
            document3 = open(gemeni_srt_path)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=document3 )
            
            translation.translate_srt(origin_srt_path, ollama_srt_path)
        
            document2 = open(ollama_srt_path, 'rb')
            await context.bot.send_document(chat_id=update.effective_chat.id, document=document2)
        


            ### delete video from system 
            os.remove("share-folder/output-"+file_name+".mp4")
        except:
            logging.debug("errorrr")
        # finally:
        #     os.remove("temprarily files")
    
async def whoami(update: Update, context: CallbackContext):
    admins = os.getenv('ADMIN_ID')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'admins are: {admins}, and you are {update.effective_chat.id}')
    print(update)
    print(admins)
async def receive_video(update: Update, context: CallbackContext):
    """Handles receiving and downloading a video file from Telegram."""
    
    if context.user_data.get('waiting_for_video'):
        video = update.message.video or update.message.document  # Handle both video & document
        if video:
            file_id = video.file_id
            file_name = f"{file_id}.mp4"  # Assign a unique filename
            video_path = os.path.join(DOWNLOADS_DIR, file_name)

            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text=f"✅ Video received! Downloading...")

            # Download the video to local storage
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(video_path)

            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text=f"🎬 Video saved as `{video_path}`.")

            # Store the video path
            context.user_data['waiting_for_video'] = False
            context.user_data['video_path'] = video_path  

            # Check if subtitles are already uploaded
            if context.user_data.get('subtitle_path'):
                await bind_subtitle_to_video(update, context)

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text="❌ Please send a valid video file.")




async def receive_srt(update: Update, context: CallbackContext):
    """Handle the received SRT subtitle file."""
    if context.user_data.get('waiting_for_srt'):
        document = update.message.document
        if document and document.file_name.endswith(('.srt', '.ass')):
            file_id = document.file_id
            subtitle_path = os.path.join(DOWNLOADS_DIR, document.file_name)

            # Download the subtitle file to local storage
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(subtitle_path)

            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text=f"✅ Subtitle file received and saved as `{subtitle_path}`.")

            # Store the subtitle path and reset state
            context.user_data['waiting_for_srt'] = False
            context.user_data['subtitle_path'] = subtitle_path  
            
            # Check if a video is also available
            if context.user_data.get('video_path'):
                await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text=f"✅ Lest bind subtitle to video" )
                await bind_subtitle_to_video(update, context)

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text="Please upload a valid .srt subtitle file.")

def generate_name(prefix="file"):
    """Generate a unique name using the current timestamp and a random number."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    random_number = random.randint(1000, 9999)  # 4-digit random number
    return f"{prefix}_{timestamp}_{random_number}"

async def bind_subtitle_to_video(update: Update, context: CallbackContext):
    """
    Asynchronously binds a subtitle to a video and sends the processed video.
    """
    video_path = context.user_data.get('video_path')
    subtitle_path = context.user_data.get('subtitle_path')
    output_video = os.path.join(DOWNLOADS_DIR, generate_name("video")+".mp4")

    if not video_path or not subtitle_path:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Missing video or subtitle file!")
        return
    
    async with asyncio.Lock():  # Prevent multiple users from running at the same time
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⏳ Processing video...")

            # Run your existing function asynchronously
            await asyncio.to_thread(media.embed_subtitles_ffmpeg, video_path, output_video, subtitle_path)

            # Send the processed video back to the user
            await context.bot.send_video(chat_id=update.effective_chat.id, video=open(output_video, 'rb'))

        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error processing video: {str(e)}")

        finally:
            # Clean up temporary files
            if os.path.exists(output_video):
                os.remove(output_video)
            if os.path.exists(video_path):
                os.remove(video_path)  # Remove video after processing
            if os.path.exists(subtitle_path):
                os.remove(subtitle_path)  # Remove subtitle after processing

            # Reset user data to avoid conflicts
            context.user_data.pop('video_path', None)
            context.user_data.pop('subtitle_path', None)
            
async def add_sub_command(update: Update, context: CallbackContext):
    """Handles the /addsub command and asks the user for a video and subtitle."""
    context.user_data['waiting_for_video'] = True
    context.user_data['waiting_for_srt'] = True
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🎬 Please upload the video file first.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Then, upload the subtitle (.srt) file.")


def main():
    load_dotenv()
    # Read logging settings from environment variables
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()  # Default to INFO
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    
  # Set up logger
    logging.basicConfig(
        format=log_format,
        level=getattr(logging, log_level, logging.INFO)  # Convert string level to logging constant
    )
    application = Application.builder().token(os.getenv('TELEGRAM_API_KEY')).build()  
    logging.debug("Starting bot...")

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("reels", get_insta_reels))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("addsub", add_sub_command))
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video))
    application.add_handler(MessageHandler(filters.Document.ALL, receive_srt))

    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == "__main__":
    main()
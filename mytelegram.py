from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from dotenv import load_dotenv
from collections import deque
from google import genai
from utils import media
from utils.database import DatabaseManager
import threading
import time 
import random
from utils import translation
import os
import shutil
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
queue = deque()

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
user_subtitle_settings = {}
 ### Initialize database
db = DatabaseManager()

def is_within_working_hours() -> tuple[bool, str]:
    """Check if current time is within working hours and return status with time info"""
    # Get working hours from .env
    working_hours = os.getenv("WORKING_HOURS", "08:00 21:00")
    try:
        start_time, end_time = working_hours.split(" ")
        
        # Handle edge case where end_time is 24:00
        if end_time == "24:00":
            end_time = "23:59"
        
        # Convert to datetime objects
        now = datetime.now()
        current_time = now.time()
        
        try:
            start_time = datetime.strptime(start_time, "%H:%M").time()
            end_time = datetime.strptime(end_time, "%H:%M").time()
        except ValueError as e:
            logging.error(f"Invalid time format in WORKING_HOURS: {e}")
            # Default to 8 AM - 9 PM if there's an error
            start_time = datetime.strptime("08:00", "%H:%M").time()
            end_time = datetime.strptime("21:00", "%H:%M").time()

        # Format time info
        time_info = (
            f"🕒 Server Time: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"⏰ Working Hours: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        )

        # Check if current time is within working hours
        is_working = start_time <= current_time <= end_time
        return is_working, time_info
        
    except Exception as e:
        logging.error(f"Error in working hours check: {e}")
        # Return a safe default if there's any error
        now = datetime.now()
        time_info = (
            f"🕒 Server Time: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"⏰ Working Hours: 08:00 - 21:00 (default)"
        )
        return False, time_info

### check if user's request is in working hours
def check_working_hours():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    return current_time in working_hours

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
    if not is_within_working_hours()[0]:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Vidio Editor is not available outside working hours.")
        return
    
    ### check user id , if it is admin then send reels
    admins = os.getenv('ADMIN_ID').split(",")
    logging.debug(f'admins are {admins}')
    logging.debug(f'user id is {update.effective_chat.id}')

    url = update.message.text.split(" ")[-1]

    ### add user's request into database
    db.log_command(
        user_id=update.effective_user.id,
        command="reels",
        user_name=update.effective_user.username  # Optional
    )
    ### return if url is not start with instagram reels 
    if not url.startswith("https://www.instagram.com/reel"):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🙅‍♂️ url is not instagram reels")
        return
    try:
        queue.append(f'{ update.effective_chat.id},{ update.message.text.split(" ")[0]},{ update.message.text.split(" ")[-1]}')
        queue_size = len(queue)
        print(f"Queue size: {queue_size}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"# Jobs in the queue: {queue_size}")
        # file_name = generate_filename()
        
        # await context.bot.send_message(chat_id=update.effective_chat.id, text="📺")
        # media.download_insta_reel(url,"share-folder", str(file_name))
        # ### send video to user
        # video_path = "share-folder/output-"+file_name+".mp4"
        # origin_srt_path = "share-folder/transcription-"+file_name+".srt"
        # ollama_srt_path = "share-folder/translated-"+file_name+".srt"
        # gemeni_srt_path = "share-folder/Gemeni_translated-"+file_name+".srt"
        # gemeni_txt_path = "share-folder/Gemeni_translated-"+file_name+".txt"
        
        
        # await context.bot.send_video(chat_id=update.effective_chat.id, video=video_path)
        # extracted_audio = media.extract_audio(video_path)
        # language, segments = media.transcribe(audio=extracted_audio)
        
        # media.save_segments_to_srt(segments, origin_srt_path)
        # document1 = open(origin_srt_path, 'rb')
        # await context.bot.send_document(chat_id=update.effective_chat.id, document=document1)
        
        # ### lets test gemeni :) 
        # API_KEY = os.getenv('GEM_API_KEY')
        # translation.gemeni_translator(API_KEY, origin_srt_path, gemeni_srt_path)
        # document3 = open(gemeni_srt_path)
        # # Read the contents
        # # content = document3.read()
        # await context.bot.send_document(chat_id=update.effective_chat.id, document=document3 )
        # # document3.close()
        
        # # copy strt to txt file 
        # shutil.copyfile(gemeni_srt_path, gemeni_txt_path)
        # # with open(txt_path, "w", encoding="utf-8") as txt_file:
        # #     txt_file.write(content.decode("utf-8"))
        # await context.bot.send_document(chat_id=update.effective_chat.id, document=gemeni_txt_path )
        # # translation.translate_srt(origin_srt_path, ollama_srt_path)
    
        # ### delete video from system 
        # remove_file_if_exists(video_path)
        # remove_file_if_exists(origin_srt_path)
        # remove_file_if_exists(ollama_srt_path)
        # remove_file_if_exists(gemeni_srt_path)
        # remove_file_if_exists(gemeni_txt_path)
        
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error processing video: {str(e)}")
    # finally:
    #     os.remove("temprarily files")
    
async def whoami(update: Update, context: CallbackContext):
    admins = os.getenv('ADMIN_ID')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'admins are: {admins}, and you are {update.effective_chat.id}')
    print(update)
    print(admins)
async def receive_video(update: Update, context: CallbackContext):
    """Handles receiving and downloading a video file from Telegram."""

    logging.info(context.user_data)
    logging.info(context.user_data)
    if context.user_data.get('waiting_for_video'):
        video = update.message.video or update.message.document  # Handle both video & document
        if video:
            file_id = video.file_id
            print("((((((((((()))))))))))")
            print(file_id)
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



async def set_subtitle(update: Update, context: CallbackContext):
  # Ensure subtitle_setting dictionary exists
    if "subtitle_setting" not in context.user_data:
        context.user_data["subtitle_setting"] = {}  # Initialize empty dictionary
    
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text="Please enter FontSize ?")

async def set_font_size(update: Update, context: CallbackContext):
    # Ensure subtitle_setting dictionary exists
    if "subtitle_setting" not in context.user_data:
        context.user_data["subtitle_setting"] = {}  # Initialize empty dictionary
    
    font_size = update.message.text
    context.user_data["subtitle_setting"]["fontsize"] = font_size
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=f"✅ FontSize set to {font_size}")

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
            
            logging.info(context.user_data.get('subtitle_setting'))
            # Run your existing function asynchronously
            await asyncio.to_thread(media.embed_subtitles_ffmpeg, video_path, output_video, subtitle_path, context.user_data.get('subtitle_setting'))

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
    if not is_within_working_hours()[0]:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Subtitles are not available outside working hours.")
        return
    
    ### add user's request into database
    db.log_command(
        user_id=update.effective_user.id,
        command="addsub",
        user_name=update.effective_user.username  # Optional
    )
    
    """Handles the /addsub command and asks the user for a video and subtitle."""
    context.user_data['waiting_for_video'] = True
    context.user_data['waiting_for_srt'] = True
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🎬 Please upload the video file first.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Then, upload the subtitle (.srt) file.")

    # Ensure subtitle_setting exists in user_data
    if "subtitle_setting" not in context.user_data:
        context.user_data["subtitle_setting"] = {}  # Initialize empty dictionary



### poll subtitle position 
async def send_subtitle_position_poll(update: Update, context: CallbackContext):
    """
    Sends a poll to ask the user for their preferred subtitle position.
    """
    # Ensure subtitle_setting dictionary exists
    if "subtitle_setting" not in context.user_data:
        context.user_data["subtitle_setting"] = {}  # Initialize empty dictionary
        
    question = "Where do you want the subtitles to appear?"
    options = ["1/7(30)", "2/7(55)", "3/7(85)", "4/7(120)", "5/7(155)", "6/7(190)", "7/7(230)"]

    ### add user's request into database
    db.log_command(
        user_id=update.effective_user.id,
        command="setposition",
        user_name=update.effective_user.username  # Optional
    )
    # Send the poll
    message = await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=options[::-1],
        is_anonymous=False
    )
    
    # # Store poll message ID and chat ID to track answers
    # context.chat_data["poll_id"] = message.poll.id
    # context.chat_data["poll_message_id"] = message.message_id
    # context.chat_data["chat_id"] = update.effective_chat.id

### show user's subtitle position
async def show_subtitle_position(update: Update, context: CallbackContext):
    ### check if subtitle position is set
    if "subtitle_setting" not in context.user_data:
        context.user_data["subtitle_setting"] = {}  # Initialize empty dictionary
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your subtitle position is: bottom')
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your subtitle position is: {context.user_data["subtitle_setting"]["marginv"]}')
    
### handle subtitle position poll 
async def handle_poll_answer(update: Update, context: CallbackContext):
    """
    Handles the user's answer from the poll and updates the subtitle position setting.
    """
    poll_answer = update.poll_answer
    user_id = poll_answer.user.id
    selected_option = poll_answer.option_ids[0]  # Get the index of the selected option
    

    # Map poll options to subtitle alignment codes
    position_mapping = {
        0: "230",
        1: "190",
        2: "155",         # At the top
        3: "120",         # At the top
        4: "85",      # Slightly below top
        5: "55",  # Slightly above bottom
        6: "30",      # Default bottom center
    }
    
    selected_position = position_mapping.get(selected_option, "30")  # Default to "bottom"

    context.user_data["subtitle_setting"]["marginv"] = selected_position
    print(context.user_data)


    # Store the user's choice
    context.user_data['subtitle_position'] = selected_option

    # Send confirmation message
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ Subtitle position set to: {selected_position} above bottom!"
    )
async def add_queue(update: Update, context: CallbackContext):
    text = f'{update.effective_chat.id},{update.message.text.split(" ")[0]},{update.message.text.split(" ")[1]}'
    logging.debug(text)
    queue.append(text)
    
async def background_task(app: Application):
    """یک تسک پس‌زمینه‌ای که هر ۱۰ ثانیه یک پیام ارسال می‌کند."""
    while True:
        # print("📢 پیام خودکار از سمت بات!")
        await asyncio.sleep(10)  # هر ۱۰ ثانیه اجرا شود
        # chat_id = 2140876637  # آیدی چت مورد نظر (تغییر دهید)
        # await app.bot.send_message(chat_id, "📢 پیام خودکار از سمت بکگراند تسک!")
    
        #### bring /reels here 
        # admins = os.getenv('ADMIN_ID').split(",")
        # logging.debug(f'admins are {admins}')
        # logging.debug(f'user id is {update.effective_chat.id}')
        
        # if str(update.effective_chat.id) not in admins:
        #     await context.bot.send_message(chat_id=update.effective_chat.id, text="you are not allowed 👮 ")
            # return
            # get user name from message
            # with download_lock:
        try: 
            if queue:
                msg = queue.popleft()
                chat_id = msg.split(",")[0]
                command = msg.split(",")[1]
                url = msg.split(",")[2]

                await app.bot.send_message(chat_id, msg)
                file_name = generate_filename()
                
                await app.bot.send_message(chat_id=chat_id, text="📺")
                media.download_insta_reel(url,"share-folder", str(file_name))
                ### send video to user
                video_path = "share-folder/output-"+file_name+".mp4"
                origin_srt_path = "share-folder/transcription-"+file_name+".srt"
                ollama_srt_path = "share-folder/translated-"+file_name+".srt"
                gemeni_srt_path = "share-folder/Gemeni_translated-"+file_name+".srt"
                gemeni_txt_path = "share-folder/Gemeni_translated-"+file_name+".txt"
                
                
                await app.bot.send_video(chat_id=chat_id, video=video_path)
                extracted_audio = media.extract_audio(video_path)
                language, segments = media.transcribe(audio=extracted_audio)
                
                media.save_segments_to_srt(segments, origin_srt_path)
                document1 = open(origin_srt_path, 'rb')
                await app.bot.send_document(chat_id=chat_id, document=document1)
                
                ### lets test gemeni :) 
                API_KEY = os.getenv('GEM_API_KEY')
                translation.gemeni_translator(API_KEY, origin_srt_path, gemeni_srt_path)
                document3 = open(gemeni_srt_path)
                # Read the contents
                # content = document3.read()
                await app.bot.send_document(chat_id=chat_id, document=document3 )
                # document3.close()
                
                # copy strt to txt file 
                shutil.copyfile(gemeni_srt_path, gemeni_txt_path)
                # with open(txt_path, "w", encoding="utf-8") as txt_file:
                #     txt_file.write(content.decode("utf-8"))
                await app.bot.send_document(chat_id=chat_id, document=gemeni_txt_path )
                # translation.translate_srt(origin_srt_path, ollama_srt_path)
            
                ### delete video from system 
                media.remove_file_if_exists(video_path)
                media.remove_file_if_exists(origin_srt_path)
                media.remove_file_if_exists(ollama_srt_path)
                media.remove_file_if_exists(gemeni_srt_path)
                media.remove_file_if_exists(gemeni_txt_path)
        except Exception as e:
            await app.bot.send_message(chat_id=chat_id, text=f"❌ Error processing video: {str(e)}")
            media.remove_file_if_exists(video_path)
            media.remove_file_if_exists(origin_srt_path)
            media.remove_file_if_exists(ollama_srt_path)
            media.remove_file_if_exists(gemeni_srt_path)
            media.remove_file_if_exists(gemeni_txt_path)
            logging.error(f"Error processing video: {str(e)}")
        finally:
            queue_size = len(queue)
            print(f"Queue size: {queue_size}")
            

async def show_report(update: Update, context: CallbackContext):
    """Return user command statistics and history"""
    user_id = update.effective_user.id
    try:
        # Check if user is admin
        admins = os.getenv('ADMIN_ID', '').split(',')
        is_admin = str(user_id) in admins

        # Parse command arguments
        args = context.args[0] if context.args else "user"
        
        if is_admin:
            if args == "time":
                # Show time-based statistics
                report = db.format_time_report()
            elif args == "all":
                # Show all users history (default 7 days)
                days = 7
                if len(context.args) > 1 and context.args[1].isdigit():
                    days = int(context.args[1])
                report = db.get_all_users_history(days=days)
            elif args == "global":
                # Show global usage statistics
                report = db.format_global_report()
            else:
                # Show individual user report
                report = db.format_user_report(user_id)
        else:
            # Non-admin users can only see their own stats
            report = db.format_user_report(user_id)
        
        # Split long reports into multiple messages if needed
        if len(report) > 4000:
            for i in range(0, len(report), 4000):
                chunk = report[i:i + 4000]
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=chunk
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=report
            )
            
        if is_admin:
            # Show available report options to admins
            help_text = """
Available report types:
/show_report - Show your usage
/show_report time - Show time-based statistics
/show_report all [days] - Show all users history (optional: specify number of days)
/show_report global - Show global usage statistics
"""
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=help_text
            )
            
    except Exception as e:
        error_msg = f"Error generating report: {str(e)}"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=error_msg
        )
        logging.error(error_msg)
            
async def on_startup(app: Application):
    """این تابع هنگام اجرای بات اجرا می‌شود."""
    asyncio.create_task(background_task(app))  # اجرای تسک پس‌زمینه
async def show_queue(update: Update, context: CallbackContext):
    queue_size = len(queue)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Queue size: {queue_size}")
    
async def broadcast(update: Update, context: CallbackContext):
    """Send a broadcast message to all users (admin only)"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    admins = os.getenv('ADMIN_ID', '').split(',')
    if str(user_id) not in admins:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ This command is only available to administrators."
        )
        return

    # Check working hours
    is_working, time_info = is_within_working_hours()
    if not is_working:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Broadcasting is not available outside working hours.\n\n{time_info}"
        )
        return

    # Check if there's a message to broadcast
    if not context.args:
        help_text = f"""
📢 Broadcast Usage:
{time_info}

1. Simple Text:
   /broadcast Your message here
   
2. With Markdown:
   /broadcast -m *bold* _italic_ `code` text
   
3. Forward a message:
   Reply to any message with: /broadcast -f

Example:
/broadcast -m *Important Update*
Dear users,
The bot will be under maintenance from _10:00_ to `12:00` UTC.
"""
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_text,
            parse_mode='Markdown'
        )
        return

    # Check if it's a forward request
    if context.args[0] == '-f' and update.message.reply_to_message:
        message_to_forward = update.message.reply_to_message
        broadcast_type = 'forward'
    else:
        # Check if it's a markdown message
        if context.args[0] == '-m':
            broadcast_message = ' '.join(context.args[1:])
            parse_mode = 'Markdown'
        else:
            broadcast_message = ' '.join(context.args)
            parse_mode = None
        broadcast_type = 'message'

    users = db.get_all_users()
    success_count = 0
    fail_count = 0

    # Send status message with time info
    status_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🚀 Broadcasting message...\n{time_info}"
    )

    # Send to each user
    for user_id, username in users:
        try:
            if broadcast_type == 'forward':
                await message_to_forward.forward(user_id)
            else:
                # Add timestamp to broadcast message
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                timestamped_message = f"📢 Broadcast Message ({current_time}):\n\n{broadcast_message}"
                await context.bot.send_message(
                    chat_id=user_id,
                    text=timestamped_message,
                    parse_mode=parse_mode
                )
            success_count += 1
            if success_count % 5 == 0:  # Update status every 5 successful sends
                await status_message.edit_text(
                    f"🚀 Broadcasting...\n{time_info}\n"
                    f"Sent: {success_count}\nFailed: {fail_count}"
                )
            # Add small delay to avoid hitting rate limits
            await asyncio.sleep(0.1)
        except Exception as e:
            fail_count += 1
            logging.error(f"Failed to send broadcast to user {user_id}: {str(e)}")

    # Final status update with current time
    _, updated_time_info = is_within_working_hours()  # Get fresh time info
    await status_message.edit_text(
        f"✅ Broadcast completed!\n{updated_time_info}\n"
        f"Successfully sent: {success_count}\n"
        f"Failed: {fail_count}\n"
        f"Total users: {len(users)}"
    )

    # Log the broadcast command
    db.log_command(
        user_id=update.effective_user.id,
        command=f"broadcast",
        user_name=update.effective_user.username
    )

def main():
    
    load_dotenv()
    # Read logging settings from environment variables
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    
    # Set up logger
    logging.basicConfig(
        format=log_format,
        level=getattr(logging, log_level, logging.INFO)
    )
    application = Application.builder().token(os.getenv('TELEGRAM_API_KEY')).post_init(on_startup).build()
    logging.debug("Starting bot...")

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("reels", get_insta_reels))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("addsub", add_sub_command))
    application.add_handler(CommandHandler("subset", set_subtitle))
    application.add_handler(CommandHandler("add_q", add_queue))
    application.add_handler(CommandHandler("setposition", send_subtitle_position_poll))
    application.add_handler(CommandHandler("showposition", show_subtitle_position))
    application.add_handler(CommandHandler("setfontsize", set_font_size))
    application.add_handler(CommandHandler("show_q", show_queue))
    application.add_handler(CommandHandler("show_report", show_report))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(
        (filters.ChatType.GROUPS | filters.ChatType.PRIVATE) & (filters.VIDEO | filters.Document.VIDEO),
        receive_video
    ))

    
    application.add_handler(MessageHandler(filters.Document.ALL, receive_srt))

    application.add_handler(PollAnswerHandler(handle_poll_answer))

    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == "__main__":
    main()

import ffmpeg
from faster_whisper import WhisperModel
from datetime import timedelta
import yt_dlp
import gc
import pysubs2
import logging
import os


input_video = "output.mp4"
input_video_name = input_video.replace(".mp4", "").replace(" ", "_")

def download_insta_reel(url,folder="share-folder", prefix=""):
    options = {
        'outtmpl': f'{folder}/{input_video_name}-{prefix}.%(ext)s',  # Save with the title as filename
        'format': 'best',  # Best quality available
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
    
    print("Download complete!")
    
    
def extract_audio(input_video=input_video):
    print(f"Extracting audio from {input_video}")
    extracted_audio = f"audio-{input_video_name}.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio

def transcribe(audio):
    model = WhisperModel("small", compute_type="float32")
    try:
        segments, info = model.transcribe(audio)
        print(info)
        language = info
        print("Transcription language", info)
        print("New Version ....")
        segments = list(segments)
        for segment in segments:
            print(segment.start)
            print(segment.end)
            print("[%.2fs -> %.2fs] %s" %
                (segment.start, segment.end, segment.text))
        return language, segments
    finally:
        print("Cleaning up memory...")
        del model  # Delete model instance
        gc.collect()  # Force garbage collection

def seconds_to_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())  # Extract total whole seconds
    milliseconds = int((seconds - total_seconds) * 1000)  # Extract milliseconds

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def save_segments_to_srt(segments, output_file="output.srt"):
    """Save Whisper transcription segments to an SRT subtitle file."""
    with open(output_file, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, start=1):
            start_time = seconds_to_srt_time(segment.start)
            end_time = seconds_to_srt_time(segment.end)
            text = segment.text.strip()

            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

    print(f"✅ SRT file saved: {output_file}")



# def convert_srt_to_ass(srt_file, ass_file="styled_farsi_subtitles.ass"):
#     """
#     Convert an SRT file to an ASS file and apply Persian styling (black text, white background).
#     """
#     subs = pysubs2.load(srt_file, encoding="utf-8")

#     # Define Persian-friendly font style
#     subs.styles["FarsiStyle"] = pysubs2.Style(
#         fontname="B Nazanin",  # Use a Persian font (install it first)
#         fontsize=36,           # Adjust font size
#         primarycolor=pysubs2.Color(0, 0, 0, 255),  # Black text
#         backcolor=pysubs2.Color(255, 255, 255, 255),  # White background
#         alignment=pysubs2.Alignment.BOTTOM_CENTER,  # Centered subtitles
#         bold=True
#     )
#     subs.info["ScaledBorderAndShadow"] = "no"


#     # Apply the custom style to all subtitle lines
#     for line in subs:
#         line.style = "FarsiStyle"

#     # Save as ASS
#     subs.save(ass_file)
#     print(f"✅ Converted {srt_file} to {ass_file} with Persian styling.")
#     return subs

def convert_srt_to_ass(srt_file, ass_file="styled_farsi_subtitles.ass", subtitle_setting={}):
    """
    Convert an SRT file to an ASS file and apply Persian styling (black text, white background).
    """
    subs = pysubs2.load(srt_file, encoding="utf-8")

    print("subtitle_setting is:  ")
    logging.info(subtitle_setting)
    # Modify default subtitle style for Persian
    subs.styles["Default"].fontname = "B Titr"
    subs.styles["Default"].primarycolor = pysubs2.Color(0,0,0)  # White text
    subs.styles["Default"].backcolor = pysubs2.Color(255,255,255)  # black color
    subs.styles["Default"].outlinecolor = pysubs2.Color(255,255,255)  # black color
    
    # Set font size with explicit default handling
    # subs.styles["Default"].fontsize = 14  # Increase size for readability
    subs.styles["Default"].fontsize = subtitle_setting["fontsize"] if "fontsize" in subtitle_setting else 12  # Default: 16
    
    
    subs.styles["Default"].outline = 4  # No outline
    subs.styles["Default"].shadow = 0  # No shadow
    subs.styles["Default"].borderstyle = 4  # 3 = Boxed background
    subs.styles["Default"].marginl = 20  # Left margin
    subs.styles["Default"].marginr = 20  # Right margin
    # subs.styles["Default"].marginv = 20  # Bottom margin
    subs.styles["Default"].marginv =  subtitle_setting["marginv"] if "marginv" in subtitle_setting else 20  # Default: 20
    
    subs.styles["Default"].bold = True
    subs.info["ScaledBorderAndShadow"] = "no"

    # Save to ASS format
    subs.save(ass_file)

    print(f"✅ Converted {srt_file} to {ass_file} with Persian styling.")

### bind str to video 
def embed_subtitles_ffmpeg(video_file, output_file, subtitle_file="styled_farsi_subtitles.ass", subtitle_setting={}):
    """
    Embeds an .ass subtitle file into an .mp4 video using the ffmpeg library.

    Args:
        video_file (str): Path to the input video file.
        subtitle_file (str): Path to the .ass subtitle file.
        output_file (str): Path to the output video file.
    """
    ASS_file = "test2.ass"
    convert_srt_to_ass(subtitle_file,ASS_file, subtitle_setting)
    try:
        # Build and run the ffmpeg command
        (
            ffmpeg
            .input(video_file)
            .output(output_file, vf=f"subtitles={ASS_file}", vcodec="libx264", acodec="aac", crf=23, preset="medium")
            .run(overwrite_output=True)
        )
        print(f"Subtitled video saved as: {output_file}")
    except ffmpeg.Error as e:
        print("Error during processing:", e.stderr.decode())

# Function to remove file if it exists
def remove_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Removed: {file_path}")
    else:
        print(f"File not found: {file_path}")
        
def run():

    ### download instagram reels from url
    # instagram_reel_url = "https://www.instagram.com/reel/CwOalxUg06n/?igsh=bHd5eHQ0enZyNW9o"
    # extracted_audio = extract_audio()
    # language, segments = transcribe(audio=extracted_audio)
    
    # save_segments_to_srt(segments, "transcription.srt")
    convert_srt_to_ass("sub.srt", "styled_farsi_subtitles.ass")


if __name__ == "__main__":
    run()
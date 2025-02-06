import datetime
import ffmpeg
from faster_whisper import WhisperModel

input_video = "output.mp4"
input_video_name = input_video.replace(".mp4", "")


def extract_audio():
    extracted_audio = f"audio-{input_video_name}.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio

def transcribe(audio):
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    print(info)
    language = info
    print("Transcription language", info)
    segments = list(segments)
    for segment in segments:
        # print(segment)
        print("[%.2fs -> %.2fs] %s" %
              (segment.start, segment.end, segment.text))
    return language, segments

def seconds_to_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    return str(td)[:-3].replace(".", ",")

def save_segments_to_srt(segments, output_file="output.srt"):
    """Save Whisper transcription segments to an SRT subtitle file."""
    with open(output_file, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, start=1):
            start_time = seconds_to_srt_time(segment.start)
            end_time = seconds_to_srt_time(segment.end)
            text = segment.text.strip()

            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

    print(f"✅ SRT file saved: {output_file}")

def run():

    extracted_audio = extract_audio()
    language, segments = transcribe(audio=extracted_audio)
    save_segments_to_srt(segments, "transcription.srt")

run()
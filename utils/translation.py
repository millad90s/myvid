from ollama import Client
import re
from tqdm import tqdm
import os

from ollama import pull

my_ollama = Client(
  host='http://ollama:11434',
  headers={'x-some-header': 'some-value'}
)

### Pull the model
my_ollama.pull('gemma2')

def translate_text(text, model="gemma2"):
    print(f'text is {text}')
    """Translates English text to Persian"""
    prompt = (
        f"Translate the following text into Persian. "
        f"Provide only the translated text without any explanations, breakdowns, or additional context.\n\n"
        f"Text: \"{text}\"\nTranslation:"
    )
    response = my_ollama.chat(model=model, messages=[
        {'role': 'user', 'content': prompt
    }
    ])
    return response['message']['content']

def translate_srt(input_srt, output_srt, model="gemma2"):
    """Reads an SRT file, translates it, and writes to a new file."""
    print(input_srt)
    with open(input_srt, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    translated_srt = []
    subtitle_blocks = re.split(r'\n\n', srt_content)  # Split by empty lines

    for block in subtitle_blocks:
        lines = block.split('\n')
        if len(lines) < 2:
            continue  # Skip empty lines

        subtitle_index = lines[0]  # Subtitle number
        timestamp = lines[1]       # Time duration
        text = '\n'.join(lines[2:])  # Subtitle text
        print(text)

        translated_text = translate_text(text, model)
        print(translated_text)
        translated_srt.append(f"{subtitle_index}\n{timestamp}\n{translated_text}\n")

    with open(output_srt, 'w', encoding='utf-8') as file:
        file.write("\n\n".join(translated_srt))

    print(f"Translation complete! Saved to {output_srt}")

    return translated_srt

def main():
  translate_srt("transcription.srt", "translated_fa_gemma2.srt",model="gemma2")
  os.sleep(300)


if __name__ == "__main__":
  main()
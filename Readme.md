# Telegram Video and Subtitle Bot

This project is a Telegram bot that allows users to download Instagram reels, extract and transcribe audio, and manage subtitles with customizable settings.

## Features

- **Download Instagram Reels**: Users can download reels by providing a URL.
- **Audio Extraction and Transcription**: Extract audio from videos and transcribe it using Whisper.
- **Subtitle Management**: Convert SRT subtitles to ASS format with customizable styling.
- **User Commands**: Set subtitle font size and position via Telegram commands.

## Commands

- `/start`: Start interacting with the bot.
- `/setfontsize <size>`: Set the font size for subtitles.
- `/addsub`: Upload a video and subtitle file to bind them together.
- `/setposition`: Set the subtitle position via a poll.
- `/show_report`: Show user command statistics and history.
- `/show_queue`: Display the current size of the processing queue.
- `/broadcast`: Send a broadcast message to all users (admin only).

## Setup

1. **Create a Telegram Bot**: Use BotFather to create a bot and obtain an API token.
2. **Environment Variables**: Create a `.env` file with the following variables:
   - `TELEGRAM_API_KEY`: Your Telegram bot API key.
   - `ADMIN_ID`: Comma-separated list of admin user IDs.
   - `LOG_LEVEL`: Logging level (e.g., `DEBUG`).
   - `LOG_FORMAT`: Format for log messages.
   - `GEM_API_KEY`: API key for the Gemeni API.
   - `WORKING_HOURS`: Operational hours in `HH:MM HH:MM` format.

3. **Dependencies**: Install required Python packages using `pip install -r requirements.txt`.

## Running the Bot

### Locally

1. Start the bot by running the `mytelegram.py` script.
2. Interact with the bot using the commands listed above.

### Using Docker

1. **Build the Docker Image**:
   ```bash
   docker-compose build
   ```

2. **Run the Docker Container**:
   ```bash
   docker-compose up
   ```

3. **Stop the Container**:
   ```bash
   docker-compose down
   ```

## Customization

- **Font Size**: Users can set the font size using the `/setfontsize` command.
- **Subtitle Position**: Users can choose the subtitle position via a poll.

## License

This project is licensed under the MIT License.

### status
* docker-compose runs python and ollama 
** ollama model gemma2 is downloaded and pulled from ollama server
** and then python service send requests to ollama server for translation of text


Next Steps:
* plan telegram bot for that : Done 
* How bind subtitle with different ass style file !
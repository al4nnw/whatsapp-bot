from pathlib import Path
import openai
import asyncio

# Initialize the OpenAI client
client = openai.Client()

async def transcribe_audio(file_path: Path) -> str:
    """
    Transcribes an audio file using OpenAI's Whisper API via the regular OpenAI API.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        str: The transcribed text.
    """
    def sync_transcribe():
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="text"
            )
            return transcript

    # Run the synchronous transcription in a separate thread to avoid blocking.
    try:
        transcribed_text = await asyncio.to_thread(sync_transcribe)
    except Exception as e:
        print(f"Error during transcription: {e}")
        return ""
    

    print(f"Transcription successful for {file_path}. Transcribed text: {transcribed_text}")
    return transcribed_text
#imports
import asyncio, threading, time, os

import numpy, sounddevice #playing audio

import dotenv #loading env variables
import elevenlabs #text to speech

import pyttsx3 #text to speech

#loading api keys
dotenv.load_dotenv()

#constants
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
SAMPLE_RATE = 22050
MODEL = "eleven_flash_v2_5"
#global variables
_speaking = threading.Event()
_lock = asyncio.Lock()
_client = None
#functions

#returns whether the bot is currently speaking
def is_speaking():
    return _speaking.is_set()

def _get_client():
    global _client
    if _client is None:
        _client = elevenlabs.ElevenLabs(api_key=ELEVENLABS_API_KEY)
    return _client
def _generate_audio(text):
    client = _get_client()
    chunks = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=text,
        model_id=MODEL,
        output_format = "pcm_22050"
    )
    audio_bytes = b''.join(chunks)
    return numpy.frombuffer(audio_bytes, dtype=numpy.int16)
#procedures
def _play_audio(audio):
    sounddevice.play(audio, samplerate=SAMPLE_RATE)
    sounddevice.wait()
def _fallback_speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()
def _speak_blocking(text):
    _speaking.set()
    try:
        _play_audio(_generate_audio(text))
    except Exception as e:
        print(f"[voice] ElevenLabs failed: {e}")
        _fallback_speak(text)
    finally:
        time.sleep(0.3)
        _speaking.clear()
async def speak(text):
    async with _lock:
        await asyncio.to_thread(_speak_blocking, text)

    

if __name__ == "__main__":
    async def test():
        await asyncio.gather(speak("First message."), speak("Second message."))
    asyncio.run(test())


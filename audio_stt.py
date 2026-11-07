import os, asyncio, time
import sounddevice, dotenv
import voice
from deepgram import AsyncDeepgramClient
from models import TranscriptChunk

dotenv.load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
SAMPLE_RATE = 16000
BLOCK_SIZE = 1600
MODEL = "nova-3"

async def _sender(socket, audio_q):
    while True:
        chunk = await audio_q.get()
        if voice.is_speaking():
            chunk = bytes(len(chunk))
        await socket.send_media(chunk)

async def _receiver(socket, out_q):
    async for msg in socket:
        if getattr(msg, "type", None) != "Results":
            continue
        text = msg.channel.alternatives[0].transcript
        if text:
            chunk = TranscriptChunk(
                text=text,
                timestamp=time.time(),
                is_final=bool(msg.is_final))
            await out_q.put(chunk)

async def listen (out_q):
    loop = asyncio.get_running_loop()
    audio_q = asyncio.Queue()

    def _mic_callback(indata, frames, time_info, status):
        try:
            loop.call_soon_threadsafe(audio_q.put_nowait, bytes(indata))
        except RuntimeError:
            pass  # program is shutting down, drop the chunk
    client = AsyncDeepgramClient(api_key=DEEPGRAM_API_KEY)
    with sounddevice.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, dtype="int16", channels=1, callback=_mic_callback):
        while True:
            try:
                async with client.listen.v1.connect(
                    model=MODEL, encoding="linear16", sample_rate=SAMPLE_RATE,
                    channels=1, interim_results="true",
                    smart_format="true", endpointing=300
                ) as socket:
                    print("[audio] connected to Deepgram")
                    sender = asyncio.create_task(_sender(socket, audio_q))
                    receiver = asyncio.create_task(_receiver(socket, out_q))
                    done, pending = await asyncio.wait(
                        [sender, receiver], return_when=asyncio.FIRST_COMPLETED)
                    for task in pending:
                        task.cancel()
                    for task in done:
                        task.result()
            except Exception as e:
                print(f"[audio] connection lost: {e}")
            await asyncio.sleep(1)
if __name__ == "__main__":
    async def test():
        q = asyncio.Queue()
        asyncio.create_task(listen(q))
        while True:
            chunk = await q.get()
            print("FINAL:" if chunk.is_final else "INTERIM:", chunk.text)
    asyncio.run(test())
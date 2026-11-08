import asyncio
from nicegui import ui, app

import interface
from audio_stt import listen
from brain import Brain
from voice import speak

brain = Brain()
async def run_guardian():
    q = asyncio.Queue()
    asyncio.create_task(listen(q))
    while True:
        chunk = await q.get()
        print("HEARD:", chunk.text, "| final" if chunk.is_final else"")
        if not chunk.is_final:
            continue
        label = "You" if chunk.speaker == 0 else "Caller"
        interface.add_transcript(interface.TranscriptChunk(text=chunk.text, speaker=label))
        brain.add_chunk(chunk)
        assessment = await asyncio.to_thread(brain.assess)
        interface.add_assessment(assessment)
        if assessment.should_speak:
            asyncio.create_task(speak(assessment.message))
app.on_startup(run_guardian)
ui.run(host="0.0.0.0", port=8080, reload = False)

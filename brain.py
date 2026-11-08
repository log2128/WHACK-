"""Scam Brain: turns transcript chunks into an Assessment.

The LLM only classifies (risk, tactics, reason, suggested message).
Plain code decides whether the agent should actually speak
"""
import json
import os
import time
from collections import deque

from google import genai
from google.genai import types

from models import Assessment, TranscriptChunk

MODEL = os.getenv("GUARDIAN_MODEL", "gemini-3.5-flash-lite")
WINDOW_SECONDS = 60       # how much transcript the LLM sees
SPEAK_RISK = 60           # risk needed to count as "confident" (tune later)
COOLDOWN_SECONDS = 8     # minimum gap between spoken messages
TACTICS = [
    "safe_account", "hmrc", "hi_mum", "tech_support", "gift_cards",
    "remote_access", "secrecy", "urgency", "authority",
]

SYSTEM_PROMPT = f"""You protect older people from phone scams. You read a live
transcript of a call and judge whether the caller is using social-engineering tactics. Each line starts with PERSON (the older person you protect) or CALLER.
Judge mainly what the CALLER says. Labels can occasionally be wrong.

Allowed tactic ids: {", ".join(TACTICS)}.
One weak tactic alone (for example urgency) is weak evidence. Several together,
or any request for money, gift cards, bank details or remote access, is strong evidence.
Ordinary calls (a GP appointment, a delivery, family chat) must score low.

YOUR PERSONALITY (for the "message" only):
You are Rosie, a warm, steady, quietly witty companion who sits beside the person
like a trusted grandchild. You are on their side, never bossy, never scary.
- Speak directly to them as "you". Plain everyday British English.
- Name the trick in simple words, e.g. "A real bank never asks you to move money."
- Always give ONE clear thing to do, e.g. "Let's hang up and call the number on your card."
- Risk 60-79: gentle and curious, like a raised eyebrow.
- Risk 80+: firm and clear, but still kind. Tell them to hang up.
- Never blame or embarrass them. Scammers are professionals; anyone can be fooled.
- Max 25 words. It will be spoken aloud: no emojis, lists or symbols.

Reply with JSON only, no other text:
{{"risk": <0-100>, "tactics": [<allowed ids>], "reason": "<one short sentence>",
 "message": "<what Rosie says to the person>"}}"""


class Brain:
    def __init__(self):
        self.client = genai.Client()  # reads gemini api key
        self.window: deque[TranscriptChunk] = deque()
        self.recent_confident: list[bool] = []
        self.last_spoke = 0.0

    def reset(self):
        """Forget current call and start a new one."""
        self.window.clear()
        self.recent_confident.clear()
        self.last_spoke = 0.0
    def add_chunk(self, chunk: TranscriptChunk) -> None:
        """Keep only final chunks from the last WINDOW_SECONDS."""
        if not chunk.is_final:
            return
        self.window.append(chunk)
        cutoff = chunk.timestamp - WINDOW_SECONDS
        while self.window and self.window[0].timestamp < cutoff:
            self.window.popleft()

    def assess(self) -> Assessment:
        lines = []
        for c in self.window:
            who = "PERSON" if c.speaker == 0 else "CALLER"
            lines.append(f"{who}: {c.text}")
        transcript = "\n".join(lines)
        if not transcript.strip():
            return Assessment(risk=0)

        try:
            reply = self.client.models.generate_content(
                model=MODEL,
                contents=transcript,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    max_output_tokens=2048,
                ),
            )
            data = json.loads(reply.text)
            risk = max(0, min(100, int(data["risk"])))
            tactics = [t for t in data.get("tactics", []) if t in TACTICS]
            reason = str(data.get("reason", ""))
            message = str(data.get("message", ""))
        except Exception as error:
            print(f"[brain] assessment failed: {error}")
            return Assessment(risk=0, reason="assessment failed")

        return Assessment(
            risk=risk,
            tactics=tactics,
            reason=reason,
            should_speak=self._should_speak(risk),
            message=message,
        )

    def _should_speak(self, risk: int) -> bool:
        """Two confident assessments in a row, and the cooldown is over."""
        self.recent_confident = (self.recent_confident + [risk >= SPEAK_RISK])[-2:]
        confident_twice = len(self.recent_confident) == 2 and all(self.recent_confident)
        cooled_down = time.time() - self.last_spoke >= COOLDOWN_SECONDS
        very_sure = risk >= 80
        if (confident_twice or very_sure) and cooled_down:
            self.last_spoke = time.time()
            return True
        return False


"""if __name__ == "__main__":
    fake_call = [
    ]
    brain = Brain()
    now = time.time()
    for i, line in enumerate(fake_call):
        brain.add_chunk(TranscriptChunk(text=line, timestamp=now + i * 5, is_final=True))
        result = brain.assess()
        print(f"{i + 1}. risk={result.risk} speak={result.should_speak} tactics={result.tactics}")
        if result.should_speak:
            print(f"   SAY: {result.message}")"""


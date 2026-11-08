from dataclasses import dataclass, field

@dataclass
class TranscriptChunk:
    text: str
    timestamp: float
    is_final: bool  # end of a sentence/utterance
    speaker: int | None = None # 0 = first voice heard, 1 = second...


@dataclass
class Assessment:
    risk: int  # 0-100
    tactics: list[str] = field(default_factory=list)  # e.g. ["urgency", "secrecy"]
    reason: str = ""  # short explanation
    should_speak: bool = False  # only interrupt if confident
    message: str = ""  # what the agent says
import json
import logging
import os
from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("strategy_studio_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Strategy Studio API",
    description="Local backend for a resume-ready OpenAI-powered strategy app.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    niche: str = Field(..., min_length=2, max_length=120)
    audience: str = Field(..., min_length=2, max_length=180)
    goal: str = Field(..., min_length=2, max_length=220)
    tone: str = Field(..., min_length=2, max_length=80)
    platforms: List[str] = Field(default_factory=list)
    constraints: str = Field(default="", max_length=400)


class DayPlan(BaseModel):
    day: str
    format: str
    concept: str
    angle: str


class StrategyResponse(BaseModel):
    overview: str
    pillars: List[str]
    hooks: List[str]
    ctas: List[str]
    risks: List[str]
    seven_day_plan: List[DayPlan]


SYSTEM_PROMPT = """You are a senior content strategist.
Produce practical, original strategy outputs for creators and startups.
Return ONLY valid JSON, matching this exact schema:
{
  "overview": "string",
  "pillars": ["string", "string", "string"],
  "hooks": ["string", "string", "string", "string"],
  "ctas": ["string", "string", "string"],
  "risks": ["string", "string", "string"],
  "seven_day_plan": [
    {"day": "Day 1", "format": "string", "concept": "string", "angle": "string"}
  ]
}
Rules:
- 3 pillars, 4 hooks, 3 ctas, 3 risks, and exactly 7 plan entries.
- Keep each string concise and actionable.
- No markdown, no prose outside JSON.
"""

CHAT_SYSTEM_PROMPT = """You are Content Coach GPT, a practical assistant for creators and small teams.
Goal:
- Help users brainstorm content ideas, hooks, outlines, and posting plans.
- Ask clarifying questions when helpful, but stay concise.
- Give actionable advice users can execute immediately.
Style:
- Friendly, direct, and specific.
- Prefer short paragraphs and compact bullet points.
- Avoid fluff and repetition.
"""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    niche: str = Field(..., min_length=2, max_length=120)
    platform: str = Field(default="General", min_length=2, max_length=80)
    objective: str = Field(default="Grow audience", min_length=2, max_length=180)
    model: str = Field(default="gpt-4o-mini", min_length=2, max_length=80)
    messages: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    mode: str


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY is missing. Add it to your environment or .env. "
                "The app will still fall back to mock responses when the key is absent."
            ),
        )
    return OpenAI(api_key=api_key)


def has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not include a valid JSON object")
    return json.loads(text[start : end + 1])


def build_user_prompt(payload: GenerateRequest) -> str:
    platforms = ", ".join(payload.platforms) if payload.platforms else "Not specified"
    return (
        "Build a strategy with this input:\n"
        f"Niche: {payload.niche}\n"
        f"Audience: {payload.audience}\n"
        f"Primary goal: {payload.goal}\n"
        f"Tone: {payload.tone}\n"
        f"Platforms: {platforms}\n"
        f"Constraints: {payload.constraints or 'None'}"
    )


def build_chat_messages(payload: ChatRequest) -> List[dict]:
    preface = (
        "Use this context for the whole conversation:\n"
        f"Niche: {payload.niche}\n"
        f"Primary platform: {payload.platform}\n"
        f"Objective: {payload.objective}\n"
    )
    convo = [{"role": "user", "content": preface}]
    for msg in payload.messages[-12:]:
        convo.append({"role": msg.role, "content": msg.content})
    return convo


def openai_model_name() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()


def normalize_model_name(model: str) -> str:
    candidate = (model or "").strip()
    if not candidate:
        return openai_model_name()
    allowed = {
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
    }
    return candidate if candidate in allowed else openai_model_name()


def mock_chat_reply(payload: ChatRequest) -> str:
    last_user = ""
    for msg in reversed(payload.messages):
        if msg.role == "user":
            last_user = msg.content
            break
    if not last_user:
        last_user = "I need content ideas"
    return (
        f"Great niche for {payload.platform}. Here is a practical direction for your objective ({payload.objective}):\n\n"
        "1) Topic angle: pick one high-friction problem your audience faces weekly.\n"
        "2) Content format: publish a short post + one deeper follow-up thread/video.\n"
        "3) CTA: ask for one specific action (reply, save, or newsletter signup).\n\n"
        f"Based on your message \"{last_user}\", start with this hook:\n"
        "\"Most people fail here because they skip the first 20 minutes of planning.\"\n\n"
        "If you want, I can generate 7 posts next with hooks, outlines, and CTA for each."
    )


def mock_strategy_response(payload: GenerateRequest) -> StrategyResponse:
    base = payload.niche.strip().rstrip(".")
    overview = (
        f"Build a focused content system around {base.lower()} that educates, proves expertise, and converts viewers into subscribers or calls."
    )
    pillars = [
        f"Quick wins for {base}",
        f"Behind-the-scenes process in {base}",
        f"Common mistakes and fixes in {base}",
    ]
    hooks = [
        f"Stop doing this if you want better {base.lower()} results",
        f"The fastest way to improve your {base.lower()} content this week",
        f"Most people get {base.lower()} wrong in this one place",
        f"A simple framework for better {base.lower()} outcomes",
    ]
    ctas = [
        "Comment 'plan' and I’ll send the checklist",
        "DM me for the template",
        "Subscribe for the weekly breakdown",
    ]
    risks = [
        "Avoid posting generic advice without a specific audience angle.",
        "Avoid overloading each post with too many ideas.",
        "Avoid ending posts without a direct next step.",
    ]
    seven_day_plan = [
        DayPlan(day="Day 1", format="Short post", concept=f"Introduce the core problem in {base}", angle="Promise a practical outcome."),
        DayPlan(day="Day 2", format="Carousel", concept="Break down a 3-step framework", angle="Make the steps visual and easy to save."),
        DayPlan(day="Day 3", format="Talking head video", concept="Share one mistake to avoid", angle="Use a bold hook and one example."),
        DayPlan(day="Day 4", format="Text post", concept="Give a quick win checklist", angle="Keep it highly actionable."),
        DayPlan(day="Day 5", format="Case study", concept="Show a real or hypothetical result", angle="Use numbers or a before/after."),
        DayPlan(day="Day 6", format="FAQ post", concept="Answer a common question", angle="Keep it concise and specific."),
        DayPlan(day="Day 7", format="CTA post", concept="Invite readers to reply or subscribe", angle="Make the action simple and low-friction."),
    ]
    return StrategyResponse(
        overview=overview,
        pillars=pillars,
        hooks=hooks,
        ctas=ctas,
        risks=risks,
        seven_day_plan=seven_day_plan,
    )


@app.post("/api/generate", response_model=StrategyResponse)
async def generate_strategy(payload: GenerateRequest) -> StrategyResponse:
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            temperature=0.6,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(payload)},
            ],
        )
        content = response.choices[0].message.content or ""
        parsed = extract_json(content)
        return StrategyResponse.model_validate(parsed)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Strategy generation failed; falling back to mock strategy response")
        return mock_strategy_response(payload)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    if not has_api_key():
        return ChatResponse(reply=mock_chat_reply(payload), mode="mock")

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=normalize_model_name(payload.model),
            temperature=0.6,
            max_tokens=900,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                *build_chat_messages(payload),
            ],
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise ValueError("Empty model response")
        return ChatResponse(reply=content.strip(), mode="openai")
    except Exception as exc:
        logger.exception("Chat generation failed; falling back to mock reply")
        return ChatResponse(reply=mock_chat_reply(payload), mode="mock-fallback")


@app.get("/")
async def serve_app() -> FileResponse:
    index_path = Path(__file__).with_name("index.html")
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "strategy-studio-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
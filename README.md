[readme (1).md](https://github.com/user-attachments/files/26689131/readme.1.md)
Content Coach Chatbot link ( https://contentchatbot.netlify.app/ )

A working,content-based chatbot project with:

Single-file frontend app in `index.html` (HTML + CSS + JS in one file)
  Clean FastAPI backend in `main.py` for local execution
  Dual execution mode:
   Local backend mode via `/api/chat` endpoint
   Local mock fallback when `OPENAI_API_KEY` is not set
 OpenAI model selection in the UI
 Export chat transcripts to Markdown
 Persistent chat history in the browser

Features

Professional chat interface for content planning
 Persistent in-page conversation history
 Robust fallback behavior (artifact Claude API first, local backend second, then mock if needed)
 Health endpoint for ops checks

Local Setup or link (https://contentchatbot.netlify.app/)

1. Create and activate a virtual environment:

bash
python3 -m venv .venv
source .venv/bin/activate


2. Install dependencies:

bash
pip install -r requirements.txt


3. Optional: add environment variable for real OpenAI responses from local backend:

bash
export OPENAI_API_KEY="your_key_here"

Or create `.env` in the project root:

env
OPENAI_API_KEY=your_key_here

4. Run the backend:


python main.py


5. Open the app:

Visit `https://contentchatbot.netlify.app/`

UI Features

- Select an OpenAI model directly in the app
- Use prompt chips for fast starting points
- Watch a typing indicator while the assistant responds
- Export the current transcript as Markdown
- Copy the latest assistant reply with one click

 API Endpoints

`GET /health`
 `POST /api/chat`

Example request body:

json
{
  "niche": "Career coaching for software engineers",
  "platform": "LinkedIn",
  "objective": "Drive newsletter signups",
  "messages": [
    {"role": "user", "content": "Give me 5 post ideas for this week."}
  ]
}
 Notes
 The backend uses OpenAI when `OPENAI_API_KEY` is set.
If no API key is configured locally, `/api/chat` still works in `mock` mode.
You can override the model with `OPENAI_MODEL` or the in-app dropdown.

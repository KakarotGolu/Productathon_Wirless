from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from flask import Flask, render_template, request, jsonify
import requests
import openai
import os
from dotenv import load_dotenv





# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Heurist API URL from environment variable
HEURIST_API_URL = os.getenv("HEURIST_API_URL")

# Pydantic models with updated syntax
class UserRequest(BaseModel):
    niche: str = Field(..., min_length=1, description="The content niche to generate ideas for")

    class Config:
        json_schema_extra = {
            "example": {
                "niche": "fitness"
            }
        }

class ContentResponse(BaseModel):
    content_suggestions: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "content_suggestions": ["Workout routine for beginners", "Healthy meal prep ideas"]
            }
        }

def get_trending_ideas(niche: str) -> List[str]:
    """Fetch trending content ideas from Heurist API."""
    try:
        params = {
            "query": "SELECT * FROM content_ideas WHERE niche = :niche",
            "params": {"niche": niche}
        }

        response = requests.get(
            HEURIST_API_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        if data.get('records'):
            return [record['Suggested Content Idea'] for record in data['records']]
        return ["No trending topics found for this niche."]

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error fetching trending ideas: {str(e)}"
        )

def generate_content_idea(trend: str) -> str:
    """Generate content ideas using GPT-4."""
    try:
        response = openai.Completion.create(
            model="gpt-4",
            prompt=f"Suggest a creative content idea related to '{trend}' for influencers.",
            max_tokens=50,
            temperature=0.7
        )
        return response.choices[0].text.strip()

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error generating content idea: {str(e)}"
        )

@app.post("/chatbot/", response_model=ContentResponse)
async def chatbot(request: UserRequest) -> ContentResponse:
    """Main chatbot endpoint for generating content suggestions."""
    try:
        # Input validation
        if not request.niche.strip():
            raise HTTPException(status_code=400, detail="Niche cannot be empty")

        trending_ideas = get_trending_ideas(request.niche)

        if not trending_ideas or trending_ideas[0].startswith("No trending"):
            return ContentResponse(
                content_suggestions=["No ideas available. Please try a different niche."]
            )

        # Generate suggestions from GPT-4
        content_suggestions = [
            generate_content_idea(trend) for trend in trending_ideas[:3]
        ]

        return ContentResponse(content_suggestions=content_suggestions)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
  

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    message = data.get('message', '')
    response = f"Python received: {message}"
    return jsonify({'reply': response})

if __name__ == '__main__':
    app.run(debug=True)
  

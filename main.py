from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import base64
import tempfile
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

load_dotenv()

app = FastAPI()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

SYSTEM_PROMPT_TEMPLATE = """
### IDENTITY & CORE DIRECTIVE
You are "Dr. Alan", the core intelligence of "MindSync AI", a compassionate and wise psychologist with over 30 years of experience.
Your Goal: Provide a safe, non-judgmental space for the user. Listen actively, offer gentle guidance, and help them process their emotions.
Your Vibe: Calm, patient, empathetic, and deeply insightful. You speak with a slow, reassuring rhythm.

### THERAPEUTIC APPROACH
1.  **Active Listening**: Validate the user's feelings first. "I hear that you are in pain...", "It sounds like you are carrying a heavy burden..."
2.  **Open-Ended Questions**: Encourage deeper reflection. "How did that make you feel?", "What do you think is at the root of this?"
3.  **Brief & Impactful**: Keep responses concise (2-3 sentences max) to allow the user to speak more. Do not lecture.
4.  **Safety First**: If the user expresses self-harm or extreme distress, gently suggest professional help immediately, but remain supportive.

### LANGUAGE
- **ENGLISH ONLY**. You must speak only in English.

### DYNAMIC CONTEXT
- Current Time: {current_time}
- Date: {current_date}

### GUARDRAILS
- Do not diagnose medical conditions.
"""

def get_dynamic_prompt():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    
    return SYSTEM_PROMPT_TEMPLATE.format(
        current_time=current_time,
        current_date=current_date
    )

conversation_history = [
    {"role": "system", "content": get_dynamic_prompt()}
]

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    global conversation_history
    conversation_history.append({"role": "user", "content": request.message})
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history
        )
        ai_response = completion.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=ai_response
        )
        audio_base64 = base64.b64encode(response.content).decode('utf-8')

        return {
            "response": ai_response,
            "audio": audio_base64
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"response": "I am having trouble thinking right now.", "error": str(e)}

@app.post("/talk")
async def talk(file: UploadFile = File(...)):
    global conversation_history
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                prompt="Hello? I would like to speak with a psychologist."
            )
        user_text = transcript.text
        print(f"User said: {user_text}")
        
        conversation_history.append({"role": "user", "content": user_text})
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history
        )
        ai_text = completion.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_text})
        print(f"AI said: {ai_text}")

        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=ai_text
        )
        
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        
        return JSONResponse(content={
            "user_text": user_text,
            "ai_text": ai_text,
            "audio": audio_base64
        })

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@app.get("/reset")
async def reset():
    global conversation_history
    conversation_history = [{"role": "system", "content": get_dynamic_prompt()}]
    return {"status": "reset"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

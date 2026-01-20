from fastapi import FastAPI, Request, UploadFile, File, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import os
import base64
import tempfile
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from sqlalchemy.orm import Session
import stripe
import io
from PIL import Image

import models
import database
import auth

load_dotenv()

# Create Database Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Stripe Setup (Test Key)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

SYSTEM_PROMPT_TEMPLATE = """
### IDENTITY & CORE DIRECTIVE
You are "MindSync AI" (マインドシンクAI), a compassionate and wise Japanese psychologist with over 30 years of experience.
Your Goal: Provide a safe, non-judgmental space for the user. Listen actively, offer gentle guidance, and help them process their emotions.
Your Vibe: Calm, patient, empathetic, and deeply insightful. You speak with a slow, reassuring rhythm.

### THERAPEUTIC APPROACH
1.  **Active Listening**: Validate the user's feelings first. "辛い思いをされましたね...", "それは大変でしたね..."
2.  **Open-Ended Questions**: Encourage deeper reflection. "その時、どのように感じましたか？", "その原因は何だと思いますか？"
3.  **Brief & Impactful**: Keep responses concise (2-3 sentences max) to allow the user to speak more. Do not lecture.
4.  **Safety First**: If the user expresses self-harm or extreme distress, gently suggest professional help immediately, but remain supportive.

### LANGUAGE
- **JAPANESE ONLY**. You must speak only in natural, polite Japanese (Desu/Masu tone).

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

def get_chat_context(user_id: int, db: Session):
    # Get last 10 messages
    messages = db.query(models.Message).filter(models.Message.user_id == user_id).order_by(models.Message.timestamp.asc()).limit(20).all()
    
    context = [{"role": "system", "content": get_dynamic_prompt()}]
    for msg in messages:
        role = "assistant" if msg.role == "ai" else "user"
        context.append({"role": role, "content": msg.content})
    return context

class ChatRequest(BaseModel):
    message: str

class UserCreate(BaseModel):
    email: str
    password: str

# --- Auth Endpoints ---

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"email": new_user.email, "id": new_user.id}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "email": current_user.email, 
        "is_subscribed": current_user.is_subscribed
    }

# --- Subscription Endpoints ---

@app.post("/create-checkout-session")
async def create_checkout_session(request: Request, current_user: models.User = Depends(auth.get_current_active_user)):
    base_url = str(request.base_url).rstrip("/")
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'MindSync AI Premium',
                        },
                        'unit_amount': 999, # $9.99
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'{base_url}/?success=true&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base_url}/?canceled=true',
            metadata={'user_id': current_user.id}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        print(f"Stripe Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-portal-session")
async def create_portal_session(request: Request, current_user: models.User = Depends(auth.get_current_active_user)):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing information found")

    base_url = str(request.base_url).rstrip("/")
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=base_url,
        )
        return {"url": portal_session.url}
    except Exception as e:
        print(f"Stripe Portal Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/me/avatar")
async def upload_avatar(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Resize if too large (max 300x300)
        image.thumbnail((300, 300))
        
        # Convert to Base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Save to DB
        current_user.profile_picture = f"data:image/png;base64,{img_str}"
        db.commit()
        
        return {"profile_picture": current_user.profile_picture}
    except Exception as e:
        print(f"Avatar Upload Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@app.post("/verify-payment")
async def verify_payment(request: Request, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    data = await request.json()
    session_id = data.get('session_id')
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            current_user.is_subscribed = True
            current_user.stripe_customer_id = session.customer
            db.commit()
            return {"status": "success", "message": "Subscription verified"}
        else:
            return {"status": "pending", "message": "Payment not yet confirmed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(database.get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET") # Add this to .env

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('metadata', {}).get('user_id')
        if user_id:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                user.is_subscribed = True
                user.stripe_customer_id = session.get('customer')
                db.commit()
                print(f"User {user.email} subscribed!")

    return {"status": "success"}

# --- Protected Chat Endpoints ---

@app.get("/chat/history")
async def get_history(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_subscribed_user)):
    messages = db.query(models.Message).filter(models.Message.user_id == current_user.id).order_by(models.Message.timestamp.asc()).all()
    return messages

@app.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_subscribed_user)):
    # Save User Message
    user_msg = models.Message(user_id=current_user.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    # Build Context
    context = get_chat_context(current_user.id, db)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=context
        )
        ai_response = completion.choices[0].message.content
        
        # Save AI Message
        ai_msg = models.Message(user_id=current_user.id, role="ai", content=ai_response)
        db.add(ai_msg)
        db.commit()
        
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
async def talk(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_subscribed_user)):
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                prompt="もしもし？心理カウンセラーとお話ししたいのですが。"
            )
        user_text = transcript.text
        print(f"User said: {user_text}")
        
        # Save User Message
        user_msg = models.Message(user_id=current_user.id, role="user", content=user_text)
        db.add(user_msg)
        db.commit()

        # Build Context
        context = get_chat_context(current_user.id, db)

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=context
        )
        ai_text = completion.choices[0].message.content
        
        # Save AI Message
        ai_msg = models.Message(user_id=current_user.id, role="ai", content=ai_text)
        db.add(ai_msg)
        db.commit()
        
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
async def reset(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_subscribed_user)):
    # Delete all messages for this user
    db.query(models.Message).filter(models.Message.user_id == current_user.id).delete()
    db.commit()
    return {"status": "reset"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# MindSync AI (マインドシンクAI)

MindSync AI is a compassionate, voice-enabled AI psychologist designed to provide a safe and non-judgmental space for emotional support. It is fully localized in Japanese and features a premium subscription model.

## Features (機能)

- **Japanese Psychologist Persona**: "MindSync AI" acts as an experienced, empathetic Japanese counselor.
- **Voice Interaction**: "Hold to Speak" (長押しして話す) functionality for natural voice conversations using OpenAI Whisper and TTS.
- **User Authentication**: Secure Email/Password registration and login system.
- **Premium Subscription**: Integrated Stripe payments for monthly subscriptions ($9.99/mo).
    - **Paywall**: Restricts access to AI features for non-subscribed users.
    - **My Account**: Manage subscription status and logout.
- **Chat History**: Conversations are saved to a local SQLite database and restored upon login.

## Tech Stack (技術スタック)

- **Backend**: FastAPI (Python)
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: HTML/CSS/JS (Vanilla)
- **AI Models**: OpenAI GPT-4o (Chat), Whisper (STT), TTS-1 (Audio)
- **Payments**: Stripe API

## Setup (セットアップ)

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment**:
    Create a `.env` file in the root directory with the following variables:
    ```env
    OPENAI_API_KEY=sk-...
    STRIPE_SECRET_KEY=sk_test_...
    STRIPE_WEBHOOK_SECRET=whsec_...
    ```

3.  **Run the Server**:
    ```bash
    python main.py
    ```
    *The database (`sql_app.db`) will be created automatically on the first run.*

4.  **Access the App**:
    Open `http://localhost:8000` in your browser.

## Usage (使い方)

1.  **Register/Login**: Create an account to get started.
2.  **Subscribe**: Use a Stripe Test Card (e.g., `4242...`) to subscribe to the Premium plan.
3.  **Chat**: Type or hold the microphone button to speak with the AI in Japanese.
4.  **History**: Refresh the page or log in again to see your past conversations.

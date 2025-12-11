# MindSync AI

MindSync AI is a compassionate, voice-enabled AI psychologist designed to provide a safe and non-judgmental space for emotional support. Powered by OpenAI's GPT-4o and Text-to-Speech models, it offers a seamless voice and text chat experience.

## Features
- **Empathetic Persona**: "Dr. Alan", an experienced psychologist with a calm and wise demeanor.
- **Voice Interaction**: "Hold to Speak" functionality for natural voice conversations.
- **Text Chat**: Integrated text messaging with spoken AI responses.
- **Visualizer**: Real-time UI feedback for listening, thinking, and speaking states.
- **Session History**: Full conversation log for easy reference.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JS (Vanilla)
- **AI Models**: OpenAI GPT-4o (Chat), Whisper (STT), TTS-1 (Audio)

## Setup
1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure Environment**:
    - Create a `.env` file in the root directory.
    - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`
3.  **Run the Server**:
    ```bash
    python main.py
    ```
    *Or with uvicorn directly:*
    ```bash
    uvicorn main:app --reload
    ```
4.  **Access the App**:
    - Open `http://localhost:8000` in your browser.

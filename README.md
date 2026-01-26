# MindSync AI (マインドシンクAI)

MindSync AI is a compassionate, voice-enabled AI psychologist designed to provide a safe and non-judgmental space for emotional support. Fully localized in Japanese with a premium subscription model.

## Features (機能)

### Core
- 🎙️ **Voice Interaction**: "Hold to Speak" for natural voice conversations (OpenAI Whisper + TTS)
- 💬 **Text Chat**: Type and receive instant AI responses
- 🧠 **Japanese Psychologist Persona**: Empathetic counselor with "Aizuchi" (相槌) listening style
- 📜 **Chat History**: Conversations saved and restored upon login

### Authentication & Subscription
- 🔐 **User Authentication**: Email/Password registration and login
- 👤 **Guest Mode**: Try 3 free messages without registration
- 💳 **Premium Plans**: Stripe integration
  - Monthly: $9.99/月
  - Yearly: $99.99/年 (お得！)
- 📦 **Customer Portal**: Manage/cancel subscription via Stripe

### Safety & Security
- 🚨 **Crisis Detection**: Detects crisis keywords and shows Japan hotlines
  - いのちの電話: 0120-783-556
  - よりそいホットライン: 0120-279-338
- 🔑 **Password Reset**: Forgot password flow with reset link
- 📷 **Profile Pictures**: Upload custom avatar or use default

## Tech Stack (技術スタック)

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL (Vercel) / SQLite (Local) |
| Frontend | HTML/CSS/JS (Vanilla) |
| AI | OpenAI GPT-4o, Whisper, TTS-1 |
| Payments | Stripe API |
| Hosting | Vercel |

## Setup (セットアップ)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment** (`.env`):
   ```env
   OPENAI_API_KEY=sk-...
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   DATABASE_URL=postgresql://...  # Optional, for production
   ```

3. **Run the Server**:
   ```bash
   python main.py
   ```

4. **Access**: `http://localhost:8000`

## Deployment (Vercel)

1. Push to GitHub
2. Import to Vercel
3. Add environment variables
4. Run `/db-migrate` after first deploy

## Usage (使い方)

1. **Register/Login** or try as Guest
2. **Subscribe** with Stripe Test Card: `4242 4242 4242 4242`
3. **Chat** via text or voice
4. **Manage Account** via header avatar

## License

MIT

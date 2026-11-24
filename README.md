# AI Legal Advisor — Full-Stack Starter

An AI-powered legal information assistant designed for educational guidance and project demonstrations (e.g. final-year B.Tech CSE project).

---

## 🚀 Live Deployment Options

This project is pre-configured to be deployed in minutes to **Vercel**, **GitHub Pages**, or **Render**. Choose whichever platform you prefer:

### Option 1: Deploy to Vercel (Recommended — Full-Stack Python + Frontend)

Vercel provides a live URL (e.g. `https://your-project.vercel.app`) with both the interactive frontend and Python FastAPI backend running together.

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for deployment"
   git branch -M main
   git remote add origin https://github.com/<your-username>/ai-legal-advisor.git
   git push -u origin main
   ```
2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
   - Click **Add New...** -> **Project**.
   - Select your `ai-legal-advisor` repository.
   - Framework Preset: **Other** (Root Directory: `./`).
   - (Optional) In **Environment Variables**, you can add your LLM credentials:
     - `LLM_API_KEY`: your OpenAI or compatible API key
     - `LLM_MODEL`: `gpt-4o-mini` (or your model name)
     - `LLM_BASE_URL`: optional custom base URL
   - Click **Deploy**.
3. **Submit your link**: Vercel gives you an instant HTTPS live link like `https://ai-legal-advisor-xyz.vercel.app`.

---

### Option 2: Deploy to GitHub Pages (Fastest Static Submission Link)

GitHub Pages hosts your website directly from your GitHub repository for free at `https://<username>.github.io/<repo-name>/`.

1. Push your repository to GitHub (same step as above).
2. Go to your repository on GitHub.com and open **Settings** ⚙️.
3. In the left sidebar, click **Pages**.
4. Under **Build and deployment**:
   - **Source**: Select `Deploy from a branch`.
   - **Branch**: Select `main` and `/ (root)`.
   - Click **Save**.
5. Wait 1-2 minutes. GitHub will display:
   > *"Your site is live at https://<username>.github.io/<repo-name>/"*
6. The site includes a built-in client demo mode that provides realistic legal answers, topic guidance, and document preview even when running purely statically!

---

### Option 3: Deploy to Render (Free Python Web Service)

1. Push your code to GitHub.
2. Sign up / Log in to [render.com](https://render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. Set:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. Click **Create Web Service**. Render provides your live URL (`https://ai-legal-advisor.onrender.com`).

---

## 💻 Local Development

### 1. Start Backend

```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend API documentation: http://127.0.0.1:8000/docs

### 2. Run Frontend

Open `index.html` in your browser or run:
```bash
python3 -m http.server 5500
```
Then visit http://127.0.0.1:5500

---

## 📁 Project Structure

```text
ai_legal_advisor_fullstack/
├── api/
│   └── index.py            # Vercel serverless Python entrypoint
├── backend/
│   ├── main.py             # FastAPI backend with SQLite history & endpoints
│   ├── requirements.txt    # Backend Python dependencies
│   ├── .env.example        # Environment variable template
│   └── .gitignore
├── frontend/
│   └── index.html          # Frontend single-page application
├── index.html              # Root copy for GitHub Pages & static hosting
├── vercel.json             # Vercel routing configuration
├── render.yaml             # Render deployment configuration
├── Procfile                # Heroku/Render process configuration
├── requirements.txt        # Root dependencies for cloud platforms
└── README.md
```

---

## ⚠️ Disclaimer
This application is for educational purposes only and does not constitute formal legal counsel. Always verify legal provisions through official government gazettes or consult a licensed advocate.

# Stock Scanner - Deployment Guide

## Local Setup

### 1. Run Locally
```bash
# Terminal 1: Start the scanner
source .venv/bin/activate
python Start.py

# Terminal 2: Start the web dashboard
source .venv/bin/activate
python -m flask --app app run
```

Visit `http://localhost:5000` in your browser to see the dashboard.

---

## Deploy Online (Free)

### Option 1: Railway (Recommended - Easiest)

1. **Sign up** at https://railway.app (connect GitHub)

2. **Create new project** → "Deploy from GitHub"

3. **Select your Stock-Scanner repository**

4. **Add environment variables:**
   - Go to Variables tab
   - Add these:
     ```
     FINNHUB_API_KEY=your_api_key_here
     GMAIL_EMAIL=your_email@gmail.com
     GMAIL_PASSWORD=your_app_password
     ```

5. **Update app.py for production:**
   ```python
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
   ```

6. **Create Procfile** in your root:
   ```
   web: python -m flask --app app run
   scanner: python Start.py
   ```

7. **Deploy!** Railway automatically deploys when you push to GitHub.

---

### Option 2: Render (Good Alternative)

1. **Sign up** at https://render.com

2. **New Web Service** → Connect GitHub

3. **Select Stock-Scanner repository**

4. **Configure:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `python -m flask --app app run`

5. **Add environment variables** (same as above)

6. **Deploy!**

---

### Option 3: PythonAnywhere (Easy for Beginners)

1. Go to https://www.pythonanywhere.com
2. Create account (free tier available)
3. Upload your code
4. Set up a web app with Flask
5. Add config variables via dashboard

---

## How It Works

- **Scanner** (Start.py) runs every 5 minutes, checking stocks and logging alerts to the database
- **Dashboard** (app.py) displays all alerts in a beautiful web interface
- **Database** (alerts.db) stores alert history

You can access the dashboard from anywhere once deployed!

---

## Monitoring

- Check the logs in your hosting platform's dashboard
- The scanner runs in the background automatically
- Alerts appear on the dashboard in real-time (refreshes every 30 seconds)

---

## Tips

1. Keep your API keys and passwords in environment variables (never in code)
2. The `.gitignore` file prevents `config.py` from being uploaded
3. Deploy frequently after making changes: `git add . && git commit -m "update" && git push`
4. Monitor your free tier limits on whatever platform you choose

"""Expose the local Flask app through an Ngrok tunnel. Run: python run_public.py"""
import os, sys
from dotenv import load_dotenv
from pyngrok import ngrok
from app import app

load_dotenv()
PORT = 5050
token = os.environ.get("NGROK_AUTHTOKEN")
if not token: sys.exit("Add NGROK_AUTHTOKEN=... to your .env file first.")
ngrok.set_auth_token(token)
url = ngrok.connect(PORT).public_url
print("=" * 54, "\nYOUR PUBLIC WEBSITE URL IS LIVE!\nURL:", url, "\n" + "=" * 54)
app.run(port=PORT, debug=False)  # debug must stay False so Flask does not spawn a reloader

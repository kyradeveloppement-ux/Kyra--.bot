# ⚠️ STANDALONE DEPLOYMENT - NOT PART OF MAIN BOT

This folder contains a **separate webhook service** for Top.gg vote tracking.  
**This is NOT loaded by the main bot** and should be deployed independently.

## Why is this separate?

The Top.gg webhook requires a web server (Quart) to receive vote events from Top.gg's servers.  
To keep the main bot lightweight and focused, this service is designed to run independently.

## How to use this?

### Option 1: Deploy Separately (Recommended)
1. Deploy this folder to a free hosting platform like:
   - **Render** (recommended)
   - Railway
   - Fly.io
   - Vercel

2. Set up environment variables:
   - `BOT_TOKEN` - Your Discord bot token
   - `TOPGG_AUTHORIZATION` - Your Top.gg webhook authorization key
   - `WEBHOOK_URL` - Discord webhook URL for posting vote notifications

3. Configure Top.gg webhook:
   - Go to your bot's Top.gg dashboard
   - Set webhook URL to: `https://your-deployed-url.com/topgg/`
   - Set authorization header to match your `TOPGG_AUTHORIZATION`

### Option 2: Don't use Top.gg webhooks
If you don't need Top.gg vote tracking, you can safely **delete this entire folder**.

## Files in this folder:
- `app/__init__.py` - Quart web server with vote tracking logic
- `server.py` - Entry point for running the app
- `requirements.txt` - Dependencies (Quart, aiohttp, aiosqlite)
- `start.sh` - Shell script for deployment
- `votes.db` - SQLite database for storing vote data (created automatically)

## Important Notes:
- This service uses **Quart** (async Flask alternative)
- The main bot **does NOT depend on this service**
- Vote data is stored in a local SQLite database
- Customize the webhook embed in `app/__init__.py` lines 106-127

## Need help?
Check the original `help.md` file for more detailed instructions.

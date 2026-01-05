# 🚀 Quick Start Guide - Modernized Bot

## What's New in v2.0?

✨ **Cleaner, faster, more maintainable code!**

- 🔥 Removed Flask/Quart dependency
- 🎨 Centralized configuration (colors, emojis, settings)
- 🗄️ Database manager for cleaner code
- 📦 Automatic cog loading system
- 📝 Better documentation and code structure

See [MODERNIZATION.md](MODERNIZATION.md) for full details.

---

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file or set environment variables:
```env
TOKEN=your_discord_bot_token_here
```

### 3. Configure Bot Settings
Edit `utils/config.py` to customize:
- Owner IDs
- Bot name and links
- Emojis (optional)
- Colors (optional)

### 4. Run the Bot
```bash
python main.py
```

---

## Configuration

### Owner IDs
Edit `utils/config.py`:
```python
OWNER_IDS: List[int] = [
    1341478551764860958,  # Your Discord user ID
    # Add more owner IDs here
]
```

### Bot Prefix
Default prefix is `+`. To change it:
```python
DEFAULT_PREFIX = "+"  # Change to your preferred prefix
```

Users can also set custom prefixes per server using the prefix command.

---

## Top.gg Webhook (Optional)

The `top-gg-STANDALONE-DEPLOYMENT/` folder contains a separate webhook service.

**If you don't use Top.gg:** Delete this folder.

**If you use Top.gg:** Deploy this folder separately on Render/Railway/Fly.io
- See `top-gg-STANDALONE-DEPLOYMENT/README.md` for instructions

---

## Database Files

The bot automatically creates these databases:
- `db/np.db` - No-prefix users
- `db/prefix.db` - Guild prefixes
- Other databases as needed by specific features

**No manual setup required!** Databases are created on first run.

---

## Features

### 200+ Commands across 15 categories:
- 🛡️ **Security** - Antinuke & emergency features
- 🤖 **Automoderation** - Anti-spam, anti-caps, anti-link, etc.
- 🔨 **Moderation** - Ban, kick, mute, timeout, etc.
- 🎵 **Music** - High-quality music streaming (disabled by default)
- 👋 **Welcoming** - Customizable welcome messages
- 🎮 **Games** - Fun interactive games
- 🎉 **Giveaway** - Easy giveaway management
- 😄 **Fun** - Entertainment commands
- ⚙️ **Utilities** - Server management tools
- 🎨 **Custom Roles** - Role management
- 🗣️ **Voice** - Voice channel utilities
- 🤖 **AI Image Generator** - Create AI-powered images

---

## Custom Configuration

### Emojis
Edit `utils/config.py`:
```python
class Emojis:
    SUCCESS = "✅"      # Change to <:custom:123456789>
    ERROR = "❌"
    # ... customize all emojis
```

### Colors
Edit `utils/config.py`:
```python
class Colors:
    DEFAULT = 0x000000   # Black
    SUCCESS = 0x00ff00   # Green
    ERROR = 0xff0000     # Red
    # ... customize all colors
```

---

## Adding New Features

### Adding a New Cog
1. Create your cog file in `cogs/commands/` or `cogs/events/`
2. Import it in `cogs/__init__.py`
3. Add it to the appropriate group in `COG_GROUPS`

Example:
```python
# In cogs/__init__.py
from .commands.mycog import MyCog

COG_GROUPS = {
    "commands": [
        Help, General, Fun,
        MyCog  # Add your cog here!
    ],
}
```

That's it! The bot will automatically load it.

---

## Troubleshooting

### Bot doesn't start
- Check your `.env` file has valid `TOKEN`
- Ensure all dependencies are installed
- Check terminal for error messages

### Commands not working
- Verify bot has proper permissions
- Check if command is in ignore list
- Try using bot mention as prefix

### Database errors
- Ensure `db/` directory exists
- Check file permissions
- Bot will auto-create missing databases

---

## Development

### Running in Development
```bash
python main.py
```

### Using Jishaku (Debug Commands)
Jishaku is loaded automatically for bot owners:
```
+jsk py await ctx.send("Hello!")
+jsk su @user command  # Run command as another user
+jsk sh ls -la         # Execute shell commands
```

---

## Support

- **Discord Server:** https://discord.gg/X9NDdMf3xf
- **GitHub Issues:** Report bugs
- **Documentation:** See [MODERNIZATION.md](MODERNIZATION.md)

---

## Credits

- **Original Author:** Natrix
- **Modernization:** GenSpark AI
- **Bot Framework:** discord.py v2.4.0

---

**Enjoy your modernized bot! 🎉**

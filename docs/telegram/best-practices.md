# Telegram Bot Best Practices & FAQ

## General Best Practices

### 1. Security

#### Never Expose Sensitive Information
```python
# ❌ BAD: Exposing API keys in messages
await update.message.reply_text(f"API Key: {settings.API_KEY}")

# ✅ GOOD: Never send credentials
await update.message.reply_text("API connection: ✅ Connected")
```

#### Implement User Authentication
```python
AUTHORIZED_USERS = os.getenv("TELEGRAM_AUTHORIZED_USERS", "").split(",")

def authorized_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if user_id not in AUTHORIZED_USERS:
            await update.message.reply_text("⛔ Unauthorized access")
            logger.warning(f"Unauthorized access attempt: {user_id}")
            return
        return await func(update, context)
    return wrapper
```

#### Validate User Input
```python
async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > MAX_AMOUNT:
            raise ValueError(f"Amount exceeds maximum: {MAX_AMOUNT}")

        # Process valid amount
        await update.message.reply_text(f"Amount set: ${amount:.2f}")

    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"❌ Invalid amount: {str(e)}")
```

#### Secure Configuration
```python
# ✅ Use environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

# ❌ Never hardcode credentials
BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # DON'T DO THIS
```

### 2. User Experience

#### Provide Clear Feedback
```python
# ✅ GOOD: Clear, informative messages
await update.message.reply_text(
    "✅ Order placed successfully!\n\n"
    "Symbol: BTC\n"
    "Size: 0.5\n"
    "Price: $50,000\n"
    "Order ID: #12345"
)

# ❌ BAD: Vague messages
await update.message.reply_text("Done")
```

#### Use Emojis Appropriately
```python
STATUS_EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳"
}

await update.message.reply_text(
    f"{STATUS_EMOJIS['loading']} Processing your request..."
)
```

#### Show Progress for Long Operations
```python
async def long_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send initial message
    msg = await update.message.reply_text("⏳ Starting operation...")

    try:
        # Step 1
        await msg.edit_text("⏳ Step 1/3: Fetching data...")
        await fetch_data()

        # Step 2
        await msg.edit_text("⏳ Step 2/3: Processing...")
        await process_data()

        # Step 3
        await msg.edit_text("⏳ Step 3/3: Saving results...")
        await save_results()

        # Complete
        await msg.edit_text("✅ Operation completed successfully!")

    except Exception as e:
        await msg.edit_text(f"❌ Operation failed: {str(e)}")
```

#### Implement Help Commands
```python
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 **Available Commands**

**Account**
/account - View account balance and info
/positions - Show open positions

**Trading**
/buy <symbol> <amount> - Place buy order
/sell <symbol> <amount> - Place sell order
/close <symbol> - Close position

**Settings**
/settings - Configure bot settings
/notifications - Manage notifications

**Help**
/help - Show this message
/start - Restart bot

Need more help? Contact @your_support
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")
```

### 3. Error Handling

#### Graceful Error Messages
```python
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = await risky_operation()
        await update.message.reply_text(f"✅ Success: {result}")

    except ConnectionError:
        await update.message.reply_text(
            "❌ Connection error. Please check your internet connection and try again."
        )

    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid input: {str(e)}\n\n"
            "Use /help for correct usage."
        )

    except Exception as e:
        logger.exception("Unexpected error")
        await update.message.reply_text(
            "❌ An unexpected error occurred. The issue has been logged."
        )
```

#### Global Error Handler
```python
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error {context.error}")

    # Create error message
    error_msg = "❌ An error occurred."

    # Add specific handling for common errors
    if isinstance(context.error, Forbidden):
        error_msg = "❌ Bot was blocked by user."
    elif isinstance(context.error, BadRequest):
        error_msg = "❌ Invalid request. Please check your input."
    elif isinstance(context.error, TimedOut):
        error_msg = "❌ Request timed out. Please try again."
    elif isinstance(context.error, NetworkError):
        error_msg = "❌ Network error. Please check your connection."

    # Notify user if possible
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(error_msg)
        except Exception:
            pass  # Silently fail if can't send error message

application.add_error_handler(error_handler)
```

### 4. Performance

#### Avoid Rate Limits
```python
import asyncio
from collections import deque
from time import time

class RateLimiter:
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()

    async def acquire(self):
        now = time()

        # Remove old calls
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()

        # Check if limit reached
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            await asyncio.sleep(sleep_time)

        self.calls.append(now)

# Usage
rate_limiter = RateLimiter(max_calls=20, time_window=1.0)

async def send_message(chat_id: int, text: str):
    await rate_limiter.acquire()
    await context.bot.send_message(chat_id=chat_id, text=text)
```

#### Batch Operations
```python
async def send_to_multiple_users(user_ids: list, message: str):
    """Send message to multiple users efficiently."""
    tasks = []

    for user_id in user_ids:
        task = context.bot.send_message(chat_id=user_id, text=message)
        tasks.append(task)

        # Batch in groups of 10
        if len(tasks) >= 10:
            await asyncio.gather(*tasks, return_exceptions=True)
            tasks = []
            await asyncio.sleep(0.5)  # Small delay between batches

    # Send remaining
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
```

#### Cache Frequently Accessed Data
```python
from functools import lru_cache
import time

class TimedCache:
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl

    def get(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value):
        self.cache[key] = (value, time.time())

# Usage
cache = TimedCache(ttl=60)  # 60 second cache

async def get_account_info(user_id: int):
    cached = cache.get(f"account_{user_id}")
    if cached:
        return cached

    # Fetch fresh data
    data = await fetch_from_api()
    cache.set(f"account_{user_id}", data)
    return data
```

### 5. Logging and Monitoring

#### Structured Logging
```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f"logs/bot_{datetime.now():%Y%m%d}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"User {user_id} executed command: {command}")
logger.warning(f"Rate limit approached for user {user_id}")
logger.error(f"API call failed: {error}")
```

#### Monitor Bot Health
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BotMetrics:
    start_time: datetime
    total_messages: int = 0
    total_commands: int = 0
    total_errors: int = 0
    active_users: set = None

    def __post_init__(self):
        if self.active_users is None:
            self.active_users = set()

metrics = BotMetrics(start_time=datetime.now())

async def track_message(update: Update):
    metrics.total_messages += 1
    metrics.active_users.add(update.effective_user.id)

    if update.message.text and update.message.text.startswith('/'):
        metrics.total_commands += 1

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.now() - metrics.start_time
    status_msg = f"""
📊 **Bot Status**

⏱ Uptime: {uptime}
📨 Messages: {metrics.total_messages}
⚡ Commands: {metrics.total_commands}
👥 Active Users: {len(metrics.active_users)}
❌ Errors: {metrics.total_errors}
"""
    await update.message.reply_text(status_msg, parse_mode="Markdown")
```

## Common Pitfalls and Solutions

### Pitfall 1: Not Answering Callback Queries

```python
# ❌ BAD: Forgetting to answer
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Missing: await query.answer()
    await query.edit_message_text("Button clicked!")

# ✅ GOOD: Always answer callback queries
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # This is crucial!
    await query.edit_message_text("Button clicked!")
```

### Pitfall 2: Blocking the Event Loop

```python
# ❌ BAD: Using blocking operations
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time.sleep(5)  # Blocks entire bot!
    await update.message.reply_text("Done")

# ✅ GOOD: Use async sleep
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(5)  # Non-blocking
    await update.message.reply_text("Done")
```

### Pitfall 3: Message Too Long

```python
# ✅ GOOD: Split long messages
async def send_long_message(chat_id: int, text: str, max_length: int = 4096):
    """Split and send long messages."""
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        await context.bot.send_message(chat_id=chat_id, text=chunk)
        await asyncio.sleep(0.1)
```

### Pitfall 4: Not Handling Command Arguments

```python
# ❌ BAD: Assuming arguments exist
async def command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = float(context.args[0])  # May raise IndexError!

# ✅ GOOD: Validate arguments
async def command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /command <amount>")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount")
        return

    # Process amount...
```

### Pitfall 5: Memory Leaks in Context Data

```python
# ❌ BAD: Accumulating data without cleanup
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault('history', []).append(large_data)

# ✅ GOOD: Limit data size
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = context.user_data.setdefault('history', [])
    history.append(data)

    # Keep only last 100 items
    if len(history) > 100:
        context.user_data['history'] = history[-100:]
```

## FAQ

### Q: Should I use polling or webhooks?

**A:**
- **Polling**: Easier to set up, good for development and small bots
- **Webhooks**: More efficient, required for production at scale, needs HTTPS endpoint

For this trading bot, start with polling and migrate to webhooks when needed.

### Q: How do I handle multiple users simultaneously?

**A:** The python-telegram-bot library handles this automatically with async/await. Each handler runs concurrently.

```python
# This works for multiple users simultaneously
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User-specific data
    user_id = update.effective_user.id

    # Each user gets their own execution
    data = await fetch_user_data(user_id)
    await update.message.reply_text(f"Your data: {data}")
```

### Q: How do I persist data between bot restarts?

**A:** Use PicklePersistence:

```python
from telegram.ext import PicklePersistence

persistence = PicklePersistence(filepath="bot_data.pkl")
application = Application.builder().token(token).persistence(persistence).build()

# Data in user_data, chat_data, and bot_data persists automatically
```

### Q: Can I edit messages after sending?

**A:** Yes, save the message reference:

```python
msg = await update.message.reply_text("Processing...")
# Later...
await msg.edit_text("Done!")
```

### Q: How do I send messages to users proactively?

**A:** Use `context.bot.send_message()` with the chat ID:

```python
async def notify_user(chat_id: int, message: str):
    await context.bot.send_message(chat_id=chat_id, text=message)

# Trigger from external event
await notify_user(user_chat_id, "Price alert!")
```

### Q: What's the difference between update.message and update.effective_message?

**A:**
- `update.message`: Only available for new messages
- `update.effective_message`: Works for both new and edited messages, and callback queries

Use `effective_message` for more robust code.

### Q: How do I handle bot startup tasks?

**A:** Use the `post_init` hook:

```python
async def post_init(application: Application):
    """Run after bot starts."""
    logger.info("Bot starting up...")
    await initialize_services()
    await send_admin_notification("Bot started")

application = (
    Application.builder()
    .token(token)
    .post_init(post_init)
    .build()
)
```

### Q: Should I use user_data, chat_data, or bot_data?

**A:**
- `user_data`: Per-user settings (preferences, state)
- `chat_data`: Per-chat settings (group settings)
- `bot_data`: Global data (statistics, configuration)

```python
# Per-user preference
context.user_data['theme'] = 'dark'

# Per-chat setting
context.chat_data['language'] = 'en'

# Global statistic
context.bot_data['total_trades'] = context.bot_data.get('total_trades', 0) + 1
```

## Testing

### Unit Testing

```python
import pytest
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

@pytest.mark.asyncio
async def test_start_command():
    # Create mock update
    user = User(id=123, first_name="Test", is_bot=False)
    chat = Chat(id=123, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text="/start"
    )
    update = Update(update_id=1, message=message)

    # Create mock context
    context = ContextTypes.DEFAULT_TYPE()

    # Test handler
    await start_command(update, context)

    # Assert expected behavior
    assert message.reply_text.called
```

### Integration Testing

```python
# test_bot.py
async def test_bot_responses():
    """Test bot in real environment."""
    from src.bot.main import telegram_bot

    # Build bot
    app = telegram_bot.build()

    # Simulate update
    update_json = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": 123, "first_name": "Test"},
            "chat": {"id": 123, "type": "private"},
            "text": "/start"
        }
    }

    # Process update
    await app.process_update(Update.de_json(update_json, app.bot))
```

## Deployment

### Environment Variables

```bash
# .env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_AUTHORIZED_USERS=123456789,987654321
TELEGRAM_CHAT_ID=123456789

# For production
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/hyperbot.service
[Unit]
Description=Hyperbot Telegram Trading Bot
After=network.target

[Service]
Type=simple
User=hyperbot
WorkingDirectory=/home/hyperbot/app
Environment="PATH=/home/hyperbot/app/venv/bin"
ExecStart=/home/hyperbot/app/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

**Remember**: Always test on a test bot before deploying to production!

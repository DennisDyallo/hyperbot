# Telegram Bot API Reference (python-telegram-bot)

## Overview

This reference covers the `python-telegram-bot` library (v20.x), which provides a pure Python interface for the Telegram Bot API with async/await support.

**Official Documentation**: https://docs.python-telegram-bot.org/

## Installation

```bash
pip install python-telegram-bot==20.7
```

## Basic Setup

### Creating a Bot

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text("Hello! I'm your bot.")

def main():
    # Create application
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))

    # Run bot
    application.run_polling()

if __name__ == "__main__":
    main()
```

## Core Concepts

### 1. Application

The `Application` class is the main entry point for your bot.

```python
from telegram.ext import Application

# Build application
application = (
    Application.builder()
    .token(bot_token)
    .post_init(post_init_callback)
    .post_shutdown(post_shutdown_callback)
    .build()
)
```

**Key Methods:**
- `add_handler(handler)` - Register a handler
- `run_polling()` - Start polling for updates
- `run_webhook()` - Run with webhooks
- `stop()` - Stop the bot gracefully

### 2. Update Object

The `Update` object contains all information about an incoming update.

```python
update.message               # Message object
update.effective_user        # User who sent the update
update.effective_chat        # Chat where update occurred
update.callback_query        # Callback query from inline button
update.effective_message     # Message (works for both messages and edited messages)
```

### 3. Context Object

The `ContextTypes.DEFAULT_TYPE` provides context for handlers.

```python
context.bot                  # Bot instance
context.user_data            # Per-user data storage (dict)
context.chat_data            # Per-chat data storage (dict)
context.bot_data             # Global bot data storage (dict)
context.args                 # Command arguments
context.error                # Error object (in error handlers)
context.job_queue            # Job queue for scheduled tasks
```

## Handlers

### CommandHandler

Handle commands like `/start`, `/help`, etc.

```python
from telegram.ext import CommandHandler

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Access command arguments
    args = context.args  # /command arg1 arg2 -> ['arg1', 'arg2']
    await update.message.reply_text(f"Arguments: {args}")

application.add_handler(CommandHandler("command", command_handler))
```

### MessageHandler

Handle text messages, photos, documents, etc.

```python
from telegram.ext import MessageHandler, filters

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")

# Handle all text messages
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

# Handle photos
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # Get highest resolution
    file = await photo.get_file()
    await file.download_to_drive("photo.jpg")

application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
```

### CallbackQueryHandler

Handle inline keyboard button presses.

```python
from telegram.ext import CallbackQueryHandler

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Answer the callback query

    # Get button data
    button_data = query.data

    # Edit the message
    await query.edit_message_text(f"You clicked: {button_data}")

application.add_handler(CallbackQueryHandler(button_handler))
```

### ConversationHandler

Handle multi-step conversations.

```python
from telegram.ext import ConversationHandler

# Define states
NAME, AGE, LOCATION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("What's your name?")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("How old are you?")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Where are you from?")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    await update.message.reply_text("Thank you! Registration complete.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('register', start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

application.add_handler(conv_handler)
```

## Inline Keyboards

### Creating Inline Keyboards

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Create keyboard
keyboard = [
    [
        InlineKeyboardButton("Option 1", callback_data="opt1"),
        InlineKeyboardButton("Option 2", callback_data="opt2")
    ],
    [InlineKeyboardButton("Option 3", callback_data="opt3")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

# Send message with keyboard
await update.message.reply_text(
    "Choose an option:",
    reply_markup=reply_markup
)
```

### Handling Callbacks

```python
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Always answer callback queries

    if query.data == "opt1":
        await query.edit_message_text("You chose Option 1")
    elif query.data == "opt2":
        await query.edit_message_text("You chose Option 2")
    elif query.data == "opt3":
        await query.edit_message_text("You chose Option 3")

application.add_handler(CallbackQueryHandler(button_callback))
```

### Reply Keyboards

```python
from telegram import ReplyKeyboardMarkup, KeyboardButton

# Create reply keyboard
keyboard = [
    [KeyboardButton("Button 1"), KeyboardButton("Button 2")],
    [KeyboardButton("Button 3")]
]
reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,  # Optimize keyboard size
    one_time_keyboard=True  # Hide after one use
)

await update.message.reply_text(
    "Choose a button:",
    reply_markup=reply_markup
)
```

## Message Formatting

### Markdown

```python
await update.message.reply_text(
    "*bold* _italic_ `code` [link](http://example.com)",
    parse_mode="Markdown"
)
```

### MarkdownV2 (Recommended)

```python
from telegram.helpers import escape_markdown

text = escape_markdown("Text with special chars!", version=2)
await update.message.reply_text(
    f"*Bold* _Italic_ ||Spoiler|| `Code`\n{text}",
    parse_mode="MarkdownV2"
)
```

### HTML

```python
await update.message.reply_text(
    "<b>Bold</b> <i>Italic</i> <code>Code</code> <a href='http://example.com'>Link</a>",
    parse_mode="HTML"
)
```

## Sending Messages

### Text Messages

```python
# Simple message
await context.bot.send_message(
    chat_id=chat_id,
    text="Hello!"
)

# With formatting
await context.bot.send_message(
    chat_id=chat_id,
    text="*Bold text*",
    parse_mode="Markdown"
)
```

### Photos

```python
# From file
with open('photo.jpg', 'rb') as photo:
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption="Photo caption"
    )

# From URL
await context.bot.send_photo(
    chat_id=chat_id,
    photo="https://example.com/photo.jpg"
)
```

### Documents

```python
with open('document.pdf', 'rb') as doc:
    await context.bot.send_document(
        chat_id=chat_id,
        document=doc,
        caption="Document caption"
    )
```

### Multiple Messages

```python
async def send_multiple(chat_id: int):
    """Send multiple messages efficiently."""
    messages = ["Message 1", "Message 2", "Message 3"]

    for msg in messages:
        await context.bot.send_message(chat_id=chat_id, text=msg)
        await asyncio.sleep(0.1)  # Small delay to avoid rate limits
```

## Error Handling

### Error Handler

```python
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")

    # Notify user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "An error occurred. Please try again."
        )

application.add_error_handler(error_handler)
```

### Try-Except in Handlers

```python
async def safe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Your code here
        result = await risky_operation()
        await update.message.reply_text(f"Success: {result}")
    except Exception as e:
        logger.exception("Handler error")
        await update.message.reply_text(f"Error: {str(e)}")
```

## Job Queue (Scheduled Tasks)

### One-Time Job

```python
async def alarm(context: ContextTypes.DEFAULT_TYPE):
    """Send a message."""
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="Alarm!"
    )

async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a timer."""
    # Run after 60 seconds
    context.job_queue.run_once(
        alarm,
        60,
        chat_id=update.effective_chat.id,
        name=str(update.effective_chat.id)
    )
    await update.message.reply_text("Timer set for 60 seconds!")
```

### Repeating Job

```python
async def repeating_task(context: ContextTypes.DEFAULT_TYPE):
    """Task that runs periodically."""
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="Periodic update!"
    )

async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start periodic monitoring."""
    context.job_queue.run_repeating(
        repeating_task,
        interval=300,  # Every 5 minutes
        first=10,  # Start after 10 seconds
        chat_id=update.effective_chat.id
    )
    await update.message.reply_text("Monitoring started!")
```

### Cancel Jobs

```python
async def stop_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all jobs for this chat."""
    jobs = context.job_queue.get_jobs_by_name(str(update.effective_chat.id))
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text("All jobs cancelled!")
```

## Persistence

Save bot data between restarts:

```python
from telegram.ext import PicklePersistence

# Create persistence
persistence = PicklePersistence(filepath="bot_data.pkl")

# Build application with persistence
application = (
    Application.builder()
    .token(bot_token)
    .persistence(persistence)
    .build()
)

# Data persists automatically
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['count'] = context.user_data.get('count', 0) + 1
    await update.message.reply_text(f"Count: {context.user_data['count']}")
```

## Best Practices

### 1. Use Decorators for Authentication

```python
from functools import wraps

AUTHORIZED_USERS = [123456789, 987654321]

def restricted(func):
    """Restrict access to authorized users."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            await update.message.reply_text("Unauthorized!")
            return
        return await func(update, context)
    return wrapper

@restricted
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin action executed!")
```

### 2. Rate Limiting

```python
from collections import defaultdict
import time

user_last_message = defaultdict(float)
RATE_LIMIT = 1.0  # 1 second between messages

async def rate_limited_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_time = time.time()

    if current_time - user_last_message[user_id] < RATE_LIMIT:
        await update.message.reply_text("Please slow down!")
        return

    user_last_message[user_id] = current_time
    # Handle message
```

### 3. Logging

```python
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id}: {update.message.text}")
```

### 4. Context Data Management

```python
async def store_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Per-user data
    context.user_data['preference'] = 'dark_mode'

    # Per-chat data
    context.chat_data['settings'] = {'notifications': True}

    # Global bot data
    context.bot_data['total_users'] = context.bot_data.get('total_users', 0) + 1
```

### 5. Graceful Shutdown

```python
async def post_shutdown(application: Application):
    """Cleanup before shutdown."""
    logger.info("Bot shutting down...")
    # Close connections, save data, etc.

application = (
    Application.builder()
    .token(bot_token)
    .post_shutdown(post_shutdown)
    .build()
)
```

## Common Patterns

### Pattern 1: Menu System

```python
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Account", callback_data="menu_account")],
        [InlineKeyboardButton("💼 Positions", callback_data="menu_positions")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🏠 Main Menu",
        reply_markup=reply_markup
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_account":
        await show_account(query)
    elif query.data == "menu_positions":
        await show_positions(query)
    elif query.data == "menu_settings":
        await show_settings(query)
```

### Pattern 2: Confirmation Dialog

```python
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data="confirm_delete"),
            InlineKeyboardButton("❌ No", callback_data="cancel_delete")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚠️ Are you sure you want to delete?",
        reply_markup=reply_markup
    )

async def confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_delete":
        # Perform deletion
        await query.edit_message_text("✅ Deleted successfully!")
    else:
        await query.edit_message_text("❌ Cancelled")
```

### Pattern 3: Pagination

```python
async def show_page(query, page: int, items: list):
    """Show paginated results."""
    items_per_page = 5
    start = page * items_per_page
    end = start + items_per_page

    page_items = items[start:end]
    total_pages = (len(items) - 1) // items_per_page + 1

    text = "\n".join(page_items)

    keyboard = []
    nav_buttons = []

    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"📄 Page {page+1}/{total_pages}\n\n{text}",
        reply_markup=reply_markup
    )
```

## Limits and Restrictions

- **Message length**: 4096 characters max
- **Caption length**: 1024 characters max
- **File size**: 50 MB for photos, 2 GB for other files
- **Rate limits**: 30 messages/second to different chats
- **Inline keyboard**: Up to 100 buttons
- **Commands**: Must start with '/', 1-32 characters

## Resources

- **Official Docs**: https://docs.python-telegram-bot.org/
- **Examples**: https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Community**: https://t.me/pythontelegrambotgroup

---

**Version**: python-telegram-bot v20.7
**Last Updated**: October 2025

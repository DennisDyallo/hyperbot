# Telegram Bot Features Guide

## Overview

This guide covers all the features available in Telegram bots and how to implement them effectively using python-telegram-bot.

## 1. Commands

### Basic Commands

Commands are the primary way users interact with bots.

```python
from telegram.ext import CommandHandler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome!")

application.add_handler(CommandHandler("start", start))
```

**Features:**
- Start with `/` character
- Can have parameters: `/command param1 param2`
- Visible in command menu (set with BotFather)
- Support deep linking: `https://t.me/botname?start=parameter`

**Best Practices:**
- Keep commands short and memorable
- Provide `/help` command
- Use `/start` for initialization
- Document all commands

## 2. Inline Keyboards

Interactive buttons attached to messages.

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

keyboard = [
    [
        InlineKeyboardButton("Option 1", callback_data="1"),
        InlineKeyboardButton("Option 2", callback_data="2")
    ],
    [InlineKeyboardButton("URL", url="https://example.com")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text(
    "Choose an option:",
    reply_markup=reply_markup
)
```

**Button Types:**
- `callback_data`: Trigger callback query
- `url`: Open URL
- `switch_inline_query`: Start inline query
- `pay`: Payment button
- `web_app`: Open mini app

**Limitations:**
- Max 100 buttons per message
- Max 64 bytes per callback_data
- Max 8 buttons per row recommended

## 3. Reply Keyboards

Custom keyboard that replaces the user's keyboard.

```python
from telegram import ReplyKeyboardMarkup, KeyboardButton

keyboard = [
    [KeyboardButton("📊 Account"), KeyboardButton("💼 Positions")],
    [KeyboardButton("⚙️ Settings")]
]
reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,
    one_time_keyboard=False
)

await update.message.reply_text(
    "Main menu:",
    reply_markup=reply_markup
)
```

**Options:**
- `resize_keyboard`: Optimize size
- `one_time_keyboard`: Hide after use
- `selective`: Show to specific users
- `input_field_placeholder`: Hint text

**Special Buttons:**
- `request_contact`: Request phone number
- `request_location`: Request location
- `request_poll`: Request poll creation

## 4. Inline Mode

Allow users to use bot in any chat via `@botname query`.

```python
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    results = [
        InlineQueryResultArticle(
            id="1",
            title="Result 1",
            input_message_content=InputTextMessageContent(f"You searched: {query}")
        )
    ]

    await update.inline_query.answer(results)

application.add_handler(InlineQueryHandler(inline_query))
```

**Result Types:**
- Article (text)
- Photo
- Video
- Audio
- Document
- Location
- Venue
- Contact
- Game

**Use Cases:**
- Quick lookups
- Share content across chats
- Mini search engine
- Content recommendations

## 5. Media Support

### Photos

```python
# Send photo
with open('photo.jpg', 'rb') as photo:
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption="Photo caption"
    )

# Receive photo
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # Highest resolution
    file = await photo.get_file()
    await file.download_to_drive("saved_photo.jpg")
```

### Documents

```python
# Send document
await context.bot.send_document(
    chat_id=chat_id,
    document=open('report.pdf', 'rb'),
    caption="Monthly report"
)

# Receive document
async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file = await document.get_file()
    await file.download_to_drive(document.file_name)
```

### Voice & Audio

```python
# Voice message
await context.bot.send_voice(
    chat_id=chat_id,
    voice=open('voice.ogg', 'rb')
)

# Audio file
await context.bot.send_audio(
    chat_id=chat_id,
    audio=open('song.mp3', 'rb'),
    title="Song Title",
    performer="Artist"
)
```

### Video

```python
await context.bot.send_video(
    chat_id=chat_id,
    video=open('video.mp4', 'rb'),
    caption="Video caption",
    supports_streaming=True
)
```

**Limits:**
- Photos: 10 MB (20 MB as document)
- Videos: 50 MB
- Audio: 50 MB
- Documents: 50 MB
- Voice: No limit (recommended < 20 MB)

## 6. Rich Text Formatting

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

text = escape_markdown("Special chars: _*[]()~>#+-=|{}.!", version=2)
await update.message.reply_text(
    f"*Bold* _Italic_ __Underline__ ~Strike~ ||Spoiler||\n{text}",
    parse_mode="MarkdownV2"
)
```

### HTML

```python
await update.message.reply_text(
    "<b>Bold</b> <i>Italic</i> <u>Underline</u> "
    "<s>Strike</s> <code>Code</code> "
    "<a href='http://example.com'>Link</a>",
    parse_mode="HTML"
)
```

**Entities:**
- Bold: `**text**` or `<b>text</b>`
- Italic: `_text_` or `<i>text</i>`
- Code: `` `code` `` or `<code>code</code>`
- Pre: ` ```code``` ` or `<pre>code</pre>`
- Link: `[text](url)` or `<a href="url">text</a>`

## 7. Conversations

Multi-step interactions using ConversationHandler.

```python
from telegram.ext import ConversationHandler

STATE1, STATE2, STATE3 = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("What's your name?")
    return STATE1

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("How old are you?")
    return STATE2

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text(
        f"Nice to meet you, {context.user_data['name']}!"
    )
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('register', start)],
    states={
        STATE1: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        STATE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
```

**Features:**
- State management
- Per-user conversations
- Timeout support
- Fallback handlers
- Nested conversations

## 8. Payments

Accept payments directly in Telegram.

```python
from telegram import LabeledPrice

async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="Product Name",
        description="Product description",
        payload="product-payload",
        provider_token="PAYMENT_PROVIDER_TOKEN",
        currency="USD",
        prices=[
            LabeledPrice("Item", 1000),  # $10.00
            LabeledPrice("Tax", 100)      # $1.00
        ]
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)  # Approve payment

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Payment successful! Thank you.")

application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
```

**Supported Providers:**
- Stripe
- Yandex.Money
- PayPal (via third parties)
- And more...

## 9. Web Apps (Mini Apps)

Embed web applications in Telegram.

```python
from telegram import WebAppInfo, InlineKeyboardButton

keyboard = [
    [InlineKeyboardButton(
        "Open Web App",
        web_app=WebAppInfo(url="https://your-webapp.com")
    )]
]

await update.message.reply_text(
    "Click to open the app:",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
```

**Features:**
- Full-screen web interface
- Access to user data
- Send data back to bot
- Payment integration
- Theme-aware

## 10. Polls & Quizzes

Create interactive polls.

```python
# Regular poll
await context.bot.send_poll(
    chat_id=chat_id,
    question="What's your favorite feature?",
    options=["Inline Keyboards", "Commands", "Media", "Polls"],
    is_anonymous=True,
    allows_multiple_answers=False
)

# Quiz
await context.bot.send_poll(
    chat_id=chat_id,
    question="What is 2+2?",
    options=["3", "4", "5"],
    type="quiz",
    correct_option_id=1,  # Index of correct answer
    explanation="Basic math!"
)
```

## 11. File Management

Handle files efficiently.

```python
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get file
    document = update.message.document
    file = await document.get_file()

    # Download to memory
    file_bytes = await file.download_as_bytearray()

    # Or download to disk
    await file.download_to_drive("saved_file.pdf")

    # Get file info
    file_id = document.file_id
    file_size = document.file_size
    file_name = document.file_name

    await update.message.reply_text(
        f"Received: {file_name} ({file_size} bytes)"
    )
```

## 12. Groups & Channels

### Group Management

```python
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members."""
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"Welcome {member.first_name}!"
        )

application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

# Admin actions
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user."""
    if update.effective_user.id in ADMIN_IDS:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_to_ban_id
        )
```

### Channel Posts

```python
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel posts."""
    post = update.channel_post
    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=f"New post in channel: {post.text}"
    )

application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, channel_post))
```

## 13. Notifications

Send proactive notifications.

```python
async def send_notification(user_id: int, message: str):
    """Send notification to user."""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="Markdown"
        )
    except Forbidden:
        logger.warning(f"User {user_id} blocked the bot")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

# Trigger from external events
await send_notification(user_id, "⚠️ Price alert: BTC reached $50,000!")
```

## 14. Scheduled Messages

Use Job Queue for scheduled tasks.

```python
async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily report."""
    report = generate_report()
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=report
    )

# Schedule daily at 9 AM
from datetime import time
context.job_queue.run_daily(
    daily_report,
    time=time(hour=9, minute=0),
    chat_id=user_chat_id
)
```

## 15. Message Editing

Edit messages after sending.

```python
# Send initial message
message = await update.message.reply_text("Processing...")

# Edit text
await message.edit_text("Done!")

# Edit reply markup
await message.edit_reply_markup(new_keyboard)

# Delete message
await message.delete()
```

## 16. Chat Actions

Show typing indicators.

```python
from telegram.constants import ChatAction

await context.bot.send_chat_action(
    chat_id=chat_id,
    action=ChatAction.TYPING
)

# Other actions: UPLOAD_PHOTO, UPLOAD_VIDEO, UPLOAD_DOCUMENT, etc.
```

## 17. Deep Linking

Create links that start bot with parameters.

```python
# Create deep link
deep_link = f"https://t.me/{bot_username}?start=ref123"

# Handle in /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        ref_code = context.args[0]  # "ref123"
        await update.message.reply_text(f"Referred by: {ref_code}")
```

## 18. Location Sharing

Request and send location.

```python
from telegram import KeyboardButton, ReplyKeyboardMarkup

# Request location
keyboard = [[KeyboardButton("Share Location", request_location=True)]]
await update.message.reply_text(
    "Share your location:",
    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
)

# Handle location
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    lat = location.latitude
    lon = location.longitude
    await update.message.reply_text(f"Location: {lat}, {lon}")
```

## 19. Contact Sharing

Request and send contacts.

```python
# Request contact
keyboard = [[KeyboardButton("Share Contact", request_contact=True)]]
await update.message.reply_text(
    "Share your contact:",
    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
)

# Handle contact
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number
    name = contact.first_name
    await update.message.reply_text(f"Contact: {name} - {phone}")
```

## 20. Games

Create interactive games.

```python
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_game(
        chat_id=update.effective_chat.id,
        game_short_name="my_game"
    )

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    # Generate game URL with authentication
    game_url = f"https://game.example.com?user={user_id}"

    await query.answer(url=game_url)
```

## Feature Comparison

| Feature | Bot API Support | python-telegram-bot | Use Case |
|---------|----------------|---------------------|-----------|
| Commands | ✅ | ✅ | Primary interaction |
| Inline Keyboards | ✅ | ✅ | Interactive menus |
| Reply Keyboards | ✅ | ✅ | Quick access buttons |
| Inline Mode | ✅ | ✅ | Cross-chat usage |
| Payments | ✅ | ✅ | E-commerce |
| Web Apps | ✅ | ✅ | Rich interfaces |
| Polls | ✅ | ✅ | User feedback |
| Games | ✅ | ✅ | Entertainment |
| Media | ✅ | ✅ | Rich content |
| Groups | ✅ | ✅ | Community |
| Channels | ✅ | ✅ | Broadcasting |

## Best Feature Combinations

### Trading Bot (Our Use Case)
- ✅ Commands (trading actions)
- ✅ Inline Keyboards (position management)
- ✅ Notifications (price alerts)
- ✅ Formatting (clear data display)
- ✅ Conversations (complex order entry)

### Customer Support Bot
- Commands (FAQs)
- Conversations (ticket creation)
- Media (screenshots)
- Reply Keyboards (quick responses)

### News Bot
- Channels (broadcasting)
- Inline Mode (search articles)
- Web Apps (article reader)
- Rich formatting

### E-commerce Bot
- Payments
- Inline Keyboards (product catalog)
- Media (product photos)
- Conversations (checkout)

---

**Remember**: Not all features are needed for every bot. Choose features that enhance user experience without adding complexity.

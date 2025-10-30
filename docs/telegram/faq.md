# Telegram Bots FAQ

## Official Telegram Bot FAQ

### Getting Started

**Q: How do I create a bot?**

A: To create a bot, you must set up an account with [@BotFather](https://telegram.me/botfather) and connect it to a backend server via the Telegram API. Non-programmers cannot create bots without developer assistance - programming knowledge is required.

**Q: Do I need to know programming?**

A: Yes. Creating and running a bot requires programming skills to set up a backend server and interact with the Telegram Bot API.

### Message Visibility & Privacy Mode

**Q: What messages can bots see?**

A: Message visibility depends on privacy mode:

**All bots receive:**
- Service messages (user joined, left, etc.)
- All private chat messages
- Replies to their own messages

**Bots with privacy mode ENABLED** (default) only see:
- Commands explicitly meant for them (e.g., `/command@this_bot`)
- Replies to their messages
- Service messages

**Bot admins with privacy mode DISABLED** see:
- All messages in groups (except messages from other bots)

**Q: Can bots see messages from other bots?**

A: No. Bots deliberately cannot see messages from other bots, regardless of privacy mode. This prevents bot loops and unwanted interactions.

**Q: How do I disable privacy mode?**

A: Use [@BotFather](https://telegram.me/botfather):
1. Send `/mybots`
2. Select your bot
3. Go to Bot Settings → Group Privacy
4. Disable privacy mode

Note: Bot must be re-added to groups after changing this setting.

### Update Methods

**Q: Should I use long polling or webhooks?**

A: Both methods have pros and cons:

**Long Polling:**
- ✅ Easier to set up
- ✅ Works behind firewalls/NAT
- ✅ Good for development
- ❌ Less efficient for high-traffic bots
- ❌ Requires constant connection

**Webhooks:**
- ✅ More efficient
- ✅ Better for production
- ✅ Lower server load
- ❌ Requires HTTPS with valid certificate
- ❌ Requires public IP or domain
- ❌ More complex setup

**Q: How do I avoid duplicate updates with long polling?**

A: Use the `offset` parameter: `offset = update_id of last processed update + 1`

```python
last_update_id = 0
while True:
    updates = get_updates(offset=last_update_id + 1)
    for update in updates:
        process(update)
        last_update_id = update['update_id']
```

**Q: What are the webhook requirements?**

A: Webhooks require:
- Valid SSL certificate (self-signed allowed for testing)
- Ports: 443, 80, 88, or 8443
- CN (Common Name) must **exactly match** your domain
- HTTPS only (except for local Bot API server)

### Rate Limits & Broadcasting

**Q: What are the rate limits?**

A: **Standard limits:**
- **1 message per second** to the same private chat
- **20 messages per minute** to the same group
- **30 messages per second** to different chats (approximately)

**Q: Can I send bulk notifications?**

A: Yes, with two tiers:

**Free tier:**
- About **30 messages per second**
- No additional cost
- Good for most bots

**Paid tier:**
- Up to **1,000 messages per second**
- Cost: **0.1 Stars per message** above free tier
- Requirements:
  - Minimum **100,000 Stars** in account
  - Minimum monthly active users threshold

**Q: What happens if I exceed rate limits?**

A: You'll receive a `429 Too Many Requests` error with a `retry_after` field indicating how many seconds to wait before retrying.

```json
{
  "ok": false,
  "error_code": 429,
  "description": "Too Many Requests: retry after 30",
  "parameters": {
    "retry_after": 30
  }
}
```

### Media & File Handling

**Q: What are the file size limits?**

A:
- **Photos as photo**: 10 MB
- **Photos as document**: 20 MB
- **Videos**: 50 MB
- **Audio**: 50 MB
- **Documents**: 50 MB
- **Voice messages**: No official limit (recommended < 20 MB)

With **Local Bot API Server**:
- **Up to 2,000 MB (2 GB)** for all file types

**Q: How do I download files?**

A: Use the `getFile` method:

1. Get file path: `getFile` with `file_id`
2. Download from: `https://api.telegram.org/file/bot<token>/<file_path>`
3. Maximum download size: **20 MB** (unlimited with local Bot API server)

```python
# Get file info
file = await context.bot.get_file(file_id)

# Download file
await file.download_to_drive('filename.pdf')
```

**Q: Do file IDs persist?**

A: Yes, file IDs remain valid and persistent. You can reuse them to send the same file multiple times without re-uploading.

**Q: What's the difference between sending as photo vs document?**

A:
- **As photo**: Compressed, faster loading, 10 MB limit, shown as image preview
- **As document**: Original quality preserved, 50 MB limit, requires download to view

### Commands & Interaction

**Q: How long can command names be?**

A: Commands can be **1-32 characters** long and must:
- Start with `/`
- Contain only Latin letters, numbers, and underscores
- Be case-insensitive

**Q: How do I show different commands to different users?**

A: Use BotFather's command scope feature:
- Set default commands for all users
- Set specific commands for group admins
- Set specific commands for group members
- Set specific commands for private chats

**Q: What's the maximum callback_data size?**

A: **64 bytes maximum**. For larger data, use a reference ID and store the actual data server-side:

```python
# Store data server-side with ID
data_id = store_data(large_data)

# Use ID in callback
callback_data = f"action_{data_id}"

# Retrieve when callback is triggered
data = get_data(data_id)
```

### Testing & Development

**Q: Should I create a separate bot for testing?**

A: Yes! Always create a separate test bot to:
- Avoid disrupting production users
- Test risky features safely
- Experiment with new functionality
- Prevent accidental data corruption

**Q: Is there a test environment?**

A: Yes, Telegram provides a test environment that allows:
- HTTP (non-TLS) for Web Apps and Web Login
- Separate test data
- Isolated from production

However, most developers simply use a separate test bot in production environment.

**Q: How does BotFather monitor bot health?**

A: BotFather automatically monitors:
- Response rate to messages (~300 requests/minute threshold)
- Inline query response rate
- Overall responsiveness

You'll receive notifications if:
- Reply rate drops abnormally low
- Bot becomes unresponsive
- Inline queries go unanswered

### Business Features

**Q: Can bots manage business accounts?**

A: Yes! Bots can be connected to Telegram Business accounts to:
- Automate private chat management
- Handle messages in business chats
- Mark messages as read
- Delete conversations
- Manage account settings
- Handle star balance and gifts

**Q: Can bots accept payments?**

A: Yes, through:
- **Third-party payment providers** (Stripe, PayPal, etc.) for fiat currency
- **Telegram Stars** (XTR) for digital goods - **Telegram only supports Stars for digital goods**

**Q: Can bots sell digital products?**

A: Yes, but **only using Telegram Stars**. Telegram does not support the sale of digital goods and services using other currencies.

### Monetization

**Q: How can bots make money?**

A: Bots can earn through:
- **Paid content**: Sell subscriptions, courses, digital products
- **Paid media**: Photos/videos users must pay to unlock
- **Telegram Stars**: Accept payments in Stars
- **Ad revenue sharing**: Get 50% of ad revenue (if eligible)
- **Tips & donations**: Accept voluntary payments

**Q: What are Telegram Stars?**

A: Telegram Stars (XTR) are the universal digital currency for bot transactions. Bots can:
- Accept Stars for digital goods
- Convert Stars to Toncoin
- Send gifts to users
- Increase message limits with Stars

**Q: How do users get Telegram Stars?**

A: Users can:
- Purchase through in-app purchases
- Get them from @PremiumBot
- Receive as gifts
- Convert from unique gifts

### Advanced Features

**Q: Can bots post Stories?**

A: Yes! Bots can:
- Post stories with media
- Add clickable areas (locations, links, weather, gifts)
- Edit stories
- Delete stories

**Q: What are Web Apps (Mini Apps)?**

A: Custom HTML5 interfaces that run within Telegram with:
- Full-screen immersive experiences
- Theme customization
- Native dialogs and UI elements
- QR code reading
- Biometric authentication
- Geolocation and motion tracking
- Story sharing capabilities

**Q: Can bots create and manage stickers?**

A: Yes! Bots can:
- Create sticker sets
- Add stickers to existing sets
- Delete stickers
- Support vector animations and .WEBM videos
- Manage custom emoji

**Q: What are suggested posts?**

A: New feature (August 2025) where channels receive content suggestions. Bots can:
- Approve suggested posts
- Decline suggested posts
- Manage channel content programmatically

### Local Bot API Server

**Q: What is the Local Bot API Server?**

A: A self-hosted Bot API server that provides:
- **Unlimited file downloads**
- **2GB file uploads** (vs 50MB)
- **HTTP support** (not just HTTPS)
- **Custom ports** and local IPs
- **Up to 100,000 webhook connections** (vs 100)
- Local file paths and `file://` URIs

**Q: When should I use Local Bot API Server?**

A: Use it when you need:
- Large file handling
- Maximum performance
- Complete control
- Local network deployment
- More webhook connections

### Limits & Restrictions

**Q: What is the maximum message length?**

A:
- **Text messages**: 4,096 characters
- **Captions**: 1,024 characters
- **Poll questions**: 300 characters
- **Poll options**: 100 characters each, 12 options max (increased from 10)

**Q: How many buttons can I have in an inline keyboard?**

A: **Maximum 100 buttons** per message, but 8 buttons per row is recommended for best UX.

**Q: How many users can a bot handle?**

A: There's no hard limit, but consider:
- Rate limits for messaging
- Server capacity
- Database scalability
- API response times

Popular bots serve millions of users successfully.

**Q: Can bots join voice chats?**

A: Bots cannot directly participate in voice chats, but they can:
- Receive notifications about voice chat events
- Manage voice chat settings (as admin)
- Invite users to voice chats

### Language & Localization

**Q: Can bots support multiple languages?**

A: Yes! Bots receive `language_code` (IETF format) in updates and should adapt seamlessly. You can:
- Detect user language from updates
- Set bot descriptions and commands in multiple languages via API
- Use i18n libraries for translation

```python
async def get_text(key: str, lang_code: str) -> str:
    translations = {
        'en': {'welcome': 'Welcome!'},
        'es': {'welcome': '¡Bienvenido!'},
        'fr': {'welcome': 'Bienvenue!'}
    }
    return translations.get(lang_code, translations['en'])[key]
```

### Security & Privacy

**Q: How do I secure my bot token?**

A:
- ✅ Store in environment variables
- ✅ Never commit to version control
- ✅ Use .env files (add to .gitignore)
- ✅ Regenerate if exposed
- ❌ Never hardcode in source
- ❌ Never share publicly

**Q: Can I validate webhook requests?**

A: Yes! Use secret tokens:

```python
# Set secret when configuring webhook
await bot.set_webhook(
    url="https://your-server.com/webhook",
    secret_token="your_secret_token"
)

# Validate in your webhook handler
def webhook_handler(request):
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    if secret != "your_secret_token":
        return 403  # Forbidden
    # Process update...
```

**Q: How do I restrict bot access?**

A: Implement user authentication:

```python
AUTHORIZED_USERS = [123456789, 987654321]

async def restricted_command(update, context):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ Unauthorized")
        return
    # Command logic...
```

### Troubleshooting

**Q: Why isn't my bot responding?**

A: Check:
1. Bot token is correct
2. Server is running and accessible
3. No errors in logs
4. Not rate limited
5. Privacy mode settings (in groups)
6. Bot not blocked by user
7. Webhook configured correctly (if using)

**Q: How do I handle "Bot was blocked by the user" errors?**

A:
```python
from telegram.error import Forbidden

try:
    await context.bot.send_message(chat_id=user_id, text="Hello")
except Forbidden:
    # User blocked the bot - remove from active users list
    logger.info(f"User {user_id} blocked the bot")
    remove_user_from_database(user_id)
```

**Q: Why are my webhooks failing?**

A: Common causes:
- Invalid SSL certificate
- CN doesn't match domain
- Wrong port (use 443, 80, 88, or 8443)
- Firewall blocking Telegram IPs
- Server not responding within 60 seconds
- Response body not empty (should be 200 OK with empty body)

### Performance Optimization

**Q: How can I make my bot faster?**

A:
1. **Use webhooks** instead of polling for production
2. **Cache frequently accessed data**
3. **Use async/await** properly
4. **Batch operations** when possible
5. **Optimize database queries**
6. **Use connection pooling**
7. **Implement request queuing** for rate limit compliance

**Q: Should I use a database?**

A: For production bots: **Yes!**
- Store user preferences
- Track usage statistics
- Persist conversation state
- Cache API responses
- Queue messages

For simple bots: PicklePersistence might be sufficient.

---

**More Questions?**
- 📚 Official API Docs: https://core.telegram.org/bots/api
- 💬 Bot Support: https://t.me/BotSupport
- 👥 Developer Community: https://t.me/TelegramBotDevelopers
- 🤖 BotFather: https://t.me/botfather

**Last Updated**: October 2025

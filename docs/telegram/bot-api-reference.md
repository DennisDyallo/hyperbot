# Telegram Bot API Reference

## Overview

The Telegram Bot API is an HTTP-based interface for developers building bots for Telegram. Bots operate through unique authentication tokens and communicate via HTTPS requests to `https://api.telegram.org/bot<token>/METHOD_NAME`.

**Official Documentation**: https://core.telegram.org/bots/api

## Core Concepts

### Authentication

- Bots use a unique token in the format: `123456:ABC-DEF...`
- Tokens are obtained from [@BotFather](https://t.me/botfather)
- Include the token in the URL: `https://api.telegram.org/bot<YOUR_TOKEN>/METHOD_NAME`

### Request Methods

The API accepts **GET** and **POST** requests through four parameter formats:
- URL query strings
- `application/x-www-form-urlencoded`
- `application/json` (except file uploads)
- `multipart/form-data` (for file uploads)

### Response Structure

All responses contain JSON objects with a Boolean `ok` field:

```json
{
  "ok": true,
  "result": { ... }
}
```

Failed requests include error information:

```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: message text is empty"
}
```

## Update Handling

Two mutually exclusive mechanisms retrieve incoming updates:

### 1. Long Polling (getUpdates)

Retrieves updates with configurable offset and timeout:

```python
import requests

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
params = {
    "offset": last_update_id + 1,
    "timeout": 30,
    "allowed_updates": ["message", "callback_query"]
}
response = requests.get(url, params=params)
```

### 2. Webhooks (setWebhook)

Sends HTTPS POST requests to your specified URL:

```python
url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
data = {
    "url": "https://your-server.com/webhook",
    "secret_token": "your_secret_token",
    "max_connections": 40,
    "allowed_updates": ["message", "callback_query"]
}
response = requests.post(url, json=data)
```

**Webhook Features:**
- HTTPS required (HTTP only for local Bot API server)
- Supports custom certificates
- Fixed IP addresses
- Connection limits (1-100)
- Secret tokens for validation via `X-Telegram-Bot-Api-Secret-Token` header

## Key Object Types

### User

Represents a Telegram user or bot:

```json
{
  "id": 123456789,
  "is_bot": false,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "language_code": "en"
}
```

### Chat

Represents conversations (private, group, supergroup, or channel):

```json
{
  "id": -1001234567890,
  "type": "supergroup",
  "title": "My Group",
  "username": "mygroup",
  "permissions": { ... }
}
```

### Message

The primary data structure containing:
- Sender information
- Timestamps
- Content (text, media, polls, checklists)
- Entities (mentions, URLs, custom emoji)
- Reply chains
- Forwarding metadata

```json
{
  "message_id": 123,
  "from": { ... },
  "chat": { ... },
  "date": 1640000000,
  "text": "Hello, world!",
  "entities": [
    {
      "type": "mention",
      "offset": 0,
      "length": 5
    }
  ]
}
```

## Messaging Methods

### sendMessage

Send text messages:

```python
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = {
    "chat_id": chat_id,
    "text": "Hello, world!",
    "parse_mode": "HTML",  # or "Markdown", "MarkdownV2"
    "disable_web_page_preview": False,
    "reply_markup": {
        "inline_keyboard": [[
            {"text": "Button", "callback_data": "button_pressed"}
        ]]
    }
}
response = requests.post(url, json=data)
```

### Media Messages

**sendPhoto**, **sendVideo**, **sendAudio**, **sendDocument**, **sendAnimation**:

```python
# Upload file
with open('photo.jpg', 'rb') as photo:
    files = {'photo': photo}
    data = {
        'chat_id': chat_id,
        'caption': 'Photo caption'
    }
    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        files=files,
        data=data
    )

# Or use file_id for already uploaded files
data = {
    'chat_id': chat_id,
    'photo': 'AgACAgIAAxkBAAI...',
    'caption': 'Photo caption'
}
```

### sendPoll

Create polls or quizzes:

```python
data = {
    "chat_id": chat_id,
    "question": "What's your favorite color?",
    "options": ["Red", "Blue", "Green", "Yellow"],
    "is_anonymous": True,
    "allows_multiple_answers": False,
    "type": "quiz",  # or "regular"
    "correct_option_id": 1,  # For quizzes
    "explanation": "Blue is the most popular!"
}
```

### sendChecklist

Send collaborative task lists (new feature as of August 2025):

```python
data = {
    "chat_id": chat_id,
    "checklist": [
        {"text": "Task 1", "checked": False},
        {"text": "Task 2", "checked": True},
        {"text": "Task 3", "checked": False}
    ]
}
```

### sendLocation / sendVenue / sendContact

Share location or contact information:

```python
# Location
data = {
    "chat_id": chat_id,
    "latitude": 40.7128,
    "longitude": -74.0060
}

# Venue
data = {
    "chat_id": chat_id,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "title": "Empire State Building",
    "address": "20 W 34th St, New York, NY 10001"
}

# Contact
data = {
    "chat_id": chat_id,
    "phone_number": "+1234567890",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Advanced Messaging Features

**copyMessage / forwardMessage** - Message replication:

```python
data = {
    "chat_id": target_chat_id,
    "from_chat_id": source_chat_id,
    "message_id": message_id
}
```

**editMessageText / editMessageMedia** - Post-send modifications:

```python
data = {
    "chat_id": chat_id,
    "message_id": message_id,
    "text": "Updated text",
    "parse_mode": "HTML"
}
```

**sendPaidMedia** - Monetized content (up to 10,000 Telegram Stars):

```python
data = {
    "chat_id": chat_id,
    "star_count": 100,
    "media": [
        {"type": "photo", "media": "attach://photo1"},
        {"type": "video", "media": "attach://video1"}
    ]
}
```

## Message Formatting

### HTML

```html
<b>bold</b>
<i>italic</i>
<u>underline</u>
<s>strikethrough</s>
<code>code</code>
<pre>pre-formatted</pre>
<a href="http://example.com">link</a>
<tg-spoiler>spoiler</tg-spoiler>
```

### Markdown

```markdown
*bold*
_italic_
`code`
[link](http://example.com)
```

### MarkdownV2

```markdown
*bold*
_italic_
__underline__
~strikethrough~
||spoiler||
`code`
[link](http://example.com)
```

**Note:** Special characters must be escaped in MarkdownV2: `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`

## Inline Keyboards

Create interactive buttons:

```python
reply_markup = {
    "inline_keyboard": [
        [
            {"text": "Option 1", "callback_data": "opt1"},
            {"text": "Option 2", "callback_data": "opt2"}
        ],
        [
            {"text": "URL Button", "url": "https://example.com"}
        ],
        [
            {"text": "Web App", "web_app": {"url": "https://webapp.com"}}
        ]
    ]
}
```

**Button Types:**
- `callback_data` - Send data back to bot (up to 64 bytes)
- `url` - Open URL
- `web_app` - Open Telegram Web App
- `login_url` - Telegram Login Widget
- `switch_inline_query` - Switch to inline mode
- `pay` - Payment button

## Reply Keyboards

Custom keyboard with buttons:

```python
reply_markup = {
    "keyboard": [
        [{"text": "Button 1"}, {"text": "Button 2"}],
        [{"text": "Request Location", "request_location": True}],
        [{"text": "Request Contact", "request_contact": True}]
    ],
    "resize_keyboard": True,
    "one_time_keyboard": True,
    "selective": False
}
```

## Business Account Management

For bots connected to business accounts:

### Account Operations

```python
# Set business account name
data = {"name": "My Business"}
requests.post(f"{url}/setBusinessAccountName", json=data)

# Set username
data = {"username": "mybusiness"}
requests.post(f"{url}/setBusinessAccountUsername", json=data)

# Set bio
data = {"bio": "We sell amazing products"}
requests.post(f"{url}/setBusinessAccountBio", json=data)

# Set profile photo
files = {'photo': open('profile.jpg', 'rb')}
requests.post(f"{url}/setBusinessAccountProfilePhoto", files=files)
```

### Message Operations

```python
# Mark messages as read
data = {"message_ids": [123, 456, 789]}
requests.post(f"{url}/readBusinessMessage", json=data)

# Delete messages
data = {"chat_id": chat_id, "message_ids": [123, 456]}
requests.post(f"{url}/deleteBusinessMessages", json=data)
```

### Star Balance & Gifts

```python
# Get star balance
response = requests.get(f"{url}/getBusinessAccountStarBalance")

# Convert gift to stars
data = {"gift_id": "gift_123"}
requests.post(f"{url}/convertGiftToStars", json=data)

# Transfer gift
data = {"gift_id": "gift_123", "user_id": 123456789}
requests.post(f"{url}/transferGift", json=data)
```

## Stories

Post and manage Telegram Stories:

```python
# Post story
data = {
    "media": {
        "type": "photo",
        "media": "attach://photo"
    },
    "areas": [
        {
            "type": "location",
            "position": {"x": 0.5, "y": 0.5},
            "radius": 0.1,
            "location": {"latitude": 40.7128, "longitude": -74.0060}
        }
    ]
}
files = {'photo': open('story.jpg', 'rb')}
requests.post(f"{url}/postStory", files=files, data=data)

# Edit story
data = {"story_id": 123, "caption": "Updated caption"}
requests.post(f"{url}/editStory", json=data)

# Delete story
data = {"story_id": 123}
requests.post(f"{url}/deleteStory", json=data)
```

**Story Area Types:**
- `StoryAreaTypeLocation` - Location marker
- `StoryAreaTypeLink` - Clickable link
- `StoryAreaTypeWeather` - Weather widget
- `StoryAreaTypeUniqueGift` - Gift display
- `StoryAreaTypeReaction` - Reaction sticker

## Financial Features

### Payments & Invoices

```python
# Send invoice
data = {
    "chat_id": chat_id,
    "title": "Product Name",
    "description": "Product description",
    "payload": "unique_invoice_payload",
    "provider_token": "YOUR_PAYMENT_PROVIDER_TOKEN",
    "currency": "USD",
    "prices": [
        {"label": "Product", "amount": 10000},  # $100.00 (in cents)
        {"label": "Tax", "amount": 800}  # $8.00
    ],
    "max_tip_amount": 5000,
    "suggested_tip_amounts": [100, 500, 1000, 2000]
}
requests.post(f"{url}/sendInvoice", json=data)

# Answer pre-checkout query
data = {
    "pre_checkout_query_id": query_id,
    "ok": True
}
requests.post(f"{url}/answerPreCheckoutQuery", json=data)
```

### Telegram Stars

```python
# Get bot star balance
response = requests.get(f"{url}/getMyStarBalance")

# Gift premium subscription
data = {
    "user_id": 123456789,
    "duration": 30,  # days
    "star_count": 100
}
requests.post(f"{url}/giftPremiumSubscription", json=data)
```

## Chat Administration

### Promote/Restrict Members

```python
# Promote to administrator
data = {
    "chat_id": chat_id,
    "user_id": user_id,
    "can_manage_chat": True,
    "can_post_messages": True,
    "can_edit_messages": True,
    "can_delete_messages": True,
    "can_manage_direct_messages": True,  # New permission
    "can_invite_users": True,
    "can_restrict_members": True,
    "can_pin_messages": True,
    "can_promote_members": False
}
requests.post(f"{url}/promoteChatMember", json=data)

# Restrict member
data = {
    "chat_id": chat_id,
    "user_id": user_id,
    "permissions": {
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_pin_messages": False
    },
    "until_date": 0  # 0 = forever
}
requests.post(f"{url}/restrictChatMember", json=data)
```

### Chat Settings

```python
# Set chat title
data = {"chat_id": chat_id, "title": "New Title"}
requests.post(f"{url}/setChatTitle", json=data)

# Set chat description
data = {"chat_id": chat_id, "description": "New description"}
requests.post(f"{url}/setChatDescription", json=data)

# Set chat photo
files = {'photo': open('photo.jpg', 'rb')}
data = {"chat_id": chat_id}
requests.post(f"{url}/setChatPhoto", files=files, data=data)

# Pin message
data = {
    "chat_id": chat_id,
    "message_id": message_id,
    "disable_notification": False
}
requests.post(f"{url}/pinChatMessage", json=data)
```

### Member Management

```python
# Ban user
data = {
    "chat_id": chat_id,
    "user_id": user_id,
    "until_date": 0,  # Permanent ban
    "revoke_messages": True  # Delete their messages
}
requests.post(f"{url}/banChatMember", json=data)

# Unban user
data = {"chat_id": chat_id, "user_id": user_id, "only_if_banned": True}
requests.post(f"{url}/unbanChatMember", json=data)

# Get chat member info
data = {"chat_id": chat_id, "user_id": user_id}
response = requests.post(f"{url}/getChatMember", json=data)
```

## Recent API Updates (August 2025)

### Checklists

Messages now support collaborative task tracking:

```python
# Send checklist
data = {
    "chat_id": chat_id,
    "checklist": [
        {"text": "Complete task 1", "checked": False},
        {"text": "Complete task 2", "checked": False}
    ]
}

# Edit checklist
data = {
    "chat_id": chat_id,
    "message_id": message_id,
    "checklist": [
        {"text": "Complete task 1", "checked": True},
        {"text": "Complete task 2", "checked": False}
    ]
}
```

### Direct Messages in Channels

Channels can now receive direct messages:

- `is_direct_messages` field identifies channel DM chats
- `direct_messages_topic_id` parameter routes messages to specific topics
- New `DirectMessagePriceChanged` service message for monetization

### Suggested Posts

Channels receive content suggestions:

```python
# Approve suggested post
data = {"suggested_post_id": post_id}
requests.post(f"{url}/approveSuggestedPost", json=data)

# Decline suggested post
data = {"suggested_post_id": post_id}
requests.post(f"{url}/declineSuggestedPost", json=data)
```

### Enhanced Features

- **Poll expansion**: Maximum options increased from 10 to 12
- **Paid posts**: `is_paid_post` field, 24-hour deletion protection
- **Gift tracking**: Unique gift IDs with backdrop colors, symbols, resale history
- **Paid star tracking**: `paid_star_count` field logs star expenditure

## Rate Limits

**Official Limits:**
- 30 messages per second to different chats
- 20 messages per minute to the same group
- 1 message per second to the same private chat

**Best Practices:**
- Implement exponential backoff on errors
- Monitor `retry_after` field in error responses
- Use webhook mode for better throughput

## Error Handling

### Common Error Codes

- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid token)
- `403` - Forbidden (bot blocked by user)
- `404` - Not Found (chat/message doesn't exist)
- `429` - Too Many Requests (rate limited)

### Error Response Example

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

### Handling Errors

```python
response = requests.post(url, json=data)
result = response.json()

if not result["ok"]:
    error_code = result["error_code"]
    description = result["description"]

    if error_code == 429:
        retry_after = result.get("parameters", {}).get("retry_after", 60)
        time.sleep(retry_after)
        # Retry request
    elif error_code == 403:
        # Bot was blocked by user
        pass
    else:
        # Handle other errors
        pass
```

## Local Bot API Server

Self-hosted deployment enables:

- **Unlimited file downloads**
- **2GB file uploads** (vs 50MB standard)
- **Local file paths** and `file://` URIs
- **HTTP webhooks** and any local IP
- **Up to 100,000 webhook connections** (vs 100 standard)

### Setup

```bash
git clone https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --target install
```

### Running

```bash
telegram-bot-api --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local
```

Then use: `http://localhost:8081/bot<token>/METHOD_NAME`

## Best Practices

### 1. Security

- **Never expose your token** in public repositories
- Use environment variables for tokens
- Validate webhook secret tokens
- Implement user authentication for sensitive commands

### 2. Performance

- Use webhooks for production (better than polling)
- Implement request queuing for rate limit compliance
- Cache frequently accessed data
- Use file_id to avoid re-uploading media

### 3. User Experience

- Always answer callback queries (avoid "loading" state)
- Use inline keyboards for better UX
- Provide clear error messages
- Implement `/start` and `/help` commands
- Use reply keyboards sparingly

### 4. Error Handling

- Implement retry logic with exponential backoff
- Log all errors for debugging
- Handle network timeouts gracefully
- Monitor bot health and uptime

### 5. Code Organization

- Separate handlers by feature
- Use dependency injection for services
- Implement middleware for common tasks
- Write unit tests for critical functions

## Resources

- **Official API Docs**: https://core.telegram.org/bots/api
- **Bot API Updates**: https://core.telegram.org/bots/api-changelog
- **BotFather**: https://t.me/botfather
- **Bot Support**: https://t.me/BotSupport
- **Developer Community**: https://t.me/TelegramBotDevelopers

## API Limits

- **Message length**: 4096 characters
- **Caption length**: 1024 characters
- **File size**: 50 MB (photos), 2 GB (other files)
- **Poll options**: 12 (increased from 10)
- **Inline keyboard buttons**: 100 per message
- **Command length**: 1-32 characters
- **Callback data**: 1-64 bytes
- **Username**: 5-32 characters

---

**Last Updated**: October 2025
**API Version**: Bot API 8.0+

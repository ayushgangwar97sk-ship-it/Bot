import os
import json
import logging
import asyncio
from flask import Flask, request, Response

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ChatJoinRequestHandler, CommandHandler,
    ContextTypes, CallbackQueryHandler, MessageHandler, filters
)

# ------------------ CONFIG ------------------
BOT_TOKEN        = os.environ.get("BOT_TOKEN")
ADMIN_ID         = int(os.environ.get("ADMIN_ID", "8080371272"))
SOURCE_CHANNEL   = os.environ.get("SOURCE_CHANNEL", "@bablu922")
APK_MESSAGE_ID   = int(os.environ.get("APK_MESSAGE_ID", "3"))
VIDEO_MESSAGE_ID = int(os.environ.get("VIDEO_MESSAGE_ID", "2"))
VOICE_MESSAGE_ID = int(os.environ.get("VOICE_MESSAGE_ID", "4"))

VIP_CHANNEL_LINK  = "https://t.me/+SogkxdNWQyZkYzRl"
REGISTRATION_LINK = "https://www.shreewin34.com/#/register?invitationCode=64778100774"
LOSS_RECOVER_LINK = "t.me/lossrecoversure"

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

EMOJI_VIDEO = "6147617184479711380"
EMOJI_APK   = "5767209624675553166"
EMOJI_VOICE = "6124902618574625426"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ KEYBOARDS ------------------
VIDEO_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(text="VIP CHANNEL", url=VIP_CHANNEL_LINK,
            icon_custom_emoji_id=EMOJI_VIDEO),
        InlineKeyboardButton(text="LOSS RECOVER", url=LOSS_RECOVER_LINK,
            icon_custom_emoji_id=EMOJI_APK)
    ],
    [
        InlineKeyboardButton(text="REGISTRATION LINK", url=REGISTRATION_LINK,
            icon_custom_emoji_id=EMOJI_VOICE)
    ]
])

APK_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="DM FOR LOSS RECOVERY", url=LOSS_RECOVER_LINK,
        icon_custom_emoji_id=EMOJI_APK)]
])

VOICE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="Join VIP Now Limited Spots", url=VIP_CHANNEL_LINK,
        icon_custom_emoji_id=EMOJI_VIDEO)]
])

START_MESSAGE = (
    "𝗛𝗘𝗟𝗟𝗢\n\n"
    "𝗔𝗔𝗣𝗞𝗜 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗝𝗔𝗟𝗗𝗜 𝗛𝗜 𝗔𝗣𝗣𝗥𝗢𝗩𝗘 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜 \n\n"
    "𝗦𝗘𝗧𝗨𝗣 𝗩𝗜𝗗𝗘𝗢 & 𝗛𝗔𝗖𝗞 𝗔𝗣𝗞 𝗡𝗘𝗘𝗖𝗛𝗘 𝗗𝗜𝗬𝗔 𝗚𝗔𝗬𝗔 𝗛𝗔𝗜"
)

# ------------------ IN-MEMORY USERS ------------------
_users_cache = set()

def add_user(user_id: int):
    _users_cache.add(int(user_id))

def get_all_users():
    return list(_users_cache)

def users_count():
    return len(_users_cache)

# ------------------ HELPERS ------------------
async def send_all_content_to_user(bot, user_id: int):
    await bot.copy_message(chat_id=user_id, from_chat_id=SOURCE_CHANNEL,
        message_id=VIDEO_MESSAGE_ID, reply_markup=VIDEO_KEYBOARD)
    await bot.copy_message(chat_id=user_id, from_chat_id=SOURCE_CHANNEL,
        message_id=APK_MESSAGE_ID, reply_markup=APK_KEYBOARD)
    try:
        await bot.copy_message(chat_id=user_id, from_chat_id=SOURCE_CHANNEL,
            message_id=VOICE_MESSAGE_ID)
        await bot.send_message(chat_id=user_id,
            text="🎤 *Click below to join VIP Channel:*",
            reply_markup=VOICE_KEYBOARD, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Voice send error {user_id}: {e}")

# ------------------ HANDLERS ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    await update.message.reply_text(text=START_MESSAGE)
    try:
        await send_all_content_to_user(context.bot, user.id)
    except Exception as e:
        logger.error(f"Error in start for {user.id}: {e}")

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aap admin nahi ho")
        return
    keyboard = [
        [InlineKeyboardButton("📢 Send Text", callback_data="admin_text")],
        [InlineKeyboardButton("📦 Send APK", callback_data="admin_apk")],
        [InlineKeyboardButton("🎬 Send Video", callback_data="admin_video")],
        [InlineKeyboardButton("🎤 Send Voice", callback_data="admin_voice")],
        [InlineKeyboardButton("📤 Send All Files", callback_data="admin_all")],
        [InlineKeyboardButton("📊 Users Count", callback_data="admin_stats")],
    ]
    await update.message.reply_text("👑 *ADMIN MENU* 👑\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    total = users_count()

    if data == "admin_stats":
        await query.edit_message_text(f"📊 *Total Users:* {total}", parse_mode="Markdown")
        return

    action_map = {
        "admin_apk": ("send_apk", "📦 APK"),
        "admin_video": ("send_video", "🎬 Video"),
        "admin_voice": ("send_voice", "🎤 Voice"),
        "admin_all": ("send_all", "📤 All Files"),
    }

    if data in action_map:
        action, label = action_map[data]
        context.user_data['action'] = action
        await query.edit_message_text(
            f"{label} to All Users\n\nTotal: {total}\n\nType *CONFIRM* to start:",
            parse_mode="Markdown")
    elif data == "admin_text":
        context.user_data['action'] = 'send_text'
        await query.edit_message_text(
            f"📢 *Broadcast Text*\n\nTotal: {total}\n\nSend your message:",
            parse_mode="Markdown")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    action = context.user_data.get('action')
    if not action:
        return
    msg = update.message
    text = msg.text.strip() if msg.text else ""

    if action == 'send_apk' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "apk")
        context.user_data.pop('action', None)
    elif action == 'send_video' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "video")
        context.user_data.pop('action', None)
    elif action == 'send_voice' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "voice")
        context.user_data.pop('action', None)
    elif action == 'send_all' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "all")
        context.user_data.pop('action', None)
    elif action == 'send_text':
        await _do_broadcast(update, context, "text", text)
        context.user_data.pop('action', None)

async def _do_broadcast(update, context, kind, text=""):
    user_ids = get_all_users()
    if not user_ids:
        await update.message.reply_text("❌ No users found.")
        return
    total = len(user_ids)

    sm = await update.message.reply_text(f"⏳ Sending {kind} to {total} users...")

    success = failed = 0
    for uid in user_ids:
        try:
            if kind == "apk":
                await context.bot.copy_message(chat_id=uid, from_chat_id=SOURCE_CHANNEL,
                    message_id=APK_MESSAGE_ID, reply_markup=APK_KEYBOARD)
            elif kind == "video":
                await context.bot.copy_message(chat_id=uid, from_chat_id=SOURCE_CHANNEL,
                    message_id=VIDEO_MESSAGE_ID, reply_markup=VIDEO_KEYBOARD)
            elif kind == "voice":
                await context.bot.copy_message(chat_id=uid, from_chat_id=SOURCE_CHANNEL,
                    message_id=VOICE_MESSAGE_ID)
                await context.bot.send_message(chat_id=uid,
                    text="🎤 *Click below to join VIP Channel:*",
                    reply_markup=VOICE_KEYBOARD, parse_mode="Markdown")
            elif kind == "all":
                await send_all_content_to_user(context.bot, uid)
            elif kind == "text":
                await context.bot.send_message(chat_id=uid, text=text)
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast fail {uid}: {e}")

    await sm.edit_text(f"✅ {kind.upper()} Done\n✅ {success}\n❌ {failed}")

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user = req.from_user
    add_user(user.id)
    try:
        await context.bot.send_message(chat_id=user.id, text=START_MESSAGE)
        await send_all_content_to_user(context.bot, user.id)
    except Exception as e:
        logger.error(f"Join req error {user.id}: {e}")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 Total Users: {users_count()}")

# ------------------ APP ------------------
_application = None

def get_application():
    global _application
    if _application is None:
        _application = Application.builder().token(BOT_TOKEN).build()
        _application.add_handler(CommandHandler("start", start))
        _application.add_handler(CommandHandler("admin", admin_menu))
        _application.add_handler(CommandHandler("users", users_command))
        _application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_"))
        _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))
        _application.add_handler(ChatJoinRequestHandler(handle_join_request))
    return _application

# ------------------ FLASK APP ------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "✅ Bot is alive"

@app.route("/setup", methods=["GET"])
@app.route("/webhook", methods=["GET"])
def setup():
    try:
        application = get_application()
        async def _setup():
            await application.bot.delete_webhook(drop_pending_updates=True)
            await application.bot.set_webhook(
                url=WEBHOOK_URL,
                allowed_updates=["message", "callback_query", "chat_join_request"]
            )
        asyncio.run(_setup())
        return "✅ Webhook set successfully!"
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return f"❌ Setup error: {e}", 500

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        application = get_application()
        update = Update.de_json(data, application.bot)

        async def _process():
            await application.initialize()
            await application.process_update(update)

        asyncio.run(_process())
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "OK", 200

# Vercel entrypoint
handler = app    ]
    await update.message.reply_text("👑 *ADMIN MENU* 👑\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    total = users_count()

    if data == "admin_stats":
        await query.edit_message_text(f"📊 *Total Users:* {total}", parse_mode="Markdown")
        return

    action_map = {
        "admin_apk": ("send_apk", "📦 APK"),
        "admin_video": ("send_video", "🎬 Video"),
        "admin_voice": ("send_voice", "🎤 Voice"),
        "admin_all": ("send_all", "📤 All Files"),
    }

    if data in action_map:
        action, label = action_map[data]
        context.user_data['action'] = action
        await query.edit_message_text(
            f"{label} to All Users\n\nTotal: {total}\n\nType *CONFIRM* to start:",
            parse_mode="Markdown")
    elif data == "admin_text":
        context.user_data['action'] = 'send_text'
        await query.edit_message_text(
            f"📢 *Broadcast Text*\n\nTotal: {total}\n\nSend your message:",
            parse_mode="Markdown")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    action = context.user_data.get('action')
    if not action:
        return
    msg = update.message
    text = msg.text.strip() if msg.text else ""

    if action == 'send_apk' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "apk")
        context.user_data.pop('action', None)
    elif action == 'send_video' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "video")
        context.user_data.pop('action', None)
    elif action == 'send_voice' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "voice")
        context.user_data.pop('action', None)
    elif action == 'send_all' and text.upper() == 'CONFIRM':
        await _do_broadcast(update, context, "all")
        context.user_data.pop('action', None)
    elif action == 'send_text':
        await _do_broadcast(update, context, "text", text)
        context.user_data.pop('action', None)

async def _do_broadcast(update, context, kind, text=""):
    user_ids = get_all_users()
    if not user_ids:
        await update.message.reply_text("❌ No users found (in-memory store khaali hai).")
        return
    total = len(user_ids)
    batch = user_ids

    sm = await update.message.reply_text(
        f"⏳ Sending {kind} to {len(batch)} users..."
    )

    success = failed = 0
    for uid in batch:
        try:
            if kind == "apk":
                await context.bot.copy_message(chat_id=uid, from_chat_id=SOURCE_CHANNEL,
                    message_id=APK_MESSAGE_ID, reply_markup=APK_KEYBOARD)
            elif kind == "video":
                await context.bot.copy_message(chat_id=uid, from_chat_id=SOURCE_CHANNEL,
                    message_id=VIDEO_MESSAGE_ID, reply_markup=VIDEO_KEYBOARD)
            elif kind == "voice":
                await context.bot.copy_message(chat_id=uid, from_chat_id=SOURCE_CHANNEL,
                    message_id=VOICE_MESSAGE_ID)
                await context.bot.send_message(chat_id=uid,
                    text="🎤 *Click below to join VIP Channel:*",
                    reply_markup=VOICE_KEYBOARD, parse_mode="Markdown")
            elif kind == "all":
                await send_all_content_to_user(context.bot, uid)
            elif kind == "text":
                await context.bot.send_message(chat_id=uid, text=text)
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast fail {uid}: {e}")

    await sm.edit_text(
        f"✅ {kind.upper()} Done\n✅ Success: {success}\n❌ Failed: {failed}"
    )

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user = req.from_user
    add_user(user.id)
    try:
        await context.bot.send_message(chat_id=user.id, text=START_MESSAGE)
        await send_all_content_to_user(context.bot, user.id)
    except Exception as e:
        logger.error(f"Join req error {user.id}: {e}")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 Total Users: {users_count()}")

# ------------------ APP ------------------
_application = None

def get_application():
    global _application
    if _application is None:
        _application = Application.builder().token(BOT_TOKEN).build()
        _application.add_handler(CommandHandler("start", start))
        _application.add_handler(CommandHandler("admin", admin_menu))
        _application.add_handler(CommandHandler("users", users_command))
        _application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_"))
        _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))
        _application.add_handler(ChatJoinRequestHandler(handle_join_request))
    return _application

# ------------------ VERCEL HANDLER ------------------
class handler(BaseHTTPRequestHandler):

    def _send(self, code: int, text: str):
        self.send_response(code)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        # Setup: /webhook?setup=1
        if "setup" in query:
            try:
                app = get_application()
                async def _setup():
                    await app.bot.delete_webhook(drop_pending_updates=True)
                    await app.bot.set_webhook(
                        url=WEBHOOK_URL,
                        allowed_updates=["message", "callback_query", "chat_join_request"]
                    )
                asyncio.run(_setup())
                self._send(200, "✅ Webhook set successfully!")
            except Exception as e:
                logger.error(f"Setup error: {e}")
                self._send(500, f"❌ Setup error: {e}")
            return

        self._send(200, "✅ Bot is alive")

    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", 0))
            body = self.rfile.read(length).decode("utf-8")
            app = get_application()
            update = Update.de_json(json.loads(body), app.bot)

            async def _process():
                await app.initialize()
                await app.process_update(update)

            asyncio.run(_process())
            self._send(200, "OK")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            self._send(200, "OK")

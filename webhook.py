import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ChatJoinRequestHandler, CommandHandler,
    ContextTypes, CallbackQueryHandler, MessageHandler, filters
)
from upstash_redis import Redis

# ------------------ CONFIG (Environment Variables) ------------------
BOT_TOKEN        = os.environ.get("BOT_TOKEN")
ADMIN_ID         = int(os.environ.get("ADMIN_ID", "8080371272"))
SOURCE_CHANNEL   = os.environ.get("SOURCE_CHANNEL", "@bablu922")
APK_MESSAGE_ID   = int(os.environ.get("APK_MESSAGE_ID", "3"))
VIDEO_MESSAGE_ID = int(os.environ.get("VIDEO_MESSAGE_ID", "2"))
VOICE_MESSAGE_ID = int(os.environ.get("VOICE_MESSAGE_ID", "4"))

VIP_CHANNEL_LINK  = "https://t.me/+SogkxdNWQyZkYzRl"
REGISTRATION_LINK = "https://www.shreewin34.com/#/register?invitationCode=64778100774"
LOSS_RECOVER_LINK = "t.me/lossrecoversure"

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://your-project.vercel.app/api/webhook

# Upstash Redis (users store karne ke liye)
redis = Redis(
    url=os.environ.get("UPSTASH_REDIS_REST_URL"),
    token=os.environ.get("UPSTASH_REDIS_REST_TOKEN")
)
USERS_KEY = "bot_users_set"

# ------------------ PREMIUM EMOJI IDs ------------------
EMOJI_VIDEO = "6147617184479711380"
EMOJI_APK   = "5767209624675553166"
EMOJI_VOICE = "6124902618574625426"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------ COLORED BUTTONS ------------------
VIDEO_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(text="VIP CHANNEL", url=VIP_CHANNEL_LINK,
            icon_custom_emoji_id=EMOJI_VIDEO, style="primary"),
        InlineKeyboardButton(text="LOSS RECOVER", url=LOSS_RECOVER_LINK,
            icon_custom_emoji_id=EMOJI_APK, style="danger")
    ],
    [
        InlineKeyboardButton(text="REGISTRATION LINK", url=REGISTRATION_LINK,
            icon_custom_emoji_id=EMOJI_VOICE, style="success")
    ]
])

APK_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="DM FOR LOSS RECOVERY", url=LOSS_RECOVER_LINK,
        icon_custom_emoji_id=EMOJI_APK, style="danger")]
])

VOICE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="Join VIP Now Limited Spots", url=VIP_CHANNEL_LINK,
        icon_custom_emoji_id=EMOJI_VIDEO, style="warning")]
])

START_MESSAGE = (
    "𝗛𝗘𝗟𝗟𝗢\n\n"
    "𝗔𝗔𝗣𝗞𝗜 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗝𝗔𝗟𝗗𝗜 𝗛𝗜 𝗔𝗣𝗣𝗥𝗢𝗩𝗘 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜 \n\n"
    "𝗦𝗘𝗧𝗨𝗣 𝗩𝗜𝗗𝗘𝗢 & 𝗛𝗔𝗖𝗞 𝗔𝗣𝗞 𝗡𝗘𝗘𝗖𝗛𝗘 𝗗𝗜𝗬𝗔 𝗚𝗔𝗬𝗔 𝗛𝗔𝗜"
)

# ------------------ USERS (Redis) ------------------
def add_user(user_id: int):
    try:
        redis.sadd(USERS_KEY, str(user_id))
    except Exception as e:
        logger.error(f"Redis add_user error: {e}")

def get_all_users():
    try:
        return redis.smembers(USERS_KEY) or []
    except Exception as e:
        logger.error(f"Redis get_all_users error: {e}")
        return []

def users_count():
    try:
        return redis.scard(USERS_KEY) or 0
    except Exception:
        return 0

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

    # Vercel 10s limit — sirf pehle 25 users per call
    # Bade broadcast ke liye background job (QStash) chahiye
    BATCH = 25
    batch = user_ids[:BATCH]

    sm = await update.message.reply_text(
        f"⏳ Sending {kind} to {len(batch)}/{total} users...\n"
        f"⚠️ Vercel 10s limit: sirf pehla batch abhi bhej rahe hain."
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
        f"✅ {kind.upper()} Batch Done\n"
        f"✅ Success: {success}\n❌ Failed: {failed}\n"
        f"📊 Total Users: {total}\n"
        f"⚠️ Remaining: {total - len(batch)} (QStash needed for full broadcast)"
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

# ------------------ BUILD APP (ek baar, module load pe) ------------------
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

# ------------------ VERCEL SERVERLESS HANDLER ------------------
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # /api/setup hit karne pe webhook set karega
        if self.path.startswith("/api/setup"):
            app = get_application()
            import asyncio
            async def _setup():
                await app.bot.delete_webhook(drop_pending_updates=True)
                await app.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
            asyncio.run(_setup())
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Webhook set successfully!")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", 0))
            body = self.rfile.read(length).decode("utf-8")
            update = Update.de_json(json.loads(body), get_application().bot)

            app = get_application()
            import asyncio
            asyncio.run(app.process_update(update))

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
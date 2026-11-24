import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@sayyadihashimu"

db = sqlite3.connect("referrals.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer INTEGER,
    joined INTEGER DEFAULT 0
)
""")
db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    ref = None
    if context.args:
        try:
            ref = int(context.args[0])
        except ValueError:
            pass

    existing = db.execute(
        "SELECT user_id FROM users WHERE user_id=?", (uid,)
    ).fetchone()

    if not existing:
        if ref == uid:
            ref = None

        db.execute(
            "INSERT INTO users (user_id, referrer) VALUES (?, ?)",
            (uid, ref)
        )
        db.commit()

    keyboard = [[InlineKeyboardButton(
        "✅ Na shiga Channel", callback_data="check"
    )]]

    await update.message.reply_text(
        "Barka da zuwa Sayyadi Hashimu Bot!\n\n"
        "Ka shiga channel ɗinmu sannan ka danna maɓallin tabbatarwa.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)

        if member.status not in ["member", "administrator", "creator"]:
            await query.message.reply_text(
                "❌ Ba ka shiga channel ba tukuna!"
            )
            return

        row = db.execute(
            "SELECT referrer, joined FROM users WHERE user_id=?",
            (uid,)
        ).fetchone()

        if row and row[1] == 0:
            referrer = row[0]

            db.execute(
                "UPDATE users SET joined=1 WHERE user_id=?", (uid,)
            )

            if referrer:
                db.execute(
                    "UPDATE users SET joined=joined+0 WHERE user_id=?",
                    (referrer,)
                )

            db.commit()

        await query.message.reply_text(
            "✅ An tabbatar da shiga channel!\n"
            "Na gode da kasancewa tare da mu."
        )

    except Exception:
        await query.message.reply_text(
            "An samu matsala. Ka tabbatar bot ɗin admin ne a channel."
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    total = db.execute(
        "SELECT COUNT(*) FROM users WHERE referrer=? AND joined=1",
        (uid,)
    ).fetchone()[0]

    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}?start={uid}"

    await update.message.reply_text(
        f"👥 Mutanen da ka gayyata: {total}\n\n"
        f"🔗 Link ɗinka:\n{link}"
    )

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(check, pattern="^check$"))

    print("Sayyadi Hashimu Bot yana aiki!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

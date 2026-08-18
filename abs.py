import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ==== تنظیمات ====
import os
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# مدل‌های قابل انتخاب
MODELS = {
    "gpt": "openrouter/free",
    "gemini": "google/gemma-3-27b-it:free",
    "llama": "meta-llama/llama-3.3-70b-instruct:free",
}

MODEL_NAMES = {
    "gpt": "خودکار (بهترین مدل رایگان موجود)",
    "gemini": "Gemma (رایگان)",
    "llama": "Llama (رایگان)",
}

user_model = {}
user_history = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(MODEL_NAMES["gpt"], callback_data="model_gpt")],
        [InlineKeyboardButton(MODEL_NAMES["gemini"], callback_data="model_gemini")],
        [InlineKeyboardButton(MODEL_NAMES["llama"], callback_data="model_llama")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! کدوم مدل رو می‌خوای استفاده کنی؟",
        reply_markup=reply_markup
    )


async def model_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chosen = query.data.replace("model_", "")
    user_id = query.from_user.id
    user_model[user_id] = chosen
    user_history[user_id] = []
    await query.edit_message_text(
        "مدل انتخاب شد: " + MODEL_NAMES[chosen] + "\n\nحالا هر چی می‌خوای بپرس!"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_model:
        await update.message.reply_text("اول با /start یه مدل انتخاب کن.")
        return

    model_key = user_model[user_id]
    model_id = MODELS[model_key]
    user_text = update.message.text

    await update.message.chat.send_action("typing")

    history = user_history.get(user_id, [])
    history.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=history,
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        user_history[user_id] = history[-20:]

        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("خطا: " + str(e))


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(model_choice, pattern="^model_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("ربات روشن شد...")
    app.run_polling()


if __name__ == "__main__":
    main()

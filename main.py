import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from openai import OpenAI
import argparse

load_dotenv()


TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")

parser = argparse.ArgumentParser()
parser.add_argument('--ai', choices=['openai', 'proxyapi'], default='openai', help='Выберите тип клиента AI')
args = parser.parse_args()

if args.ai == 'openai':
    client = OpenAI(api_key=OPENAI_API_KEY)
elif args.ai == 'proxyapi':
    client = OpenAI(api_key=PROXY_API_KEY, base_url="https://api.proxyapi.ru/openai/v1")
else:
    raise ValueError('Неизвестный AI клиент')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def ai_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    user_text = update.message.text
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": user_text
            }
        ]
    )
    ai_answer = completion.choices[0].message.content
    await update.message.reply_text(ai_answer)

if __name__ == '__main__':
    print('Bot is running...')

    app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_answer))

    app.run_polling()
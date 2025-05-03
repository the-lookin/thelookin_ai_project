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
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

user_threads = {}

parser = argparse.ArgumentParser()
parser.add_argument('--ai', choices=['openai', 'proxyapi'], default='openai', help='Выберите тип клиента AI')
args = parser.parse_args()

if args.ai == 'openai':
    client = OpenAI(api_key=OPENAI_API_KEY)
elif args.ai == 'proxyapi':
    client = OpenAI(api_key=PROXY_API_KEY, base_url="https://api.proxyapi.ru/openai/v1")
else:
    raise ValueError('Неизвестный AI клиент')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('''👋 Привет! Я твой персональный помощник по здоровому питанию. Задай любой вопрос: что есть на ужин, как питаться при тренировках,  какие продукты лучше исключить — я подскажу.''')

async def assistant_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user_id=update.effective_user.id
    message_text = update.message.text

    thread_id = user_threads.get(user_id)

    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
        user_threads[user_id] = thread_id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id, 
            run_id=run.id
        )

        if run.status == "completed":
            break
    
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    for msg in messages.data:
        if(msg.role == "assistant"):
            await update.message.reply_text(msg.content[0].text.value)
            break

    return

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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, assistant_answer))

    app.run_polling()
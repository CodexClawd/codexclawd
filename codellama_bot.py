#!/usr/bin/env python3
"""
CodeLlama Telegram Bot - Direct Ollama Integration
A separate bot that talks directly to local CodeLlama via Ollama API
"""

import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Bot Configuration
TELEGRAM_TOKEN = "8340926602:AAG1m3xfzbCSOcDj8ecVOMbR3WsqpZ5Mblc"
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "llama3.1:latest"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hey {user.first_name}! I'm Llama 3.1 Bot.\n\n"
        f"I run on local Llama 3.1 8B via Ollama.\n"
        f"Just send me any message and I'll respond!\n\n"
        f"⚡ Model: {MODEL}\n"
        f"🖥️  Running locally on this VPS"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await update.message.reply_text(
        "🤖 Llama 3.1 Bot Commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/status - Check if Ollama is running\n\n"
        "Just type any message to chat with Llama 3.1!"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Ollama status."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m['name'] for m in data.get('models', [])]
                    await update.message.reply_text(
                        f"✅ Ollama is running!\n\n"
                        f"Available models:\n" + "\n".join(f"• {m}" for m in models)
                    )
                else:
                    await update.message.reply_text("⚠️ Ollama returned error")
    except Exception as e:
        await update.message.reply_text(f"❌ Cannot connect to Ollama:\n{e}")


async def chat_with_codellama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages and get response from CodeLlama."""
    user_message = update.message.text
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant. Answer concisely and clearly."},
                    {"role": "user", "content": user_message}
                ],
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 2048
            }
            
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response = data['choices'][0]['message']['content']
                    
                    # Telegram has 4096 char limit per message
                    if len(response) > 4000:
                        response = response[:4000] + "\n\n... (truncated)"
                    
                    await update.message.reply_text(response)
                else:
                    error_text = await resp.text()
                    await update.message.reply_text(
                        f"❌ Ollama error (HTTP {resp.status}):\n{error_text[:500]}"
                    )
                    
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            f"❌ Error talking to Llama 3.1:\n```\n{e}\n```\n\n"
            f"Make sure Ollama is running:\n"
            f"`ollama serve`",
            parse_mode="Markdown"
        )


def main():
    """Start the bot."""
    print("🚀 Starting CodeLlama Bot...")
    print(f"   Model: {MODEL}")
    print(f"   Ollama: {OLLAMA_URL}")
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_codellama))
    
    # Run the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.getenv('6738226883:AAF7-qm-f56vQmQ_9qV5Mlu9evWVLy0SGwc')

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Send me a YouTube link!')

def download_video(url, quality):
    ydl_opts = {
        'format': quality,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info_dict)

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    keyboard = [
        [
            InlineKeyboardButton("360p", callback_data=f"{url} 18"),
            InlineKeyboardButton("720p", callback_data=f"{url} 22"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose the quality:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    url, quality = query.data.split()
    query.answer()
    file_path = download_video(url, quality)
    query.message.reply_text('Download complete! Uploading...')
    context.bot.send_document(chat_id=query.message.chat_id, document=open(file_path, 'rb'))
    os.remove(file_path)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

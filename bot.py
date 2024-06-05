import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from pytube import YouTube
from functools import wraps

# Define constants from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
FREE_USER_LIMIT = 1 * 1024 * 1024 * 1024  # 1 GB
PAID_USER_LIMIT = None  # Unlimited
FILE_SIZE_LIMIT = 2 * 1024 * 1024 * 1024  # 2 GB

# In-memory storage for users and their subscription status
users = {'free': [], 'paid': []}

# Decorator to restrict access to admin-only commands
def admin_only(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        if str(update.effective_user.id) == ADMIN_CHAT_ID:
            return func(update, context, *args, **kwargs)
        else:
            update.message.reply_text("You don't have permission to use this command.")
    return wrapped

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Send me a YouTube link to get started.')

def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    try:
        yt = YouTube(url)
        video_streams = yt.streams.filter(progressive=True, file_extension='mp4')
        
        buttons = []
        for stream in video_streams:
            button = InlineKeyboardButton(f'{stream.resolution} - {round(stream.filesize / (1024 * 1024), 2)} MB',
                                          callback_data=f'{stream.itag}')
            buttons.append([button])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text('Choose the quality:', reply_markup=reply_markup)
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    url = query.message.reply_to_message.text
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(query.data)
    
    if stream.filesize > FILE_SIZE_LIMIT:
        query.message.reply_text('File size exceeds 2 GB limit. Operation cancelled.')
        return

    user_id = str(query.from_user.id)
    if user_id in users['free']:
        if stream.filesize > FREE_USER_LIMIT:
            query.message.reply_text('File size exceeds your 1 GB limit. Consider upgrading to a paid plan.')
            return

    query.message.reply_text(f'Downloading {stream.resolution} video...')
    file_path = stream.download()
    query.message.reply_text(f'Download completed. Uploading...')
    query.message.reply_video(video=open(file_path, 'rb'))
    os.remove(file_path)

@admin_only
def add_paid_user(update: Update, context: CallbackContext):
    if context.args:
        user_id = context.args[0]
        users['paid'].append(user_id)
        update.message.reply_text(f'User {user_id} added to paid users.')
    else:
        update.message.reply_text('Please provide a user ID.')

@admin_only
def broadcast(update: Update, context: CallbackContext):
    if context.args:
        message = ' '.join(context.args)
        for user in users['free'] + users['paid']:
            try:
                context.bot.send_message(chat_id=user, text=message)
            except Exception as e:
                print(f"Could not send message to {user}: {e}")
    else:
        update.message.reply_text('Please provide a message to broadcast.')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))
    dp.add_handler(CallbackQueryHandler(button_callback))
    
    dp.add_handler(CommandHandler("add_paid_user", add_paid_user, pass_args=True))
    dp.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

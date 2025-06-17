import telebot
from telebot import types
import json
import os

BOT_TOKEN = '8114555757:AAG3YbjeJySRUZJqHyicKOFO0u1-AgxyMCI'  # 🔁 तपाईंको Bot Token राख्नुहोस्
ADMIN_ID = 6355673268  # 🔐 तपाईंको Telegram User ID

bot = telebot.TeleBot(BOT_TOKEN)

subjects = ['Science', 'Maths', 'Nepali', 'English', 'Social']
user_data = {}        # user_id -> data dict (private photos etc)
public_photos = {}    # subject -> list of file_ids
admin_upload_session = {}  # admin_id -> subject (currently uploading to)

DATA_FILE = "bot_data.json"

def save_data():
    data = {
        'user_data': user_data,
        'public_photos': public_photos
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_data():
    global user_data, public_photos
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            user_data = data.get('user_data', {})
            public_photos = data.get('public_photos', {})

def send_admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Export Data", "Delete All Data")
    markup.add("User Count", "Back")
    bot.send_message(chat_id, "🔧 Admin Panel:", reply_markup=markup)

def export_all_data(chat_id):
    try:
        with open(DATA_FILE, 'r') as f:
            data_text = f.read()
        # Send as text message for readability
        bot.send_message(chat_id, f"📤 Exported Data:\n<pre>{data_text}</pre>", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat_id, f"❌ Export Error: {e}")

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id

    if user_id == str(ADMIN_ID):
        send_admin_panel(chat_id)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for subject in subjects:
            markup.add(subject)
        markup.add("View Public Photos")
        bot.send_message(chat_id, "📸 फोटो पठाउनुहोस् वा विषय छान्नुहोस्:", reply_markup=markup)

@bot.message_handler(commands=['upload'])
def admin_upload_command(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    if user_id != str(ADMIN_ID):
        bot.send_message(chat_id, "❌ तपाईंलाई यो कामको अनुमति छैन।")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(chat_id, "❌ प्रयोग: /upload <subject>")
            return
        subject = parts[1]
        if subject not in subjects:
            bot.send_message(chat_id, "⚠️ मान्य विषय लेख्नुहोस्।")
            return
        admin_upload_session[user_id] = subject
        bot.send_message(chat_id, f"📤 अब '{subject}' को लागि सार्वजनिक फोटो पठाउनुहोस्।")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id

    # Admin uploading public photo
    if user_id == str(ADMIN_ID) and user_id in admin_upload_session:
        subject = admin_upload_session[user_id]
        if subject not in public_photos:
            public_photos[subject] = []
        public_photos[subject].append(file_id)
        bot.send_message(chat_id, f"✅ {subject} को लागि सार्वजनिक फोटो सफलतापूर्वक अपलोड भयो।")
        del admin_upload_session[user_id]
        save_data()
        return

    # Normal user flow (private photo)
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['last_photo'] = file_id
    save_data()
    bot.send_message(chat_id, "✅ फोटो सुरक्षित भयो। अब विषय छान्नुहोस्।")

@bot.message_handler(func=lambda message: True)
def text_message_handler(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    text = message.text

    # Admin commands/buttons
    if user_id == str(ADMIN_ID):
        if text == "Export Data":
            export_all_data(chat_id)
            return
        elif text == "User Count":
            count = len(user_data)
            bot.send_message(chat_id, f"👥 कुल प्रयोगकर्ता: {count}")
            return
        elif text == "Delete All Data":
            user_data.clear()
            public_photos.clear()
            save_data()
            bot.send_message(chat_id, "🗑️ सबै डेटा सफलतापूर्वक मेटियो।")
            return
        elif text == "Back":
            send_admin_panel(chat_id)
            return

    # Normal user buttons and flows
    if text == "View Public Photos":
        if not public_photos:
            bot.send_message(chat_id, "🚫 कुनै सार्वजनिक फोटो उपलब्ध छैन।")
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for s in public_photos:
            markup.add(s)
        markup.add("Back")
        bot.send_message(chat_id, "🔎 कुन विषयको सार्वजनिक फोटो हेर्न चाहनुहुन्छ?", reply_markup=markup)
        return

    if text == "Back":
        # Normal user back button: show subjects keyboard again
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for subject in subjects:
            markup.add(subject)
        markup.add("View Public Photos")
        bot.send_message(chat_id, "📸 विषय छान्नुहोस् वा फोटो पठाउनुहोस्:", reply_markup=markup)
        return

    # If user clicked a subject name (either from subjects list or public photos keys)
    if text in subjects:
        # Save user private photo if they sent before
        if user_id in user_data and 'last_photo' in user_data[user_id]:
            last_photo = user_data[user_id]['last_photo']
            if 'saved_photos' not in user_data[user_id]:
                user_data[user_id]['saved_photos'] = {}

            if text not in user_data[user_id]['saved_photos']:
                user_data[user_id]['saved_photos'][text] = []

            user_data[user_id]['saved_photos'][text].append(last_photo)
            del user_data[user_id]['last_photo']
            save_data()
            bot.send_message(chat_id, f"📚 '{text}' को फोटो सुरक्षित भयो:")
            bot.send_photo(chat_id, last_photo)
        else:
            # User did not send a photo just now
            bot.send_message(chat_id, f"📚 '{text}' विषयको सार्वजनिक फोटोहरू देखाउँदै...")

        # Show Admin द्वारा upload गरिएका public photos for that subject (if any)
        if text in public_photos and public_photos[text]:
            bot.send_message(chat_id, f"🌐 '{text}' का सार्वजनिक फोटोहरू:")
            for file_id in public_photos[text]:
                bot.send_photo(chat_id, file_id)
        else:
            bot.send_message(chat_id, f"🚫 '{text}' विषयमा सार्वजनिक फोटो उपलब्ध छैन।")

        return

    # If user clicked one of the public photo subjects to view photos (from "View Public Photos" menu)
    if text in public_photos:
        bot.send_message(chat_id, f"🌐 '{text}' का सार्वजनिक फोटोहरू:")
        for file_id in public_photos[text]:
            bot.send_photo(chat_id, file_id)
        return

    # Unknown message
    bot.send_message(chat_id, "⚠️ कृपया मान्य विकल्प छान्नुहोस् वा /start लेख्नुहोस्।")

# Load saved data on start
load_data()

print("Bot running...")
bot.infinity_polling()

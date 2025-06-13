import os
os.makedirs("downloads", exist_ok=True)
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("7949313597:AAE-Eyl31mY7JfXWvxVbNuN10FxfljMGRLE")
bot = telebot.TeleBot(BOT_TOKEN)

# Store search queries, page info, and message IDs for each user
user_searches = {}
user_video_searches = {}

keep_alive()  # Start Flask keep-alive server

@bot.message_handler(commands=['start'])
def start_command(message):
    help_text = """🎵 Welcome to Music & Video Downloader Bot! 🎬

Here are all the commands you can use:

🔹 /song <song name>
   Search and download songs as MP3
   Example: /song Shape of You

🔹 /vid <video name>
   Search and download videos with quality selection
   Example: /vid funny cat videos

🔹 /yt <youtube_link>
   Download directly from YouTube links
   • Works with regular YouTube videos
   • Works with YouTube Shorts
   • Choose between MP3 (audio) or MP4 (video)
   Example: /yt https://youtube.com/watch?v=abc123

📱 How it works:
1. Send a command with your search term or YouTube link
2. Choose from search results (for /song and /vid)
3. Select format and quality options
4. Get your downloaded file!

🎯 Tips:
• Use 360p for videos - it's fast and stable
• YouTube Shorts download automatically in best quality
• All downloads are in high quality MP3/MP4 format

Enjoy downloading! 🚀"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['song'])
def song_search(message):
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❗ Please type a song name after /song.")
        return

    user_id = message.from_user.id
    user_searches[user_id] = {'query': query, 'page': 0, 'search_message_id': None, 'type': 'audio'}

    search_and_display(message, query, 0, content_type='audio')

@bot.message_handler(commands=['vid'])
def video_search(message):
    query = message.text[5:].strip()
    if not query:
        bot.reply_to(message, "❗ Please type a video name after /vid.")
        return

    user_id = message.from_user.id
    user_video_searches[user_id] = {'query': query, 'page': 0, 'search_message_id': None, 'type': 'video'}

    search_and_display(message, query, 0, content_type='video')

@bot.message_handler(commands=['yt'])
def youtube_link_handler(message):
    link = message.text[4:].strip()
    if not link:
        bot.reply_to(message, "❗ Please provide a YouTube link after /yt.")
        return

    # Validate if it's a YouTube link (including Shorts)
    if not ("youtube.com/watch" in link or "youtu.be/" in link or "youtube.com/shorts/" in link):
        bot.reply_to(message, "❗ Please provide a valid YouTube link (regular videos or Shorts).")
        return

    user_id = message.from_user.id
    is_shorts = "youtube.com/shorts/" in link

    # Extract video ID from the link
    try:
        if "youtu.be/" in link:
            video_id = link.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/watch" in link:
            video_id = link.split("v=")[1].split("&")[0]
        elif "youtube.com/shorts/" in link:
            video_id = link.split("youtube.com/shorts/")[1].split("?")[0]
        else:
            bot.reply_to(message, "❗ Invalid YouTube link format.")
            return
    except:
        bot.reply_to(message, "❗ Could not extract video ID from the link.")
        return

    # Show format selection buttons
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎵 Download as Song (MP3)", callback_data=f"yt_audio_{video_id}"))

    # For Shorts, use direct download; for normal videos, use quality selection
    if is_shorts:
        markup.add(InlineKeyboardButton("🎬 Download as Video (Auto Quality)", callback_data=f"yt_shorts_{video_id}"))
        message_text = "📥 Choose download format:\n🩳 YouTube Shorts detected! Video will download in best available quality."
    else:
        markup.add(InlineKeyboardButton("🎬 Download as Video", callback_data=f"yt_video_{video_id}"))
        message_text = "📥 Choose download format:\n🎬 You can select video quality for regular YouTube videos!"

    markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

    bot.send_message(message.chat.id, message_text, reply_markup=markup)

def search_and_display(message, query, page, chat_id=None, user_id=None, content_type='audio'):
    target_chat_id = chat_id if chat_id else message.chat.id
    target_user_id = user_id if user_id else message.from_user.id

    searches_dict = user_searches if content_type == 'audio' else user_video_searches
    search_message_id = searches_dict.get(target_user_id, {}).get('search_message_id')

    content_emoji = "🎧" if content_type == 'audio' else "🎬"
    content_name = "song" if content_type == 'audio' else "video"

    if search_message_id:
        try:
            bot.edit_message_text(f"🔍 Searching for `{query}` (Page {page + 1})...", 
                                target_chat_id, search_message_id, parse_mode='Markdown')
        except:
            search_msg = bot.send_message(target_chat_id, f"🔍 Searching for `{query}` (Page {page + 1})...", parse_mode='Markdown')
            searches_dict[target_user_id]['search_message_id'] = search_msg.message_id
    else:
        search_msg = bot.send_message(target_chat_id, f"🔍 Searching for `{query}` (Page {page + 1})...", parse_mode='Markdown')
        if target_user_id in searches_dict:
            searches_dict[target_user_id]['search_message_id'] = search_msg.message_id

    try:
        ydl_opts_search = {
            'quiet': True,
            'extract_flat': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            results = ydl.extract_info(f"ytsearch20:{query}", download=False)['entries']
    except Exception as e:
        error_msg = f"❌ Search failed: {str(e)}"
        search_message_id = searches_dict.get(target_user_id, {}).get('search_message_id')
        if search_message_id:
            try:
                bot.edit_message_text(error_msg, target_chat_id, search_message_id)
            except:
                bot.send_message(target_chat_id, error_msg)
        else:
            bot.send_message(target_chat_id, error_msg)
        return

    results_per_page = 5
    start_idx = page * results_per_page
    end_idx = start_idx + results_per_page
    page_results = results[start_idx:end_idx]

    if not page_results:
        error_msg = "❌ No more results found."
        search_message_id = searches_dict.get(target_user_id, {}).get('search_message_id')
        if search_message_id:
            try:
                bot.edit_message_text(error_msg, target_chat_id, search_message_id)
            except:
                bot.send_message(target_chat_id, error_msg)
        else:
            bot.send_message(target_chat_id, error_msg)
        return

    markup = InlineKeyboardMarkup()
    for video in page_results:
        title = video.get("title", "No Title")
        video_id = video.get("id")
        callback_prefix = "dl_" if content_type == 'audio' else "vid_"
        markup.add(InlineKeyboardButton(title, callback_data=f"{callback_prefix}{video_id}"))

    if len(results) > end_idx and page < 3:
        next_callback = f"next_{page + 1}" if content_type == 'audio' else f"vnext_{page + 1}"
        markup.add(InlineKeyboardButton("➡️ Next", callback_data=next_callback))

    cancel_callback = f"cancel_{target_user_id}" if content_type == 'audio' else f"vcancel_{target_user_id}"
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data=cancel_callback))

    search_message_id = searches_dict.get(target_user_id, {}).get('search_message_id')
    if search_message_id:
        try:
            bot.edit_message_text(f"{content_emoji} Choose a {content_name} to download (Page {page + 1}):", 
                                target_chat_id, search_message_id, reply_markup=markup)
        except:
            results_msg = bot.send_message(target_chat_id, f"{content_emoji} Choose a {content_name} to download (Page {page + 1}):", reply_markup=markup)
            searches_dict[target_user_id]['search_message_id'] = results_msg.message_id
    else:
        results_msg = bot.send_message(target_chat_id, f"{content_emoji} Choose a {content_name} to download (Page {page + 1}):", reply_markup=markup)
        if target_user_id in searches_dict:
            searches_dict[target_user_id]['search_message_id'] = results_msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("next_"))
def handle_next_page(call):
    user_id = call.from_user.id
    page = int(call.data[5:])

    if user_id not in user_searches:
        bot.answer_callback_query(call.id, "❌ Search session expired. Please start a new search.")
        return

    query = user_searches[user_id]['query']
    user_searches[user_id]['page'] = page

    search_and_display(None, query, page, call.message.chat.id, user_id, 'audio')

@bot.callback_query_handler(func=lambda call: call.data.startswith("vnext_"))
def handle_video_next_page(call):
    user_id = call.from_user.id
    page = int(call.data[6:])

    if user_id not in user_video_searches:
        bot.answer_callback_query(call.id, "❌ Search session expired. Please start a new search.")
        return

    query = user_video_searches[user_id]['query']
    user_video_searches[user_id]['page'] = page

    search_and_display(None, query, page, call.message.chat.id, user_id, 'video')

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def handle_cancel(call):
    user_id = call.from_user.id

    if user_id in user_searches:
        search_message_id = user_searches[user_id].get('search_message_id')
        if search_message_id:
            try:
                bot.delete_message(call.message.chat.id, search_message_id)
            except:
                pass
        del user_searches[user_id]

    user_link = f"[{call.from_user.first_name}](tg://user?id={user_id})"
    bot.send_message(call.message.chat.id, f"{user_link} cancelled the search results.", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith("vcancel_"))
def handle_video_cancel(call):
    user_id = call.from_user.id

    if user_id in user_video_searches:
        search_message_id = user_video_searches[user_id].get('search_message_id')
        if search_message_id:
            try:
                bot.delete_message(call.message.chat.id, search_message_id)
            except:
                pass
        del user_video_searches[user_id]

    user_link = f"[{call.from_user.first_name}](tg://user?id={user_id})"
    bot.send_message(call.message.chat.id, f"{user_link} cancelled the video search results.", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith("vid_"))
def handle_video_info_display(call):
    user_id = call.from_user.id
    video_id = call.data[4:]
    
    if user_id in user_video_searches:
        search_message_id = user_video_searches[user_id].get('search_message_id')
        if search_message_id:
            try:
                bot.delete_message(call.message.chat.id, search_message_id)
            except:
                pass

    # Show loading message
    loading_msg = bot.send_message(call.message.chat.id, "🔍 Fetching video details...")
    
    try:
        # Get video info
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown Title')
            channel = info.get('uploader', 'Unknown Channel')
            view_count = info.get('view_count', 0)
            like_count = info.get('like_count', 0)
            upload_date = info.get('upload_date', '')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            
            # Format numbers
            if view_count >= 1000000:
                views_str = f"{view_count/1000000:.1f}M"
            elif view_count >= 1000:
                views_str = f"{view_count/1000:.1f}K"
            else:
                views_str = str(view_count)
                
            if like_count >= 1000000:
                likes_str = f"{like_count/1000000:.1f}M"
            elif like_count >= 1000:
                likes_str = f"{like_count/1000:.1f}K"
            else:
                likes_str = str(like_count)
            
            # Format upload date
            if upload_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(upload_date, '%Y%m%d')
                    formatted_date = date_obj.strftime('%b %d, %Y')
                except:
                    formatted_date = upload_date
            else:
                formatted_date = "Unknown"
                
            # Format duration
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Unknown"
        
        # Create info message
        info_text = f"""🎬 **{title}**

📺 **Channel:** {channel}
👀 **Views:** {views_str}
👍 **Likes:** {likes_str}
📅 **Uploaded:** {formatted_date}
⏱️ **Duration:** {duration_str}

Do you want to download this video?"""

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Yes, Download", callback_data=f"confirm_vid_{video_id}"))
        markup.add(InlineKeyboardButton("❌ No, Choose Another", callback_data=f"back_vid_{user_id}"))
        
        # Delete loading message and send video info with thumbnail
        bot.delete_message(call.message.chat.id, loading_msg.message_id)
        
        if thumbnail:
            bot.send_photo(
                call.message.chat.id,
                thumbnail,
                caption=info_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                call.message.chat.id,
                info_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ Error fetching video details: {str(e)}",
            call.message.chat.id,
            loading_msg.message_id
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("quality_"))
def handle_video_download(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    video_id = parts[1]
    quality = parts[2]
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Edit the quality selection message to show checking
    try:
        bot.edit_message_text(
            f"🔍 Checking availability for {quality}p...", 
            call.message.chat.id, 
            call.message.message_id
        )
    except:
        pass

    try:
        # First check available formats thoroughly
        check_opts = {
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(check_opts) as ydl:
            info_check = ydl.extract_info(url, download=False)
            formats = info_check.get('formats', [])

            # Get available video qualities (excluding audio-only)
            available_qualities = []
            video_formats = {}

            for fmt in formats:
                height = fmt.get('height')
                vcodec = fmt.get('vcodec', 'none')
                if height and vcodec != 'none' and 'video only' in str(fmt.get('format_note', '')):
                    available_qualities.append(height)
                    if height not in video_formats:
                        video_formats[height] = fmt

            # Remove duplicates and sort
            available_qualities = sorted(list(set(available_qualities)))
            requested_height = int(quality)

            # Check if requested quality is available
            if available_qualities and requested_height not in available_qualities:
                # Find closest available quality
                closest_quality = min(available_qualities, key=lambda x: abs(x - requested_height))

                markup = InlineKeyboardMarkup()

                # Add buttons for available qualities in a user-friendly way
                for qual in available_qualities:
                    if qual == closest_quality:
                        button_text = f"✅ {qual}p (Best Match)"
                    elif qual == 360:
                        button_text = f"🔥 {qual}p (Recommended)" 
                    elif qual <= 240:
                        button_text = f"📱 {qual}p (Fast)"
                    elif qual >= 720:
                        button_text = f"🎬 {qual}p (HD)"
                    else:
                        button_text = f"📺 {qual}p"

                    markup.add(InlineKeyboardButton(button_text, callback_data=f"quality_{video_id}_{qual}"))

                markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"vcancel_{user_id}"))

                bot.edit_message_text(
                    f"😔 Oops! {quality}p is not available for this video.\n\n🎯 But don't worry! Here are the qualities you can choose:\n\n👇 Please select one of the options below:", 
                    call.message.chat.id, 
                    call.message.message_id,
                    reply_markup=markup
                )
                return

        # Quality is available, proceed with download
        bot.edit_message_text(
            f"🔍 Preparing {quality}p download...", 
            call.message.chat.id, 
            call.message.message_id
        )

        if user_id in user_video_searches:
            del user_video_searches[user_id]

        def video_progress_hook(d):
            try:
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', 'N/A')
                    speed = d.get('_speed_str', 'N/A')
                    bot.edit_message_text(f"⬇️ Downloading {quality}p: {percent} | Speed: {speed}", call.message.chat.id, call.message.message_id)
                elif d['status'] == 'finished':
                    bot.edit_message_text(f"🔄 Processing {quality}p video...", call.message.chat.id, call.message.message_id)
            except:
                pass

        # More precise quality formats that ensure exact quality match
        requested_height = int(quality)

        # Build format selector that prioritizes exact height match
        format_selector = f"best[height={requested_height}][ext=mp4]/best[height={requested_height}]"

        # Add fallback only if exact match fails
        if requested_height <= 144:
            format_selector += "/best[height<=144][ext=mp4]/best[height<=144]"
        elif requested_height <= 240:
            format_selector += "/best[height<=240][ext=mp4]/best[height<=240]"
        elif requested_height <= 360:
            format_selector += "/best[height<=360][ext=mp4]/best[height<=360]"
        elif requested_height <= 480:
            format_selector += "/best[height<=480][ext=mp4]/best[height<=480]"
        elif requested_height <= 720:
            format_selector += "/best[height<=720][ext=mp4]/best[height<=720]"
        else:
            format_selector += "/best[ext=mp4]/best"

        ydl_opts = {
            'format': format_selector,
            'outtmpl': 'downloads/%(title)s_%(height)sp.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [video_progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Ensure mp4 extension
            base_path = os.path.splitext(file_path)[0]
            mp4_path = base_path + '.mp4'

            # Check which file exists
            if os.path.exists(mp4_path):
                file_path = mp4_path
            elif not os.path.exists(file_path):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_path = base_path + ext
                    if os.path.exists(test_path):
                        file_path = test_path
                        break

        # Get actual downloaded quality and file size
        actual_height = info.get('height', 'Unknown')
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # Check if we got the requested quality
        quality_status = ""
        if actual_height != "Unknown" and actual_height != requested_height:
            quality_status = f"\n⚠️ Note: Downloaded in {actual_height}p (requested {quality}p was not available)"

        # Update message with file info
        bot.edit_message_text(
            f"📤 Uploading video ({actual_height}p)...\n📁 Size: {file_size_mb:.1f} MB{quality_status}", 
            call.message.chat.id, call.message.message_id
        )

        with open(file_path, 'rb') as f:
            # Send video with streaming support and metadata
            bot.send_video(
                call.message.chat.id, 
                f, 
                caption=f"🎬 {info['title']} ({actual_height}p)",
                supports_streaming=True,
                duration=info.get('duration'),
                width=info.get('width'),
                height=info.get('height')
            )

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        # Show quality selection again when download fails
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("144p", callback_data=f"quality_{video_id}_144"))
        markup.add(InlineKeyboardButton("240p", callback_data=f"quality_{video_id}_240"))
        markup.add(InlineKeyboardButton("360p ⭐ (Recommended)", callback_data=f"quality_{video_id}_360"))
        markup.add(InlineKeyboardButton("480p", callback_data=f"quality_{video_id}_480"))
        markup.add(InlineKeyboardButton("720p", callback_data=f"quality_{video_id}_720"))
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"vcancel_{user_id}"))

        bot.edit_message_text(
            f"❌ Download failed! Please try a different quality.\n\n📹 Select video quality again:", 
            call.message.chat.id, 
            call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_audio_"))
def handle_yt_audio_download(call):
    user_id = call.from_user.id
    video_id = call.data[9:]  # Remove "yt_audio_" prefix
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Edit the format selection message
    try:
        bot.edit_message_text("🔍 Fetching YouTube audio info...", 
                            call.message.chat.id, call.message.message_id)
    except:
        pass

    msg = bot.send_message(call.message.chat.id, "🔍 Preparing audio download...")

    def yt_audio_progress_hook(d):
        try:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                bot.edit_message_text(f"⬇️ Downloading audio: {percent} | Speed: {speed}", call.message.chat.id, msg.message_id)
            elif d['status'] == 'finished':
                bot.edit_message_text("🎵 Converting to MP3...", call.message.chat.id, msg.message_id)
        except:
            pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'progress_hooks': [yt_audio_progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(base_filename)[0] + '.mp3'

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        bot.edit_message_text(f"📤 Uploading MP3 ({file_size_mb:.1f} MB)...", call.message.chat.id, msg.message_id)

        with open(file_path, 'rb') as f:
            bot.send_audio(call.message.chat.id, f, title=info['title'])

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, msg.message_id)

        # Delete the format selection message
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    except Exception as e:
        bot.edit_message_text(f"❌ Error downloading audio: {str(e)}", call.message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_video_"))
def handle_yt_video_selection(call):
    user_id = call.from_user.id
    video_id = call.data[9:]  # Remove "yt_video_" prefix

    # Delete the format selection message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    # Show quality selection (same as /vid command)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("144p", callback_data=f"yt_quality_{video_id}_144"))
    markup.add(InlineKeyboardButton("240p", callback_data=f"yt_quality_{video_id}_240"))
    markup.add(InlineKeyboardButton("360p ⭐ (Recommended)", callback_data=f"yt_quality_{video_id}_360"))
    markup.add(InlineKeyboardButton("480p", callback_data=f"yt_quality_{video_id}_480"))
    markup.add(InlineKeyboardButton("720p", callback_data=f"yt_quality_{video_id}_720"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

    bot.send_message(call.message.chat.id, "📹 Select video quality:\n💡 360p is good and more stable", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_quality_"))
def handle_yt_video_download(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    video_id = parts[2]  # yt_quality_VIDEO_ID_QUALITY
    quality = parts[3]
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Edit the quality selection message to show checking
    try:
        bot.edit_message_text(
            f"🔍 Checking availability for {quality}p...", 
            call.message.chat.id, 
            call.message.message_id
        )
    except:
        pass

    try:
        # First check available formats thoroughly
        check_opts = {
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(check_opts) as ydl:
            info_check = ydl.extract_info(url, download=False)
            formats = info_check.get('formats', [])

            # Get available video qualities (excluding audio-only)
            available_qualities = []
            video_formats = {}

            for fmt in formats:
                height = fmt.get('height')
                vcodec = fmt.get('vcodec', 'none')
                if height and vcodec != 'none' and 'video only' in str(fmt.get('format_note', '')):
                    available_qualities.append(height)
                    if height not in video_formats:
                        video_formats[height] = fmt

            # Remove duplicates and sort
            available_qualities = sorted(list(set(available_qualities)))
            requested_height = int(quality)

            # Check if requested quality is available
            if available_qualities and requested_height not in available_qualities:
                # Find closest available quality
                closest_quality = min(available_qualities, key=lambda x: abs(x - requested_height))

                markup = InlineKeyboardMarkup()

                # Add buttons for available qualities in a user-friendly way
                for qual in available_qualities:
                    if qual == closest_quality:
                        button_text = f"✅ {qual}p (Best Match)"
                    elif qual == 360:
                        button_text = f"🔥 {qual}p (Recommended)" 
                    elif qual <= 240:
                        button_text = f"📱 {qual}p (Fast)"
                    elif qual >= 720:
                        button_text = f"🎬 {qual}p (HD)"
                    else:
                        button_text = f"📺 {qual}p"

                    markup.add(InlineKeyboardButton(button_text, callback_data=f"yt_quality_{video_id}_{qual}"))

                markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

                bot.edit_message_text(
                    f"😔 Oops! {quality}p is not available for this video.\n\n🎯 But don't worry! Here are the qualities you can choose:\n\n👇 Please select one of the options below:", 
                    call.message.chat.id, 
                    call.message.message_id,
                    reply_markup=markup
                )
                return

        # Quality is available, proceed with download
        bot.edit_message_text(
            f"🔍 Preparing {quality}p download...", 
            call.message.chat.id, 
            call.message.message_id
        )

        def yt_video_progress_hook(d):
            try:
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', 'N/A')
                    speed = d.get('_speed_str', 'N/A')
                    bot.edit_message_text(f"⬇️ Downloading {quality}p: {percent} | Speed: {speed}", call.message.chat.id, call.message.message_id)
                elif d['status'] == 'finished':
                    bot.edit_message_text(f"🔄 Processing {quality}p video...", call.message.chat.id, call.message.message_id)
            except:
                pass

        # More precise quality formats that ensure exact quality match
        requested_height = int(quality)

        # Build format selector that prioritizes exact height match
        format_selector = f"best[height={requested_height}][ext=mp4]/best[height={requested_height}]"

        # Add fallback only if exact match fails
        if requested_height <= 144:
            format_selector += "/best[height<=144][ext=mp4]/best[height<=144]"
        elif requested_height <= 240:
            format_selector += "/best[height<=240][ext=mp4]/best[height<=240]"
        elif requested_height <= 360:
            format_selector += "/best[height<=360][ext=mp4]/best[height<=360]"
        elif requested_height <= 480:
            format_selector += "/best[height<=480][ext=mp4]/best[height<=480]"
        elif requested_height <= 720:
            format_selector += "/best[height<=720][ext=mp4]/best[height<=720]"
        else:
            format_selector += "/best[ext=mp4]/best"

        ydl_opts = {
            'format': format_selector,
            'outtmpl': 'downloads/%(title)s_%(height)sp.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [yt_video_progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Ensure mp4 extension
            base_path = os.path.splitext(file_path)[0]
            mp4_path = base_path + '.mp4'

            # Check which file exists
            if os.path.exists(mp4_path):
                file_path = mp4_path
            elif not os.path.exists(file_path):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_path = base_path + ext
                    if os.path.exists(test_path):
                        file_path = test_path
                        break

        # Get actual downloaded quality and file size
        actual_height = info.get('height', 'Unknown')
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # Check if we got the requested quality
        quality_status = ""
        if actual_height != "Unknown" and actual_height != requested_height:
            quality_status = f"\n⚠️ Note: Downloaded in {actual_height}p (requested {quality}p was not available)"

        # Update message with file info
        bot.edit_message_text(
            f"📤 Uploading video ({actual_height}p)...\n📁 Size: {file_size_mb:.1f} MB{quality_status}", 
            call.message.chat.id, call.message.message_id
        )

        with open(file_path, 'rb') as f:
            # Send video with streaming support and metadata
            bot.send_video(
                call.message.chat.id, 
                f, 
                caption=f"🎬 {info['title']} ({actual_height}p)",
                supports_streaming=True,
                duration=info.get('duration'),
                width=info.get('width'),
                height=info.get('height')
            )

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        # Show quality selection again when download fails
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("144p", callback_data=f"yt_quality_{video_id}_144"))
        markup.add(InlineKeyboardButton("240p", callback_data=f"yt_quality_{video_id}_240"))
        markup.add(InlineKeyboardButton("360p ⭐ (Recommended)", callback_data=f"yt_quality_{video_id}_360"))
        markup.add(InlineKeyboardButton("480p", callback_data=f"yt_quality_{video_id}_480"))
        markup.add(InlineKeyboardButton("720p", callback_data=f"yt_quality_{video_id}_720"))
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

        bot.edit_message_text(
            f"❌ Download failed! Please try a different quality.\n\n📹 Select video quality again:", 
            call.message.chat.id, 
            call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_audio_"))
def handle_yt_audio_download(call):
    user_id = call.from_user.id
    video_id = call.data[9:]  # Remove "yt_audio_" prefix
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Edit the format selection message
    try:
        bot.edit_message_text("🔍 Fetching YouTube audio info...", 
                            call.message.chat.id, call.message.message_id)
    except:
        pass

    msg = bot.send_message(call.message.chat.id, "🔍 Preparing audio download...")

    def yt_audio_progress_hook(d):
        try:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                bot.edit_message_text(f"⬇️ Downloading audio: {percent} | Speed: {speed}", call.message.chat.id, msg.message_id)
            elif d['status'] == 'finished':
                bot.edit_message_text("🎵 Converting to MP3...", call.message.chat.id, msg.message_id)
        except:
            pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'progress_hooks': [yt_audio_progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(base_filename)[0] + '.mp3'

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        bot.edit_message_text(f"📤 Uploading MP3 ({file_size_mb:.1f} MB)...", call.message.chat.id, msg.message_id)

        with open(file_path, 'rb') as f:
            bot.send_audio(call.message.chat.id, f, title=info['title'])

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, msg.message_id)

        # Delete the format selection message
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    except Exception as e:
        bot.edit_message_text(f"❌ Error downloading audio: {str(e)}", call.message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_video_"))
def handle_yt_video_selection(call):
    user_id = call.from_user.id
    video_id = call.data[9:]  # Remove "yt_video_" prefix

    # Delete the format selection message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    # Show quality selection (same as /vid command)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("144p", callback_data=f"yt_quality_{video_id}_144"))
    markup.add(InlineKeyboardButton("240p", callback_data=f"yt_quality_{video_id}_240"))
    markup.add(InlineKeyboardButton("360p ⭐ (Recommended)", callback_data=f"yt_quality_{video_id}_360"))
    markup.add(InlineKeyboardButton("480p", callback_data=f"yt_quality_{video_id}_480"))
    markup.add(InlineKeyboardButton("720p", callback_data=f"yt_quality_{video_id}_720"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

    bot.send_message(call.message.chat.id, "📹 Select video quality:\n💡 360p is good and more stable", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_quality_"))
def handle_yt_video_download(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    video_id = parts[2]  # yt_quality_VIDEO_ID_QUALITY
    quality = parts[3]
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Edit the quality selection message to show checking
    try:
        bot.edit_message_text(
            f"🔍 Checking availability for {quality}p...", 
            call.message.chat.id, 
            call.message.message_id
        )
    except:
        pass

    try:
        # First check available formats thoroughly
        check_opts = {
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(check_opts) as ydl:
            info_check = ydl.extract_info(url, download=False)
            formats = info_check.get('formats', [])

            # Get available video qualities (excluding audio-only)
            available_qualities = []
            video_formats = {}

            for fmt in formats:
                height = fmt.get('height')
                vcodec = fmt.get('vcodec', 'none')
                if height and vcodec != 'none' and 'video only' in str(fmt.get('format_note', '')):
                    available_qualities.append(height)
                    if height not in video_formats:
                        video_formats[height] = fmt

            # Remove duplicates and sort
            available_qualities = sorted(list(set(available_qualities)))
            requested_height = int(quality)

            # Check if requested quality is available
            if available_qualities and requested_height not in available_qualities:
                # Find closest available quality
                closest_quality = min(available_qualities, key=lambda x: abs(x - requested_height))

                markup = InlineKeyboardMarkup()

                # Add buttons for available qualities in a user-friendly way
                for qual in available_qualities:
                    if qual == closest_quality:
                        button_text = f"✅ {qual}p (Best Match)"
                    elif qual == 360:
                        button_text = f"🔥 {qual}p (Recommended)" 
                    elif qual <= 240:
                        button_text = f"📱 {qual}p (Fast)"
                    elif qual >= 720:
                        button_text = f"🎬 {qual}p (HD)"
                    else:
                        button_text = f"📺 {qual}p"

                    markup.add(InlineKeyboardButton(button_text, callback_data=f"yt_quality_{video_id}_{qual}"))

                markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

                bot.edit_message_text(
                    f"😔 Oops! {quality}p is not available for this video.\n\n🎯 But don't worry! Here are the qualities you can choose:\n\n👇 Please select one of the options below:", 
                    call.message.chat.id, 
                    call.message.message_id,
                    reply_markup=markup
                )
                return

        # Quality is available, proceed with download
        bot.edit_message_text(
            f"🔍 Preparing {quality}p download...", 
            call.message.chat.id, 
            call.message.message_id
        )

        def yt_video_progress_hook(d):
            try:
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', 'N/A')
                    speed = d.get('_speed_str', 'N/A')
                    bot.edit_message_text(f"⬇️ Downloading {quality}p: {percent} | Speed: {speed}", call.message.chat.id, call.message.message_id)
                elif d['status'] == 'finished':
                    bot.edit_message_text(f"🔄 Processing {quality}p video...", call.message.chat.id, call.message.message_id)
            except:
                pass

        # More precise quality formats that ensure exact quality match
        requested_height = int(quality)

        # Build format selector that prioritizes exact height match
        format_selector = f"best[height={requested_height}][ext=mp4]/best[height={requested_height}]"

        # Add fallback only if exact match fails
        if requested_height <= 144:
            format_selector += "/best[height<=144][ext=mp4]/best[height<=144]"
        elif requested_height <= 240:
            format_selector += "/best[height<=240][ext=mp4]/best[height<=240]"
        elif requested_height <= 360:
            format_selector += "/best[height<=360][ext=mp4]/best[height<=360]"
        elif requested_height <= 480:
            format_selector += "/best[height<=480][ext=mp4]/best[height<=480]"
        elif requested_height <= 720:
            format_selector += "/best[height<=720][ext=mp4]/best[height<=720]"
        else:
            format_selector += "/best[ext=mp4]/best"

        ydl_opts = {
            'format': format_selector,
            'outtmpl': 'downloads/%(title)s_%(height)sp.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [yt_video_progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Ensure mp4 extension
            base_path = os.path.splitext(file_path)[0]
            mp4_path = base_path + '.mp4'

            # Check which file exists
            if os.path.exists(mp4_path):
                file_path = mp4_path
            elif not os.path.exists(file_path):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_path = base_path + ext
                    if os.path.exists(test_path):
                        file_path = test_path
                        break

        # Get actual downloaded quality and file size
        actual_height = info.get('height', 'Unknown')
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # Check if we got the requested quality
        quality_status = ""
        if actual_height != "Unknown" and actual_height != requested_height:
            quality_status = f"\n⚠️ Note: Downloaded in {actual_height}p (requested {quality}p was not available)"

        # Update message with file info
        bot.edit_message_text(
            f"📤 Uploading video ({actual_height}p)...\n📁 Size: {file_size_mb:.1f} MB{quality_status}", 
            call.message.chat.id, call.message.message_id
        )

        with open(file_path, 'rb') as f:
            # Send video with streaming support and metadata
            bot.send_video(
                call.message.chat.id, 
                f, 
                caption=f"🎬 {info['title']} ({actual_height}p)",
                supports_streaming=True,
                duration=info.get('duration'),
                width=info.get('width'),
                height=info.get('height')
            )

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        # Show quality selection again when download fails
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("144p", callback_data=f"yt_quality_{video_id}_144"))
        markup.add(InlineKeyboardButton("240p", callback_data=f"yt_quality_{video_id}_240"))
        markup.add(InlineKeyboardButton("360p ⭐ (Recommended)", callback_data=f"yt_quality_{video_id}_360"))
        markup.add(InlineKeyboardButton("480p", callback_data=f"yt_quality_{video_id}_480"))
        markup.add(InlineKeyboardButton("720p", callback_data=f"yt_quality_{video_id}_720"))
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel_{user_id}"))

        bot.edit_message_text(
            f"❌ Download failed! Please try a different quality.\n\n📹 Select video quality again:", 
            call.message.chat.id, 
            call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_shorts_"))
def handle_yt_shorts_download(call):
    user_id = call.from_user.id
    video_id = call.data[10:]  # Remove "yt_shorts_" prefix
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Edit the format selection message
    try:
        bot.edit_message_text("🔍 Preparing YouTube Shorts download...", 
                            call.message.chat.id, call.message.message_id)
    except:
        pass

    def shorts_progress_hook(d):
        try:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                bot.edit_message_text(f"⬇️ Downloading Shorts: {percent} | Speed: {speed}", call.message.chat.id, call.message.message_id)
            elif d['status'] == 'finished':
                bot.edit_message_text("🔄 Processing Shorts video...", call.message.chat.id, call.message.message_id)
        except:
            pass

    try:
        # Use simple format selector for Shorts - just get the best available quality
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [shorts_progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Ensure mp4 extension
            base_path = os.path.splitext(file_path)[0]
            mp4_path = base_path + '.mp4'

            # Check which file exists
            if os.path.exists(mp4_path):
                file_path = mp4_path
            elif not os.path.exists(file_path):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_path = base_path + ext
                    if os.path.exists(test_path):
                        file_path = test_path
                        break

        # Get file info
        actual_height = info.get('height', 'Auto')
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # Update message with file info
        bot.edit_message_text(
            f"📤 Uploading YouTube Shorts ({actual_height}p)...\n📁 Size: {file_size_mb:.1f} MB", 
            call.message.chat.id, call.message.message_id
        )

        with open(file_path, 'rb') as f:
            # Send video with streaming support and metadata
            bot.send_video(
                call.message.chat.id, 
                f, 
                caption=f"🩳 {info['title']} ({actual_height}p)",
                supports_streaming=True,
                duration=info.get('duration'),
                width=info.get('width'),
                height=info.get('height')
            )

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text(
            f"❌ Download failed for YouTube Shorts: {str(e)}\n\nTry again or use the audio option instead.", 
            call.message.chat.id, 
            call.message.message_id
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_song_"))
def handle_confirm_song_download(call):
    user_id = call.from_user.id
    video_id = call.data[13:]  # Remove "confirm_song_" prefix
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Delete the confirmation message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if user_id in user_searches:
        del user_searches[user_id]

    msg = bot.send_message(call.message.chat.id, "🔍 Preparing song download...")

    def progress_hook(d):
        try:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                bot.edit_message_text(f"⬇️ Downloading: {percent} | Speed: {speed}", call.message.chat.id, msg.message_id)
            elif d['status'] == 'finished':
                bot.edit_message_text("🎵 Converting to MP3...", call.message.chat.id, msg.message_id)
        except:
            pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(base_filename)[0] + '.mp3'

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        bot.edit_message_text(f"📤 Uploading MP3 ({file_size_mb:.1f} MB)...", call.message.chat.id, msg.message_id)

        with open(file_path, 'rb') as f:
            bot.send_audio(call.message.chat.id, f, title=info['title'])

        os.remove(file_path)
        bot.delete_message(call.message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", call.message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_vid_"))
def handle_confirm_video_download(call):
    user_id = call.from_user.id
    video_id = call.data[12:]  # Remove "confirm_vid_" prefix

    # Delete the confirmation message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if user_id in user_video_searches:
        del user_video_searches[user_id]

    # Show quality selection
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("144p", callback_data=f"quality_{video_id}_144"))
    markup.add(InlineKeyboardButton("240p", callback_data=f"quality_{video_id}_240"))
    markup.add(InlineKeyboardButton("360p ⭐ (Recommended)", callback_data=f"quality_{video_id}_360"))
    markup.add(InlineKeyboardButton("480p", callback_data=f"quality_{video_id}_480"))
    markup.add(InlineKeyboardButton("720p", callback_data=f"quality_{video_id}_720"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"vcancel_{user_id}"))

    bot.send_message(call.message.chat.id, "📹 Select video quality:\n💡 360p is good and more stable", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_song_"))
def handle_back_to_song_search(call):
    user_id = int(call.data[10:])  # Remove "back_song_" prefix
    
    # Delete the confirmation message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if user_id in user_searches:
        query = user_searches[user_id]['query']
        page = user_searches[user_id]['page']
        search_and_display(None, query, page, call.message.chat.id, user_id, 'audio')
    else:
        bot.send_message(call.message.chat.id, "❌ Search session expired. Please start a new search with /song")

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_vid_"))
def handle_back_to_video_search(call):
    user_id = int(call.data[9:])  # Remove "back_vid_" prefix
    
    # Delete the confirmation message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if user_id in user_video_searches:
        query = user_video_searches[user_id]['query']
        page = user_video_searches[user_id]['page']
        search_and_display(None, query, page, call.message.chat.id, user_id, 'video')
    else:
        bot.send_message(call.message.chat.id, "❌ Search session expired. Please start a new search with /vid")

@bot.callback_query_handler(func=lambda call: call.data.startswith("yt_cancel_"))
def handle_yt_cancel(call):
    user_id = call.from_user.id

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    user_link = f"[{call.from_user.first_name}](tg://user?id={user_id})"
    bot.send_message(call.message.chat.id, f"{user_link} cancelled the download.", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def handle_song_info_display(call):
    user_id = call.from_user.id
    video_id = call.data[3:]
    
    if user_id in user_searches:
        search_message_id = user_searches[user_id].get('search_message_id')
        if search_message_id:
            try:
                bot.delete_message(call.message.chat.id, search_message_id)
            except:
                pass

    # Show loading message
    loading_msg = bot.send_message(call.message.chat.id, "🔍 Fetching song details...")
    
    try:
        # Get video info
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown Title')
            channel = info.get('uploader', 'Unknown Channel')
            view_count = info.get('view_count', 0)
            like_count = info.get('like_count', 0)
            upload_date = info.get('upload_date', '')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            
            # Format numbers
            if view_count >= 1000000:
                views_str = f"{view_count/1000000:.1f}M"
            elif view_count >= 1000:
                views_str = f"{view_count/1000:.1f}K"
            else:
                views_str = str(view_count)
                
            if like_count >= 1000000:
                likes_str = f"{like_count/1000000:.1f}M"
            elif like_count >= 1000:
                likes_str = f"{like_count/1000:.1f}K"
            else:
                likes_str = str(like_count)
            
            # Format upload date
            if upload_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(upload_date, '%Y%m%d')
                    formatted_date = date_obj.strftime('%b %d, %Y')
                except:
                    formatted_date = upload_date
            else:
                formatted_date = "Unknown"
                
            # Format duration
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Unknown"
        
        # Create info message
        info_text = f"""🎵 **{title}**

📺 **Channel:** {channel}
👀 **Views:** {views_str}
👍 **Likes:** {likes_str}
📅 **Uploaded:** {formatted_date}
⏱️ **Duration:** {duration_str}

Do you want to download this song as MP3?"""

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Yes, Download", callback_data=f"confirm_song_{video_id}"))
        markup.add(InlineKeyboardButton("❌ No, Choose Another", callback_data=f"back_song_{user_id}"))
        
        # Delete loading message and send song info with thumbnail
        bot.delete_message(call.message.chat.id, loading_msg.message_id)
        
        if thumbnail:
            bot.send_photo(
                call.message.chat.id,
                thumbnail,
                caption=info_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                call.message.chat.id,
                info_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ Error fetching song details: {str(e)}",
            call.message.chat.id,
            loading_msg.message_id
        )

bot.infinity_polling()

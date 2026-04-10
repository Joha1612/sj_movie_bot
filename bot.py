from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from live_scraper import (
    search_movie,
    get_trending_movies,
    get_category_movies,
    get_download_links,
    get_latest_movies,
    group_movies,
)

import os


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789

MOVIES_PER_PAGE = 8
USERS = set()


CATEGORY_URLS = {
    "🇧🇩 Bangla & Kolkata": "https://fibwatch.art/videos/category/1",
    "📺 Web Series": "https://fibwatch.art/videos/category/3",
    "🎬 Hindi": "https://fibwatch.art/videos/category/4",
    "🌐 Hindi Dubbed": "https://fibwatch.art/videos/category/5",
    "🎭 Bangla Dubbed": "https://fibwatch.art/videos/category/852",
    "🎤 Natok": "https://fibwatch.art/videos/category/855",
}


# ================= MENUS =================

def main_menu():

    keyboard = [
        ["🎬 Search Movie"],
        ["🆕 Latest Videos"],
        ["🔥 Trending"],
        ["📂 Categories"],
        ["🧹 Clear History"],
        ["ℹ️ Help"],
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def categories_menu():

    keyboard = [
        ["🇧🇩 Bangla & Kolkata"],
        ["🎬 Hindi"],
        ["🌐 Hindi Dubbed"],
        ["🎭 Bangla Dubbed"],
        ["📺 Web Series"],
        ["🎤 Natok"],
        ["🔙 Back"],
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    USERS.add(update.effective_user.id)

    await update.message.reply_text(
        "👋 Welcome to Movie Finder Bot",
        reply_markup=main_menu(),
    )


# ================= SHOW MOVIES =================

async def show_movies(update, context, movies, page=0):

    if not movies:
        await update.message.reply_text("No movies found.")
        return

    grouped = list(group_movies(movies).keys())

    context.user_data["grouped_movies"] = grouped
    context.user_data["all_movies"] = movies
    context.user_data["page"] = page

    start_index = page * MOVIES_PER_PAGE
    end_index = start_index + MOVIES_PER_PAGE

    page_items = grouped[start_index:end_index]

    keyboard = []

    for i, title in enumerate(page_items):
        keyboard.append([
            InlineKeyboardButton(
                title,
                callback_data=f"group_{start_index+i}"
            )
        ])

    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data="prev_page")
        )

    if end_index < len(grouped):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data="next_page")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    await update.message.reply_text(
        f"Select a movie (Page {page+1})",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= PAGINATION =================

async def pagination_handler(update, context):

    query = update.callback_query
    await query.answer()

    page = context.user_data.get("page", 0)

    if query.data == "next_page":
        page += 1
    else:
        page -= 1

    movies = context.user_data.get("all_movies", [])

    await show_movies(query.message, context, movies, page)


# ================= GROUP SELECT =================

async def group_selected(update, context):

    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])

    grouped_titles = context.user_data["grouped_movies"]
    selected_title = grouped_titles[index]

    all_movies = context.user_data["all_movies"]

    variants = [
        m for m in all_movies
        if selected_title.lower() in m["title"].lower()
    ]

    context.user_data["movies"] = variants

    keyboard = []

    for i, movie in enumerate(variants):
        keyboard.append([
            InlineKeyboardButton(
                movie["title"],
                callback_data=f"movie_{i}"
            )
        ])

    await query.message.reply_text(
        "Select version:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= MOVIE SELECT =================

async def movie_selected(update, context):

    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])

    movie = context.user_data["movies"][index]

    links = get_download_links(movie["url"])["downloads"]

    context.user_data["links"] = links

    keyboard = []

    for i, link in enumerate(links):
        keyboard.append([
            InlineKeyboardButton(
                link["quality"],
                callback_data=f"cdn_{i}"
            )
        ])

    poster = movie.get("poster")

    if poster:
        await query.message.reply_photo(
            photo=poster,
            caption=f"{movie['title']}\nSelect quality:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.message.reply_text(
            "Select quality:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ================= CDN SELECT =================

async def cdn_selected(update, context):

    query = update.callback_query
    await query.answer("Link ready!")

    index = int(query.data.split("_")[1])
    link = context.user_data["links"][index]["url"]

    keyboard = [[InlineKeyboardButton("📋 Copy Link", url=link)]]

    await query.message.reply_text(
        "Tap Copy Link button",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= MENU HANDLER =================

async def menu_handler(update, context):

    text = update.message.text

    if text == "🎬 Search Movie":
        await update.message.reply_text("Send movie name:")

    elif text == "🆕 Latest Videos":
        movies = get_latest_movies()
        await show_movies(update, context, movies)

    elif text == "🔥 Trending":
        movies = get_trending_movies()
        await show_movies(update, context, movies)

    elif text == "📂 Categories":
        await update.message.reply_text(
            "Select category:",
            reply_markup=categories_menu()
        )

    elif text == "🔙 Back":
        await update.message.reply_text(
            "Back to main menu",
            reply_markup=main_menu()
        )

    elif text == "🧹 Clear History":
        context.user_data.clear()
        await update.message.reply_text(
            "History cleared",
            reply_markup=main_menu()
        )

    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "Send movie name to search 🎬"
        )

    elif text in CATEGORY_URLS:
        movies = get_category_movies(CATEGORY_URLS[text])
        await show_movies(update, context, movies)

    else:
        movies = search_movie(text)
        await show_movies(update, context, movies)


# ================= MAIN =================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(group_selected, pattern="^group_")
    )

    app.add_handler(
        CallbackQueryHandler(movie_selected, pattern="^movie_")
    )

    app.add_handler(
        CallbackQueryHandler(cdn_selected, pattern="^cdn_")
    )

    app.add_handler(
        CallbackQueryHandler(
            pagination_handler,
            pattern="^(next_page|prev_page)$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler
        )
    )

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()

# Importing the required libraries
import telebot # https://github.com/eternnoir/pyTelegramBotAPI
import os # for file handling
from telebot import types # for inline and normal buttons
import threading # for asynchronous tasks

# Creating a bot object with the token
TOKEN = "YOUR_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

# Creating a global variable to store the admin id
ADMIN_ID = "YOUR_ADMIN_ID_HERE"

# Creating a global variable to store the books directory
BOOKS_DIR = "books/"

# Creating a global variable to store the book information
BOOK_INFO = {}

# Creating a global variable to store the categories and writers
CATEGORIES = set()
WRITERS = set()

# A function to load the book information from a file
def load_book_info():
    global BOOK_INFO, CATEGORIES, WRITERS
    try:
        with open("book_info.txt", "r") as f:
            for line in f:
                book_name, book_author, book_genre = line.strip().split("|")
                BOOK_INFO[book_name] = (book_author, book_genre)
                CATEGORIES.add(book_genre)
                WRITERS.add(book_author)
    except FileNotFoundError:
        print("No book information file found")

# A function to save the book information to a file
def save_book_info():
    global BOOK_INFO
    with open("book_info.txt", "w") as f:
        for book_name in BOOK_INFO:
            book_author, book_genre = BOOK_INFO[book_name]
            f.write(f"{book_name}|{book_author}|{book_genre}\n")

# A function to check if the user is the admin
def is_admin(message):
    return message.from_user.id == ADMIN_ID

# A function to handle the /start command
@bot.message_handler(commands=['start'])
def start(message):
    # Creating a normal keyboard with the commands
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("/menu"))
    keyboard.add(types.KeyboardButton("/search"))
    keyboard.add(types.KeyboardButton("/help"))
    # If the user is the admin, add the add and delete buttons
    if is_admin(message):
        keyboard.add(types.KeyboardButton("/add"))
        keyboard.add(types.KeyboardButton("/delete"))
    # Sending a welcome message with the keyboard
    bot.send_message(message.chat.id, "Welcome to the books library bot! Here you can find and download books in pdf format. Use the buttons below to navigate.", reply_markup=keyboard)


# A function to handle the /menu command
@bot.message_handler(commands=['menu'])
def menu(message):
    # Loading the book information from the file
    load_book_info()
    # Creating an inline keyboard with two buttons: categories and writers
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Categories", callback_data="categories"))
    keyboard.add(types.InlineKeyboardButton("Writers", callback_data="writers"))
    # Sending a message with the inline keyboard
    bot.send_message(message.chat.id, "Here you can browse the books by categories or writers. Choose an option below.", reply_markup=keyboard)

# A function to handle the callback queries from the menu buttons
@bot.callback_query_handler(func=lambda call: call.data in ["categories", "writers"])
def menu_query(call):
    # Getting the option from the callback data
    option = call.data
    # Loading the book information from the file
    load_book_info()
    # Creating an empty inline keyboard
    keyboard = types.InlineKeyboardMarkup()
    if option == "categories":
        # If the option is categories, loop through the categories set and create buttons for each category
        for category in CATEGORIES:
            keyboard.add(types.InlineKeyboardButton(category, callback_data=f"category_{category}"))
        # Sending a message with the inline keyboard
        bot.send_message(call.message.chat.id, "Here are the categories available in the library. Choose a category to see the books in it.", reply_markup=keyboard)
    elif option == "writers":
        # If the option is writers, loop through the writers set and create buttons for each writer
        for writer in WRITERS:
            keyboard.add(types.InlineKeyboardButton(writer, callback_data=f"writer_{writer}"))
        # Sending a message with the inline keyboard
        bot.send_message(call.message.chat.id, "Here are the writers available in the library. Choose a writer to see their books.", reply_markup=keyboard)


# A function to handle the callback queries from the category or writer buttons
@bot.callback_query_handler(func=lambda call: call.data.startswith("category_") or call.data.startswith("writer_"))
def filter_query(call):
    # Getting the filter and the value from the callback data
    filter, value = call.data.split("_", 1)
    # Loading the book information from the file
    load_book_info()
    # Creating an empty list to store the matching books
    matching_books = []
    # Looping through the book information
    for book_name in BOOK_INFO:
        book_author, book_genre = BOOK_INFO[book_name]
        # If the filter is category and the value matches the book genre, append it to the list
        if filter == "category" and value == book_genre:
            matching_books.append(book_name)
        # If the filter is writer and the value matches the book author, append it to the list
        elif filter == "writer" and value == book_author:
            matching_books.append(book_name)
    # If the list is not empty, create an inline keyboard with the matching books
    if matching_books:
        keyboard = types.InlineKeyboardMarkup()
        for book_name in matching_books:
            # For each book, create an inline button with its name and a callback data with its file name
            book_file = book_name + ".pdf"
            keyboard.add(types.InlineKeyboardButton(book_name, callback_data=book_file))
        # Sending a message with the inline keyboard
        bot.send_message(call.message.chat.id, f"Here are the books that match your {filter}: {value}. Click on any book to download it.", reply_markup=keyboard)
    else:
        # If the list is empty, send a message saying no books were found
        bot.send_message(call.message.chat.id, f"Sorry, no books were found with that {filter}: {value}.")


# A function to handle the callback queries from the book buttons
@bot.callback_query_handler(func=lambda call: call.data.endswith(".pdf"))
def book_query(call):
    # Getting the file name from the callback data
    book_file = call.data
    # Checking if the file exists in the books directory
    if os.path.exists(BOOKS_DIR + book_file):
        # If yes, send the file as a document
        bot.send_document(call.message.chat.id, open(BOOKS_DIR + book_file, "rb"))
    else:
        # If no, send an error message
        bot.send_message(call.message.chat.id, "Sorry, this book is not available.")

# A function to handle the /search command
@bot.message_handler(commands=['search'])
def search_books(message):
    # Loading the book information from the file
    load_book_info()
    # Sending a message asking for a keyword to search by
    bot.send_message(message.chat.id, "Please enter a keyword to search by (name, author or genre).")
    # Registering the next step handler to process the keyword
    bot.register_next_step_handler(message, process_keyword)

# A function to process the keyword entered by the user
def process_keyword(message):
    # Getting the keyword from the message text
    keyword = message.text.lower()
    # Creating an empty list to store the matching books
    matching_books = []
    # Looping through the book information
    for book_name in BOOK_INFO:
        book_author, book_genre = BOOK_INFO[book_name]
        # If the keyword matches the name, author or genre of the book, append it to the list
        if keyword in book_name.lower() or keyword in book_author.lower() or keyword in book_genre.lower():
            matching_books.append(book_name)
    # If the list is not empty, create an inline keyboard with the matching books
    if matching_books:
        keyboard = types.InlineKeyboardMarkup()
        for book_name in matching_books:
            # For each book, create an inline button with its name and a callback data with its file name
            book_file = book_name + ".pdf"
            keyboard.add(types.InlineKeyboardButton(book_name, callback_data=book_file))
        # Sending a message with the inline keyboard
        bot.send_message(message.chat.id, "Here are the books that match your keyword. Click on any book to download it.", reply_markup=keyboard)
    else:
        # If the list is empty, send a message saying no books were found
        bot.send_message(message.chat.id, "Sorry, no books were found with that keyword.")

# A function to handle the /help command
@bot.message_handler(commands=['help'])
def help(message):
    # Sending a message with some instructions and information
    bot.send_message(message.chat.id, "This bot allows you to find and download books in pdf format from a library. You can use the following commands:\n\n/menu - to browse the books by categories or writers.\n/search - to search for a book by name, author or genre.\n/help - to see this message.\n\nIf you are the admin of this bot, you can also use these commands:\n\n/add - to add a new book to the library.\n/delete - to delete an existing book from the library.")

# A function to handle the /add command
@bot.message_handler(commands=['add'], func=is_admin)
def add_book(message):
    # Sending a message asking for the book file to be added
    bot.send_message(message.chat.id, "Please send the book file in pdf format that you want to add to the library.")
    # Registering the next step handler to process the file
    bot.register_next_step_handler(message, process_file)

# A function to process the file sent by the admin
def process_file(message):
    # Checking if the message contains a document
    if message.document:
        # Getting the file id and file name from the message document
        file_id = message.document.file_id
        file_name = message.document.file_name
        # Checking if the file name ends with .pdf
        if file_name.endswith(".pdf"):
            # Creating a thread to download and save the file asynchronously
            thread = threading.Thread(target=download_and_save_file, args=(file_id, file_name))
            thread.start()
            # Sending a message asking for the book information
            bot.send_message(message.chat.id, "The book file is being added. Please enter the book information in this format: name|author|genre")
            # Registering the next step handler to process the information
            bot.register_next_step_handler(message, process_info, file_name)
        else:
            # If the file name does not end with .pdf, send an error message and repeat the step
            bot.send_message(message.chat.id, "The file is not in pdf format. Please send a valid pdf file.")
            bot.register_next_step_handler(message, process_file)
    else:
        # If the message does not contain a document, send an error message and repeat the step
        bot.send_message(message.chat.id, "The message does not contain a document. Please send a valid pdf file.")
        bot.register_next_step_handler(message, process_file)

# A function to download and save the file using the file id and file name
def download_and_save_file(file_id, file_name):
    # Downloading the file using the file id and saving it in the books directory
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(BOOKS_DIR + file_name, "wb") as f:
        f.write(downloaded_file)

# A function to process the information entered by the admin
def process_info(message, file_name):
    # Getting the information from the message text
    info = message.text.strip()
    # Checking if the information is in the correct format
    if "|" in info and len(info.split("|")) == 3:
        # Splitting the information into name, author and genre
        name, author, genre = info.split("|")
        # Removing the .pdf extension from the file name
        name = name.replace(".pdf", "")
        # Updating the global variable with the new book information
        global BOOK_INFO, CATEGORIES, WRITERS
        BOOK_INFO[name] = (author, genre)
        CATEGORIES.add(genre)
        WRITERS.add(author)
        # Saving the book information to the file
        save_book_info()
        # Sending a confirmation message
        bot.send_message(message.chat.id, f"The book {name} by {author} has been added to the library under the category {genre}.")
    else:
        # If the information is not in the correct format, send an error message and repeat the step
        bot.send_message(message.chat.id, "The information is not in the correct format. Please enter it in this format: name|author|genre")
        bot.register_next_step_handler(message, process_info, file_name)

# A function to handle the /delete command
@bot.message_handler(commands=['delete'], func=is_admin)
def delete_book(message):
    # Declaring the global variables
    global BOOK_INFO, CATEGORIES, WRITERS
    # Loading the book information from the file
    load_book_info()
    # Sending a message asking for the name of the book to be deleted
    bot.send_message(message.chat.id, "Please enter the name of the book that you want to delete from the library.")
    # Registering the next step handler to process the name
    bot.register_next_step_handler(message, process_name)

# A function to process the name entered by the admin
def process_name(message):
    # Getting the name from the message text
    name = message.text.strip()
    # Checking if the name is in the book information
    if name in BOOK_INFO:
        # Getting the file name from the name
        file_name = name + ".pdf"
        # Checking if the file exists in the books directory
        if os.path.exists(BOOKS_DIR + file_name):
            # If yes, delete the file from the books directory
            os.remove(BOOKS_DIR + file_name)
        # Deleting the name from the book information
        book_author, book_genre = BOOK_INFO.pop(name)
        # Saving the book information to the file
        save_book_info()
        # Checking if the category and writer are still in use
        if book_genre not in [genre for _, genre in BOOK_INFO.values()]:
            # If not, remove them from the categories and writers sets
            CATEGORIES.remove(book_genre)
        if book_author not in [author for author, _ in BOOK_INFO.values()]:
            # If not, remove them from the categories and writers sets
            WRITERS.remove(book_author)
        # Sending a confirmation message
        bot.send_message(message.chat.id, f"The book {name} by {author} has been deleted from the library.")
    else:
        # If the name is not in the book information, send an error message and repeat the step
        bot.send_message(message.chat.id, "The book name is not found in the library. Please enter a valid book name.")
        bot.register_next_step_handler(message, process_name)

bot.polling() 

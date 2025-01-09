import telebot
import PIL as pil
import PIL.ImageOps
from PIL import Image
import io
from telebot import types

TOKEN = '7308792898:AAG29SEzQcPX10e0XCuDuvbuQbK_C19XYwc'
bot = telebot.TeleBot(TOKEN)

user_states = {}  # тут будем хранить информацию о действиях пользователя

# набор символов из которых составляем изображение
ASCII_CHARS = '@%#*+=-:. '


def resize_image(image, new_width=100):
    width, height = image.size
    ratio = height / width
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))


def grayify(image):
    return image.convert("L")


def image_to_ascii(image_stream, new_width=40, ascii_chars_in=ASCII_CHARS):
    """ Функция преобразования изображения в зображение из символов заданной последовательности """
    # Переводим в оттенки серого
    image = Image.open(image_stream).convert('L')
    ''' Перевод изображения в оттенки серого '''
    # меняем размер сохраняя отношение сторон
    width, height = image.size
    aspect_ratio = height / float(width)
    new_height = int(
        aspect_ratio * new_width * 0.55)  # 0,55 так как буквы выше чем шире
    img_resized = image.resize((new_width, new_height))
    ''' Измененияе размера изображения с сохранением соотношения сторон '''
    img_str = pixels_to_ascii(img_resized, ascii_temp=ascii_chars_in)
    img_width = img_resized.width
    ''' Получение данных для окончательного преобразования '''
    max_characters = 4000 - (new_width + 1)
    max_rows = max_characters // (new_width + 1)
    ''' Определение максимального колличества строк и символов'''
    ascii_art = ""
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"
    ''' Окончательное преобразование '''
    return ascii_art


def pixels_to_ascii(image, ascii_temp=ASCII_CHARS):
    """ Функция преобразования пиксилей в символы последовательности """
    pixels = image.getdata()
    characters = ""
    ''' Создание массива пиксилей '''
    for pixel in pixels:
        characters += ascii_temp[pixel * len(ascii_temp) // 256]
    ''' Заполнение строки символов '''
    return characters


# Огрубляем изображение
def pixelate_image(image, pixel_size):
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        Image.NEAREST
    )
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        Image.NEAREST
    )
    return image


def invert_colors(image):
    """ Функция инвертирования цветов на изображение """
    reverse_art = pil.ImageOps.invert(image)
    ''' Вызов функции инвертирования цветов из библиотеки'''
    return reverse_art


def flip_image(image, flip_type):
    """ Функция отражения изображения """
    if flip_type == "horizontally":
        flip_image = image.transpose(pil.Image.FLIP_LEFT_RIGHT)
    elif flip_type == "vertically":
        flip_image = image.transpose(pil.Image.FLIP_TOP_BOTTOM)
    ''' Отражение изображения по указанному направлению'''
    return flip_image


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me an image, and I'll provide options for you!")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "I got your photo! Please choose what you'd like to do with it.",
                 reply_markup=get_options_keyboard())
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id}


def get_options_keyboard():
    """ Клавиатура выбора действия применяемого к картинке """
    keyboard = types.InlineKeyboardMarkup()
    pixelate_btn = types.InlineKeyboardButton("Pixelate", callback_data="pixelate")
    ascii_btn = types.InlineKeyboardButton("ASCII Art", callback_data="ascii")
    reverse_btn = types.InlineKeyboardButton("Reverse", callback_data="revers")
    flip_btn = types.InlineKeyboardButton("flip", callback_data="flip")
    ''' Описание кнопок клавиатуры '''
    keyboard.add(pixelate_btn, ascii_btn, reverse_btn, flip_btn)
    ''' Создание кнопок '''
    return keyboard


def get_ascii_line_keyboard():
    """ Клавиатура выбора типа ASCII последовательности """
    keyboard = types.InlineKeyboardMarkup()
    pixelate_btn = types.InlineKeyboardButton("Default", callback_data="ascii_default")
    ascii_btn = types.InlineKeyboardButton("New", callback_data="ascii_new")
    ''' Описание кнопок клавиатуры '''
    keyboard.add(pixelate_btn, ascii_btn)
    ''' Создание кнопок '''
    return keyboard


def get_flip_keyboard():
    """ Клавиатура выбора вида отражения """
    keyboard = types.InlineKeyboardMarkup()
    horizontally_btn = types.InlineKeyboardButton("Horizontally", callback_data="flip_horizontally")
    vertically_btn = types.InlineKeyboardButton("Vertically", callback_data="flip_vertically")
    ''' Описание кнопок клавиатуры '''
    keyboard.add(horizontally_btn, vertically_btn)
    ''' Создание кнопок '''
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """ Обработчик инлайн клавиатур """
    if call.data == "pixelate":
        bot.answer_callback_query(call.id, "Pixelating your image...")
        pixelate_and_send(call.message)
        ''' Обработка кнопки пиксилизации '''
    elif call.data == "ascii":
        bot.reply_to(call.message, "Choose to use the default ASCII sequence or set your own.",
                     reply_markup=get_ascii_line_keyboard())
        ''' Обработка кнопки перерисовки в символах '''
    elif call.data == "revers":
        bot.answer_callback_query(call.id, "Revers your image color...")
        reverse_and_send(call.message)
        ''' Обработка кнопки реверса цветов изображения '''
    elif call.data == "flip":
        bot.reply_to(call.message, "Select reflect horizontally or vertically.",
                     reply_markup=get_flip_keyboard())
        ''' Обработка кнопки отражения изображения '''

    elif call.data == "ascii_default":
        bot.answer_callback_query(call.id, "Converting your image to ASCII art...")
        use_text = False
        ascii_and_send(call.message, use_text)
        ''' Обработка кнопки отрисовки в базовой последоветельности символов '''
    elif call.data == "ascii_new":
        bot.send_message(call.message.chat.id, 'Enter your ASCII sequence (ten characters for the best result)')

        @bot.message_handler()
        def handle_ascii(message):
            bot.reply_to(message, "I got your ASCII sequence")
            use_this_text = True
            ascii_and_send(message, use_this_text)
        ''' Обработка кнопки отрисовки в задоваемой последоветельности символов '''
    elif call.data == "flip_horizontally":
        flip_and_send(call.message, "horizontally")
        ''' Обработка кнопки отражения изображения по горизонтали '''
    elif call.data == "flip_vertically":
        flip_and_send(call.message, "vertically")
        ''' Обработка кнопки отражения изображения по вертикали '''


def pixelate_and_send(message):
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    pixelated = pixelate_image(image, 20)

    output_stream = io.BytesIO()
    pixelated.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def reverse_and_send(message):
    """ Функция отправки результатов по преобразованию """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    ''' Выдиление присланного изображения '''
    reversed_image = invert_colors(image)
    output_stream = io.BytesIO()
    reversed_image.save(output_stream, format="JPEG")
    output_stream.seek(0)
    ''' Подготовка результата '''
    bot.send_photo(message.chat.id, output_stream)
    ''' Отправка результата '''


def flip_and_send(message, flip_type):
    """ Функция отправки результатов по преобразованию """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    ''' Выдиление присланного изображения '''
    temp_image = flip_image(image, flip_type)
    output_stream = io.BytesIO()
    temp_image.save(output_stream, format="JPEG")
    output_stream.seek(0)
    ''' Подготовка результата '''
    bot.send_photo(message.chat.id, output_stream)
    ''' Отправка результата '''


def ascii_and_send(message, use_text):
    """ Функция отправки результатов по преобразованию """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)
    ''' Выдиление присланного изображения '''
    if use_text:
        ascii_art = image_to_ascii(image_stream, ascii_chars_in=message.text)
    else:
        ascii_art = image_to_ascii(image_stream, ascii_chars_in=ASCII_CHARS)
    ''' Проверка используемой для преобразования последовательности '''
    bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")
    ''' Отправка результата '''


bot.polling(none_stop=True)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from json import loads
import requests
from urllib.request import urlretrieve as download
import img2pdf
from bot.ModelClasses import Message

TELEGRAM_URL = "https://api.telegram.org/bot"
FILE_URL = "https://api.telegram.org/file/bot"
TOKEN = "1720556992:AAE4v6KVcdRGSfTMEVdvfBwr0EA4LbHFSok"


def url_creator(method_name):
    return f"{TELEGRAM_URL}{TOKEN}/{method_name}"


def send_message(chat_id, text, parse_mode=None, reply_to_message_id=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode is not None:
        data["parse_mode"] = parse_mode
    if reply_to_message_id is not None:
        data["reply_to_message_id"] = reply_to_message_id
    result = requests.post(url_creator("sendMessage"), data)


def get_file(file_id, chat_id):
    data = {
        "file_id": file_id.replace("\n", "")
    }
    file_path = ""
    try:
        result = requests.get(url_creator("getFile"), data=data)
        file_path = result.json().get("result").get("file_path", None)
    except Exception:
        send_message(chat_id, "مشکلی در ارتباط با سرور تلگرام پیش آمد!")
    return file_path


def download_file(file_path, user_id, index):
    extension = file_path.split(".")[-1]
    path = f"./{user_id}_{index}.{extension}"
    download(f"{FILE_URL}{TOKEN}/{file_path}", f"{path}")
    return path


def convert_image_to_pdf(images: list, user_id):
    with open(f"{user_id}.pdf", "wb") as f:
        f.write(img2pdf.convert(images))
    return f"{user_id}.pdf"


@csrf_exempt
def telegram_webhook(request, *args, **kwargs):
    message = Message(translate_request(request))
    print(translate_request(request))
    if message.is_photo_message():
        insert_photo_to_database(message.sender.id, message.photo.photo_id)
    else:
        if message.text == "/start" or message.text == "hi":
            return JsonResponse({"ok": "POST request processed"})
        downloaded_pictures = []
        try:
            photos = select_photo_from_database(message.sender.id)
            for i in range(len(photos)):
                downloaded_pictures\
                    .append(str(download_file(get_file(photos[i], message.sender.id), message.sender.id, i)))
            convert_image_to_pdf(downloaded_pictures, message.sender.id)
        except Exception:
            pass
    return JsonResponse({"ok": "POST request processed"})


def insert_photo_to_database(user_id, photo_id):
    # TODO: implement real database
    try:
        open(f"{user_id}.txt", "x").close()
    except FileExistsError:
        pass
    db = open(f"{user_id}.txt", "a")
    db.write(f"{photo_id}\n")
    db.close()


def select_photo_from_database(user_id):
    # TODO: implement real database
    file = open(f"{user_id}.txt")
    lines = file.readlines()
    file.close()
    return lines


def translate_request(request):
    return loads(request.body)

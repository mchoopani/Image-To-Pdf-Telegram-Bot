from django.views.decorators.csrf import csrf_exempt
from json import loads
from ModelClasses import Message
import requests

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


def get_file(file_id):
    data = {
        "file_id": file_id
    }
    file_path = ""
    try:
        result = requests.post(url_creator("getFile"), data=data)
        file_path = result.body.get("file_path", None)
    except Exception:
        # TODO
        send_message("TODO")
    return file_path


def download_file(file_path):
    # TODO: download photo from FILE_URL + TOKEN + file_path
    pass


@csrf_exempt
def telegram_webhook(request, *args, **kwargs):
    message = Message(translate_request(request))
    if message.is_photo_message():
        insert_photo_to_database(message.sender.id, message.photo.photo_id)
    else:
        photos = select_photo_from_database(message.sender.id)


def insert_photo_to_database(user_id, photo_id):
    # TODO: implement real database
    try:
        open(f"{user_id}.txt", "x").close()
    except FileExistsError:
        pass
    db = open(f"{user_id}.txt", "w")
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

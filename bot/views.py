import os

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


def send_document(chat_id, file_path, caption):
    file = open(file_path, "rb")
    data = {
        "chat_id": chat_id,
    }
    files = {"document": file}
    if caption is not None:
        data["caption"] = caption
    result = requests.post(url_creator("sendDocument"), data, files=files)
    file.close()


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


def delete_files(downloaded_pictures, user_id):
    for path in downloaded_pictures:
        try:
            os.remove(path)
        except Exception:
            pass
    try:
        os.remove(f"{user_id}.pdf")
    except Exception:
        pass


@csrf_exempt
def telegram_webhook(request, *args, **kwargs):
    message = Message(translate_request(request))
    print(translate_request(request))
    if message.is_photo_message():
        insert_photo_to_database(message.sender.id, message.photo.photo_id)
        return JsonResponse({"ok": "POST request processed"})
    else:
        if message.text == "/start":
            send_message(message.sender.id, "Hello welcome to your bot.\n"
                                            "to start a project send: create\n"
                                            "to end last active project send: export\n"
                                            "after sending 'create' before history of projects will clear, "
                                            "and start new project.\n"
                                            "after send `export` all of pictures that send after last 'create'"
                                            " and before 'export' will packed and converted to PDF.\n"
                                            "shortcut: you can send your photos, at last send: !\n"
                                            "this shortcut (!) collects before pictures and finally"
                                            "clears the list of photos and waits for new project.")
            return JsonResponse({"ok": "POST request processed"})
        if message.text == "create":
            send_message(message.sender.id, "new project created.")
            # TODO: delete from real database
            open(f"{message.sender.id}.txt", "w").close()
            return JsonResponse({"ok": "POST request processed"})
        if message.text == "export" or message.text == "!":
            send_message(message.sender.id, "bot will export pdf of this project soon.\n"
                                            "please wait...")
            downloaded_pictures = []
            try:
                photos = select_photo_from_database(message.sender.id)
                for i in range(len(photos)):
                    downloaded_pictures \
                        .append(str(download_file(get_file(photos[i], message.sender.id), message.sender.id, i)))
                convert_image_to_pdf(downloaded_pictures, message.sender.id)
                send_document(message.sender.id, f"{message.sender.id}.pdf", None)
                # TODO: delete from real database
                open(f"{message.sender.id}.txt", "w").close()
                delete_files(downloaded_pictures, message.sender.id)
            except Exception:
                pass
            return JsonResponse({"ok": "POST request processed"})
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

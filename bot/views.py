import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from json import loads
import requests
from urllib.request import urlretrieve as download
import img2pdf
from bot.ModelClasses import Message

# constant string that is used to created urls
TELEGRAM_URL = "https://api.telegram.org/bot"
FILE_URL = "https://api.telegram.org/file/bot"
# token of bot will be here
TOKEN = "<BOTTOKEN>"


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


def send_message(chat_id, text, reply_to_message_id=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_to_message_id is not None:
        data["reply_to_message_id"] = reply_to_message_id
    result = requests.post(url_creator("sendMessage"), data)


# get data of file from telegram servers
def get_file(file_id, chat_id):
    data = {
        "file_id": file_id.replace("\n", "")
    }
    file_path = ""
    try:
        result = requests.get(url_creator("getFile"), data=data)
        file_path = result.json().get("result").get("file_path", None)
    except Exception:
        send_message(chat_id, "there is a trouble in connection with telegram servers...")
    return file_path


def download_file(file_path, user_id, index):
    extension = file_path.split(".")[-1]
    path = f"./{user_id}_{index}.{extension}"
    download(f"{FILE_URL}{TOKEN}/{file_path}", f"{path}")
    return path


# convert list of images to pdf by img2pdf library
def convert_image_to_pdf(images: list, user_id):
    with open(f"{user_id}.pdf", "wb") as f:
        f.write(img2pdf.convert(images))
    return f"{user_id}.pdf"


# delete photos and pdf to optimize memory and respect to user personal data
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


# main function that telegram requests will call it
@csrf_exempt
def telegram_webhook(request, *args, **kwargs):
    # use Message class to translate message data to an object to easier accessibility
    message = Message(translate_request(request))
    if message.is_photo_message():
        # add photo ids to database (txt file) to use it whenever user want to export pdf
        insert_photo_to_database(message.sender.id, message.photo.photo_id)
        return JsonResponse({"ok": "POST request processed"})
    else:
        if message.text == "/start":
            # Welcome Message
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
            # delete old data to have a new project
            open(f"{message.sender.id}.txt", "w").close()
            return JsonResponse({"ok": "POST request processed"})
        if message.text == "export" or message.text == "!":
            send_message(message.sender.id, "bot will export pdf of this project soon.\n"
                                            "please wait...")
            downloaded_pictures = []
            try:
                # get all photo ids from database
                photos = select_photo_from_database(message.sender.id)
                for i in range(len(photos)):
                    # download each photo that contains in data base and add its name to convert list
                    downloaded_pictures \
                        .append(str(download_file(get_file(photos[i], message.sender.id), message.sender.id, i)))
                # convert downloaded photos to pdf
                convert_image_to_pdf(downloaded_pictures, message.sender.id)
                # send converted pdf to user
                send_document(message.sender.id, f"{message.sender.id}.pdf", None)
                # TODO: delete from real database
                open(f"{message.sender.id}.txt", "w").close()
                # delete pdf and photos
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


# returns request body
def translate_request(request):
    return loads(request.body)

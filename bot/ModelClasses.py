class User:
    def __init__(self, data_dictionary: dict):
        self.id = data_dictionary.get("id")
        self.first_name = data_dictionary.get("first_name", None)
        self.last_name = data_dictionary.get("last_name", None)


class Photo:
    def __init__(self, data_dictionary: dict):
        self.photo_id = data_dictionary.get("file_id")


class Message:
    def __init__(self, data_dictionary: dict):
        self.sender = User(data_dictionary.get("message").get("from"))
        self.text = data_dictionary.get("message").get("text", None)
        self.time = data_dictionary.get("message").get("date")
        photo = data_dictionary.get("message").get("photo", None)
        # we keep best quality of picture
        self.photo = Photo(photo[-1]) if photo is not None else None

    def is_photo_message(self):
        return self.photo is not None

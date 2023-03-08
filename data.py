import json
from pathlib import Path
from typing import Dict

from cqwu import Client

from .models import User

ROOT_PATH = Path(__name__).parent.absolute()
DATA_PATH = ROOT_PATH / "data" / "nonebot-plugin-cqwu"
DATA_PATH.mkdir(parents=True, exist_ok=True)


class CQWURawData:
    def __init__(self):
        self.file_path = DATA_PATH / "users.json"
        self.raw_data: Dict[str, User] = {}
        self.load()

    def load(self):
        if not self.file_path.exists():
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            temp_data: Dict[str, Dict] = json.load(f)
        for user_id, user in temp_data.items():
            self.raw_data[user_id] = User(**user)

    def save(self):
        temp_data: Dict[str, Dict] = {
            user_id: user.dict() for user_id, user in self.raw_data.items()
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(temp_data, f, ensure_ascii=False, indent=4)

    def add_user(self, user_id: int, username: int, password: str) -> None:
        self.raw_data[str(user_id)] = User(
            qq=user_id, username=username, password=password
        )
        self.save()


class CQWUData:
    def __init__(self):
        self.raw_data = CQWURawData()
        self.users: Dict[int, Client] = {}
        self.scores: Dict[int, int] = {}
        self.add_all_users()

    def add_all_users(self):
        for user_id, user in self.raw_data.raw_data.items():
            self.users[int(user_id)] = user.get_client()

    def add_user(self, user_id: int, username: int, password: str, client: Client) -> None:
        self.remove_user(user_id)
        self.users[user_id] = client
        self.raw_data.add_user(user_id, username, password)

    def remove_user(self, user_id: int) -> bool:
        if user_id in self.users:
            self.users[user_id].request.close()
            del self.users[user_id]
            return True
        return False

    def has_user(self, user_id: int) -> bool:
        return user_id in self.users

    def get_user(self, user_id: int) -> Client:
        return self.users[user_id]


cqwu_data = CQWUData()

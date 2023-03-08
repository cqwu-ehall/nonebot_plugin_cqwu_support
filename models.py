from pydantic import BaseModel

from cqwu import Client


class User(BaseModel):
    qq: int
    username: int
    password: str

    def get_client(self):
        return Client(
            username=self.username,
            password=self.password,
        )

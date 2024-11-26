from typing import Union


def generate_conversation_id(user1: Union[str, int], user2: Union[str, int]):
    users = sorted([f"{user1}".strip().lower(), f"{user2}".strip().lower()])
    return '-'.join(users)

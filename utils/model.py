from dotenv import load_dotenv
from agno.models.mistral import MistralChat
load_dotenv()


def get_model(name: str):
    return MistralChat(id=name)
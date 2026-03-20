import os

from langchain_openai import ChatOpenAI


model = os.getenv("OPENAI_MODEL")
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

MODEL = ChatOpenAI(
    model=model,
    base_url=base_url,
    api_key=api_key,
    temperature=0.1,
)

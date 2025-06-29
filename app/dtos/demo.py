from pydantic import BaseModel, Field


class Demo(BaseModel):
    message: str = Field(
        default="Hello, World!",
        description="A simple message to demonstrate the API.",
        examples=["Hello, FastAPI!"],
    )

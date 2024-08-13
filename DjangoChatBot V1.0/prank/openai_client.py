import os
from openai import OpenAI
from typing import Generic, TypeVar
from pydantic import BaseModel

# Define a TypeVar for generics
_T = TypeVar('_T')

# Define a generic Pydantic model
class GenericModel(BaseModel, Generic[_T]):
    data: _T

# Example of a concrete model that might be used with the generic model
class ConcreteModel(BaseModel):
    id: int
    name: str

# Define your RootModel using the GenericModel
class RootModel(GenericModel[ConcreteModel]):
    pass

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv('OPENAI_API_KEY'),
)

def get_openai_response(message):
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model="gpt-3.5-turbo",
        )
        return response
    except Exception as e:
        return f"An error occurred: {e}"


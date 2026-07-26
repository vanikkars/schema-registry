from pydantic import BaseModel, Field
from datetime import date


class User(BaseModel):
    user_name: str = Field(..., description="Username for the user")
    email: str = Field(..., description="Email address of the user")
    date_of_birth: date = Field(..., description="Date of birth in YYYY-MM-DD format")

    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "john_doe",
                "email": "john@example.com",
                "date_of_birth": "1990-05-15",
            }
        }
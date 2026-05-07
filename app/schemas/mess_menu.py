# FILE: app/schemas/mess_menu.py

from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from app.schemas.base import APIModel


class MessMenuCreateRequest(BaseModel):
    week_start_date: date
    is_active: bool = True
    meal_type: str = Field(min_length=2, max_length=50)
    item_name: str = Field(min_length=2, max_length=255)
    day_of_week: str = Field(min_length=2, max_length=20)
    is_veg: bool = True
    special_note: str | None = Field(default=None, max_length=255)
    
    @field_validator("day_of_week", mode="before")
    @classmethod
    def handle_empty_day(cls, v: str) -> str:
        """Convert empty string to a value that will fail validation with 400"""
        if v == "":
            return " "  # Single space fails min_length=2, will be caught by service
        return v


class MessMenuItemUpdateRequest(BaseModel):
    """Request to update a mess menu item"""
    day_of_week: str | None = Field(default=None, min_length=2, max_length=20)
    meal_type: str | None = Field(default=None, min_length=2, max_length=50)
    item_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_veg: bool | None = None
    special_note: str | None = Field(default=None, max_length=255)
    
    @field_validator("day_of_week", mode="before")
    @classmethod
    def handle_empty_day(cls, v: str | None) -> str | None:
        """Convert empty string to None or a value that fails validation"""
        if v == "":
            # Return something that will be caught by service validation
            return " "
        return v



class MessMenuItemUpdateRequest(BaseModel):
    """Request to update a mess menu item"""
    day_of_week: str | None = Field(default=None, min_length=1, max_length=20)  # Changed from 2 to 1
    meal_type: str | None = Field(default=None, min_length=2, max_length=50)
    item_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_veg: bool | None = None
    special_note: str | None = Field(default=None, max_length=255)


class MessMenuItemResponse(APIModel):
    id: str
    menu_id: str
    day_of_week: str
    meal_type: str
    item_name: str
    is_veg: bool
    special_note: str | None = None


class MessMenuResponse(APIModel):
    id: str
    hostel_id: str
    week_start_date: date
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    day_of_week: str | None = None
    meal_type: str | None = None
    item_name: str | None = None
    is_veg: bool | None = None
    special_note: str | None = None

    model_config = {"from_attributes": True}
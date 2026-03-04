from pydantic import BaseModel
from typing import Optional,List,Dict
from datetime import datetime
from pydantic import field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
 
class TimeBlock(BaseModel):
    start:str
    end:str
    @field_validator("start", "end", mode="before")
    @classmethod
    def convert_to_24_hour(cls, value):
        try:
         
            time_obj = datetime.strptime(value, "%H:%M")
        except ValueError:
            try:
             
                time_obj = datetime.strptime(value, "%I:%M %p")
            except ValueError:
                raise ValueError(
                    "Time must be in 'HH:MM' (24hr) or 'HH:MM AM/PM' format"
                )

        return time_obj.strftime("%H:%M")

    @field_validator("end")
    @classmethod
    def validate_time_order(cls, end_value, info):
        start_value = info.data.get("start")

        if start_value:
            start_time = datetime.strptime(start_value, "%H:%M")
            end_time = datetime.strptime(end_value, "%H:%M")

            if end_time <= start_time:
                raise ValueError("End time must be after start time")

        return end_value
    

SUPPORTED_TIMEZONES = [
    "Asia/Kolkata",
    "Asia/Dubai",
    "Asia/Singapore",
    "Asia/Tokyo",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Madrid",
    "Europe/Rome",
    "Europe/Amsterdam",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Toronto",
    "America/Vancouver",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Pacific/Auckland",
    "Asia/Hong_Kong",
    "Asia/Shanghai",
    "Asia/Jakarta",
    "Asia/Bangkok",
    "Africa/Johannesburg",
    "Europe/Dublin",
    "Europe/Zurich",
]


VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
}

class ScheduleBase(BaseModel):
    name:str
    timezone:str
    sending_windows:Dict[str,List[TimeBlock]]
    is_active:bool=True
    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value):
        if value not in SUPPORTED_TIMEZONES:
            raise ValueError("Invalid timezone selected")
        return value
    @field_validator("sending_windows")
    @classmethod
    def validate_sending_windows(cls,value):
        for day in value.keys():
         if day.lower() not in VALID_DAYS:
            raise ValueError(f"Invalid day: {day}")
        return value
    

class ScheduleCreate(ScheduleBase):
     pass 


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    sending_windows: Optional[Dict[str,List[TimeBlock]]] = None
    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value):
        if value is not None and value not in SUPPORTED_TIMEZONES:
            raise ValueError("Invalid timezone selected")
        return value
    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value):
        if value not in SUPPORTED_TIMEZONES:
            raise ValueError("Invalid timezone selected")

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError("Invalid IANA timezone")

        return value

class ScheduleResponse(ScheduleBase):
    id: str
    owner_id: str
    created_at: datetime
   
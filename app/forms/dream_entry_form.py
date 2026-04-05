from typing import List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, field_validator, model_validator

from ..models import DreamEntry, Tag

# This is a Pydantic model that recieves raw form data from the user and processes it into a DreamEntry
# The JSON-ified version of this is also used to store the data in the session if the user was not logged in
class DreamEntryForm(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    content_tags: List[str] = []
    sense_sight: bool|None = False
    sense_sound: bool|None = False
    sense_touch: bool|None = False
    sense_smell: bool|None = False
    sense_taste: bool|None = False
    sense_pain: bool|None = False
    sense_other: bool|None = False
    type_tags: List[str] = []
    context: str|None = None
    context_tags: List[str] = []
    bed_time: time|None = None
    wake_time: time|None = None
    sleep_hours: float|None = None
    sleep_tags: List[str] = []
    country: str|None = None
    state: str|None = None
    city: str|None = None
    public: bool

    @field_validator("bed_time", "wake_time", mode="before")
    @classmethod
    def time_or_none(cls, input: str):
        if input: return time.fromisoformat(input)
        else: return None

    @field_validator("context", "country", "state", "city")
    @classmethod
    def empty_to_none(cls, input: str):
        return input if input else None
    
    @model_validator(mode="after")
    def null_senses_if_all_false(self):
        if not (self.sense_sight or self.sense_sound or self.sense_touch or self.sense_smell or self.sense_taste or self.sense_pain or self.sense_other):
            self.sense_sight = self.sense_sound = self.sense_touch = self.sense_smell = self.sense_taste = self.sense_pain = self.sense_other = None
        return self
    
    @model_validator(mode="after")
    def calculate_sleep_data(self):
        if self.bed_time and self.wake_time:
            # if wake time < bed time, assume it's the next day
            if self.wake_time < self.bed_time:
                sleep_duration = datetime.combine(date(1,1,2), self.wake_time) - datetime.combine(date(1,1,1), self.bed_time)
            else:
                sleep_duration = datetime.combine(date(1,1,1), self.wake_time) - datetime.combine(date(1,1,1), self.bed_time)
            # calculate amount of sleep
            self.sleep_hours = sleep_duration.total_seconds() / 3600
            if self.sleep_hours < 4:
                self.sleep_tags.append("Very Short Sleep")
            elif self.sleep_hours < 6:
                self.sleep_tags.append("Short Sleep")
            elif self.sleep_hours > 10:
                self.sleep_tags.append("Long Sleep")
            # determine if sleep was during the day
            if 6 < self.bed_time.hour < 18 and self.wake_time > self.bed_time:
                self.sleep_tags.append("Daytime Sleep")  
        return self
    
    def createDreamEntry(self) -> DreamEntry:
        entry = DreamEntry(**self.model_dump(exclude={'content_tags', 'type_tags', 'context_tags', 'sleep_tags'}))
        entry.created_at = datetime.now()   
        return entry
    
    @property
    def all_tags(self):
        return self.content_tags + self.type_tags + self.context_tags + self.sleep_tags
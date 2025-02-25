from pydantic import BaseModel
from typing import List, Optional

class TopicBase(BaseModel):
    name: str

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: int

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    name: str
    number: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    topics: List[Topic] = []

    class Config:
        from_attributes = True
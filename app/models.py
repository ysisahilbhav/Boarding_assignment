from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    number = Column(Integer, index=True)
    topics = relationship("Topic", secondary="student_topics", back_populates="students")

class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    students = relationship("Student", secondary="student_topics", back_populates="topics")

student_topics = Table(
    'student_topics',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('topic_id', Integer, ForeignKey('topics.id'))
)
from sqlalchemy.orm import Session
import models, schemas
from database import redis_client, USE_REDIS
import uuid

def get_student(db: Session, student_id: int):
    if USE_REDIS:
        student = redis_client.hgetall(f"student:{student_id}")
        if student:
            # Convert Redis hash values from bytes to appropriate types
            student = {k.decode('utf-8'): v.decode('utf-8') for k, v in student.items()}
            student['id'] = int(student['id'])
            student['number'] = int(student['number'])
            return schemas.Student(**student)
    return db.query(models.Student).filter(models.Student.id == student_id).first()

def create_student(db: Session, student: schemas.StudentCreate):
    if USE_REDIS:
        student_id = redis_client.incr("student_id_counter") # Generate a unique ID
        db_student = models.Student(name=student.name, number=student.number)
        db_student.id=student_id
        redis_client.hmset(f"student:{student_id}", {
            "id": student_id,
            "name": db_student.name,
            "number": db_student.number
        })
        redis_client.rpush("students", db_student.id)
    else:
        db_student = models.Student(name=student.name, number=student.number)
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    db.delete(db_student)
    db.commit()
    return db_student
    
def assign_topic_to_student(db: Session, student_id: int, topic_id: int):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not db_student or not db_topic:
        return "Either the specified topic id or the student id does not exit"  # Handle the case where the student or topic does not exist
    db_student.topics.append(db_topic)
    db.commit()
    return db_student

def create_topic(db: Session, topic: schemas.TopicCreate):
    if USE_REDIS:
        topic_id = redis_client.incr("student_id_counter")
        db_topic = models.Topic(name=topic.name)
        db_topic.id=topic_id
        redis_client.hmset(f"Topic:{db_topic.id}", {
            "id": db_topic.id,
            "name": db_topic.name,
        })
        redis_client.rpush("topics", db_topic.id)
    else:
        db_topic = models.Topic(name=topic.name)
        db.add(db_topic)
        db.commit()
        db.refresh(db_topic)
    return db_topic

def delete_topic(db: Session, topic_id: int):
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    db.delete(db_topic)
    db.commit()
    return db_topic

def get_topic(db: Session, topic_id: int):
    if USE_REDIS:
        topic = redis_client.hgetall(f"topic:{topic_id}")
        if topic:
            # Convert Redis hash values from bytes to appropriate types
            topic = {k.decode('utf-8'): v.decode('utf-8') for k, v in topic.items()}
            topic['id'] = int(topic['id'])
            topic['name'] = int(topic['name'])
            return schemas.Student(**topic)
    return db.query(models.Topic).filter(models.Topic.id == topic_id).first()


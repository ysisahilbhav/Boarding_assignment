from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request
from sqlalchemy.orm import Session
import ysecret.SecretManager
from crud import create_student as crud_create_student, get_student, delete_student, assign_topic_to_student, create_topic as crud_create_topic
# from . import models, schemas
import models, schemas
from database import SessionLocal, engine, database
import uvicorn
import yocr
from PIL import Image
import io,os
import asyncio
from pydantic import BaseModel
import openai
import base64
from dotenv import load_dotenv

# Initialize a global variable to track the number of concurrent processes
process_counter = 0
max_concurrent_processes = 3
queue_lock = asyncio.Semaphore(max_concurrent_processes)
models.Base.metadata.create_all(bind=engine)

class ImageSummary(BaseModel):
    summary: str
    number_of_words: int

app = FastAPI()
# # Load environment variables from .env file
# load_dotenv()

# # Get the variables
# openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI( api_key=os.getenv("OPENAI_API_KEY"))
THIS_MODEL = "gpt-4o-mini"

# ocr=yocr()
# @app.on_event("startup")
# async def startup():
#     await database.connect()

# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Middleware to limit concurrent processes globally
@app.middleware("http")
async def limit_concurrent_requests(request, call_next):
    global process_counter

    # Check if the number of active processes is less than the max allowed
    if process_counter >= max_concurrent_processes:
        raise HTTPException(status_code=500, detail="Too many processes are running")

    # Increment the process counter before processing the request
    process_counter += 1

    try:
        # Call the endpoint function
        response = await call_next(request)
        return response
    finally:
        # Decrement the process counter after the request is processed
        process_counter -= 1

@app.get("/")
def test():
    return {"message":"This is a test API"}

@app.post("/students/", response_model=schemas.Student)
def create_student_route(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    return crud_create_student(db=db, student=student)
    # return{"message":"Hello"}

@app.get("/students/{student_id}", response_model=schemas.Student)
def read_student(student_id: int, db: Session = Depends(get_db)):
    db_student = get_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@app.delete("/students/{student_id}", response_model=schemas.Student)
def delete_student_route(student_id: int, db: Session = Depends(get_db)):
    return delete_student(db=db, student_id=student_id)

@app.post("/students/{student_id}/topics/{topic_id}", response_model=schemas.Student)
def assign_topic(student_id: int, topic_id: int, db: Session = Depends(get_db)):
    return assign_topic_to_student(db=db, student_id=student_id, topic_id=topic_id)

@app.post("/topics/", response_model=schemas.Topic)
def create_topic_route(topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    return crud_create_topic(db=db, topic=topic)



@app.post("/upload/", response_model=ImageSummary)
async def upload_image(file: UploadFile = File(...)):
    # from ysecret import SecretManager
    # secrets=SecretManager.SecretManager(False)
    # s=secrets.get_secret_with_id(1)
    # print(s)
    # Read the uploaded file
    image = Image.open(io.BytesIO(await file.read()))

    # Convert the image to bytes
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    image_bytes = buffered.getvalue()

    # Encode the bytes to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # Initialize OpenAI client
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=openai.api_key)
    THIS_MODEL = "gpt-4o-mini"

    # Send the request to the API
    response = client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a cool image analyst. Your goal is to describe what is in the image provided as a file."
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )

    # Extract the description
    description = response.choices[0].message.content
    number_of_words = len(description.split())

    return {"summary": description, "number_of_words": number_of_words}



def run():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run()



    
    print(f"response: {response}")
    # Extract the description
    description = response.choices[0].message.content
    print(f"Desription: {description}")
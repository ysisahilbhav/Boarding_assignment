from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request
from sqlalchemy.orm import Session
import ysecret.SecretManager
from crud import create_student as crud_create_student, get_student, delete_student, assign_topic_to_student, create_topic as crud_create_topic,get_topic,delete_topic
import models, schemas
from database import SessionLocal, engine, database
from PIL import Image
import io, os, asyncio, openai, base64, logging, yocr, uvicorn
from pydantic import BaseModel
from dotenv import load_dotenv
from pydantic_settings import BaseSettings



models.Base.metadata.create_all(bind=engine)
app = FastAPI()
logging.basicConfig(level=logging.INFO)

client = openai.OpenAI( api_key=os.getenv("OPENAI_API_KEY"))
THIS_MODEL = "gpt-4o-mini"

process_counter = 0
max_concurrent_processes = 3
queue_lock = asyncio.Semaphore(max_concurrent_processes)
models.Base.metadata.create_all(bind=engine)


#Pydantic classes
class ImageSummary(BaseModel):
    summary: str
    number_of_words: int

class Student(BaseModel):
    name : str
    number : int

class Settings(BaseSettings):
    app_name: str
    class Config:
        env_file = ".env"

class StudentResponse(BaseModel):
    message: str
    student: schemas.Student

class TopicResponse(BaseModel):
    message: str
    topic: schemas.Topic

settings = Settings()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.middleware("http")
async def limit_concurrent_requests(request, call_next):
    global process_counter

    if process_counter >= max_concurrent_processes:
        raise HTTPException(status_code=500, detail="Too many processes are running")

    process_counter += 1
    try:
        response = await call_next(request)
        return response
    finally:
        process_counter -= 1

#ROUTES/END-POINTS
@app.get("/")
def test():
    return {"message":"This is a test API"}

@app.get("/env")
def get_env_variables():
     return {
        "app_name": settings.app_name,
    }

@app.post("/students/",response_model=StudentResponse)
def create_student_route(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    try:
        if student.name == "error" or student.number<1:
            raise ValueError("Value error")
        logging.info(f"Student name : {student.name},Student number : {student.number}")
        db_student=crud_create_student(db=db, student=student)
        return {"message" : "Added successfully !!!", "student": db_student}

    except Exception as e:
        raise HTTPException(status_code=500,detail="An error occured!!")

@app.get("/students/{student_id}", response_model=schemas.Student)
def read_student(student_id: int, db: Session = Depends(get_db)):
    db_student = get_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@app.delete("/students/{student_id}", response_model=StudentResponse)
def delete_student_route(student_id: int, db: Session = Depends(get_db)):
    db_student=delete_student(db=db, student_id=student_id)
    return {"message" : "Deleted Successfully !!!", "student": db_student}

@app.post("/students/{student_id}/topics/{topic_id}")
def assign_topic(student_id: int, topic_id: int, db: Session = Depends(get_db)):
    db_student=assign_topic_to_student(db=db, student_id=student_id, topic_id=topic_id)
    return {"message" : "Assigned Successfully !!!"}

@app.post("/topics/", response_model=TopicResponse)
def create_topic_route(topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    db_topic=crud_create_topic(db=db, topic=topic)
    return {"message" : "Topic added Successfully !!!", "topic": db_topic}

@app.get("/topics/{topic_id}", response_model=schemas.Topic)
def read_topic(topic_id: int, db: Session = Depends(get_db)):
    db_topic = get_topic(db, topic_id=topic_id )
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return db_topic

@app.delete("/topic/{topic_id}", response_model=TopicResponse)
def delete_topic_route(topic_id: int, db: Session = Depends(get_db)):
    db_topic=delete_topic(db=db, topic_id=topic_id)
    return {"message" : "Deleted Successfully !!!", "topic": db_topic}

@app.post("/upload/", response_model=dict)
def upload_image(file: UploadFile = File(...)):
    from yocr.OCRConfig import OCRConfig, InferenceType
    from yocr.OCR import OCR
    from yocr.OCRConfig import OCRConfig, OCRMethod
    from yocr.data_struct.OcrResult import OcrResult
    config = OCRConfig(METHOD=OCRMethod.tesseract, CONFIG_PATH="config.json")
    config.INFERENCE_TYPE = InferenceType.TILE
    config.TILE_ROW_COUNT = 3
    config.TILE_COL_COUNT = 3
    config.TILE_OVERLAP = 300  # px
    ocr = OCR(config)
    [OcrResult] = ocr(image="image.png")
    image = Image.open(io.BytesIO(file.read()))
    text = yocr.r(image)
    return {"extracted_text": text}

@app.post("/upload-gpt/", response_model=ImageSummary)
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

    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=openai.api_key)
    THIS_MODEL = "gpt-4o-mini"

    response = client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a cool image analyst. Your goal is to describe what is in the image provided as a file IN LESS THAN 5 WORDS"
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

    description = response.choices[0].message.content
    number_of_words = len(description.split())

    return {"summary": description, "number_of_words": number_of_words}

def run():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run()
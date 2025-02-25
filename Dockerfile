
FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
COPY app/yocr-0.0.22.tar.gz .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install yocr-0.0.22.tar.gz

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
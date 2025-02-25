from locust import HttpUser, task, between
import random

class ApiUser(HttpUser):
    # Set the wait time between each task to be between 1 and 3 seconds
    wait_time = between(1, 3)

    @task
    def test_root(self):
        # This task simulates a GET request to the root ("/") endpoint
        self.client.get("/")

    @task
    def create_student(self):
        # This task simulates a POST request to the "/students/" endpoint
        student_data = {
            "name": "Test",
            "number": random.randint(18, 30)  # Random age between 18 and 30
        }
        self.client.post("/students/", json=student_data)

    @task
    def read_student(self):
        # This task simulates a GET request to the "/students/{student_id}" endpoint
        student_id = 4  # Random student ID between 1 and 10
        self.client.get(f"/students/{student_id}")

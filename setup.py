from setuptools import setup, find_packages

# with open("app/requirements.txt") as f:
#     requirements = f.read().splitlines()

setup(
    name="FastAPI_App",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "redis"
        # Add other dependencies here
    ],
    entry_points={
        'console_scripts': [
            'start-app=app.main:run',  # Replace with the correct path to your main.py file
        ],
    },
)
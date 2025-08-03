from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3307)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "your_password"),
    database=os.getenv("DB_NAME", "bank_db")
)
cursor = conn.cursor()

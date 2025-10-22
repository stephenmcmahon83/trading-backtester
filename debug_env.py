from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

print("DATABASE_URL from .env file:")
print(DATABASE_URL)
print("\n")
print("Password extracted:")
# Extract password (between : and @)
if DATABASE_URL:
    parts = DATABASE_URL.split('@')[0]
    password = parts.split(':')[-1]
    print(f"'{password}'")
else:
    print("DATABASE_URL is None - .env file not loaded!")
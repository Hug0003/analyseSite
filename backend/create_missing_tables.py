from app.db.session import engine
from sqlmodel import SQLModel
# Explicitly import models to register them
from app.models.user import User
from app.models.api_key import ApiKey

def fix():
    print("Registered tables in SQLModel metadata:", SQLModel.metadata.tables.keys())
    print("Creating all tables...")
    SQLModel.metadata.create_all(engine)
    print("Done.")

if __name__ == "__main__":
    fix()

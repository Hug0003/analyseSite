"""
Create Admin Script (CLI version)
Usage: python scripts/create_superuser_cli.py <email> <password>
"""
import sys
import os
import argparse

# Add backend directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models.user import User
from app.core.security import get_password_hash

def create_admin(email, password, full_name="Admin User"):
    print(f"--- Creating Superuser: {email} ---")
    
    with Session(engine) as session:
        # Check if user exists
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if user:
            print(f"User {email} already exists.")
            if not user.is_superuser:
                print("Promoting to superuser...")
                user.is_superuser = True
                user.is_active = True
                user.is_verified = True
                session.add(user)
                session.commit()
                print(f"User {email} is now an admin.")
            else:
                print("User is already an admin.")
        else:
            print("Creating new user...")
            hashed_password = get_password_hash(password)
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True,
                is_verified=True,
                is_superuser=True
            )
            session.add(new_user)
            session.commit()
            print(f"Superuser {email} created successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_superuser_cli.py <email> <password>")
        sys.exit(1)
        
    email_arg = sys.argv[1]
    password_arg = sys.argv[2]
    
    create_admin(email_arg, password_arg)

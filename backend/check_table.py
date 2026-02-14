from app.db.session import engine
from sqlalchemy import text

def check():
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT count(*) FROM api_keys"))
            print(f"Table api_keys exists. Count: {res.scalar()}")
    except Exception as e:
        print(f"Error checking table: {e}")

if __name__ == "__main__":
    check()

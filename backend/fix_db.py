from app.db.session import engine
from sqlalchemy import text

def fix():
    with engine.connect() as conn:
        print("Dropping api_keys table...")
        conn.execute(text("DROP TABLE IF EXISTS api_keys CASCADE"))
        conn.commit()
        print("Done. The table will be recreated on next server startup.")

if __name__ == "__main__":
    fix()

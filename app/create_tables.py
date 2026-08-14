from app.database import Base, engine
from app import models

def init_db():
    Base.metadata.create_all(engine)
    print("Tables created.")

if __name__ == "__main__":
    init_db()
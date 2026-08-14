from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.config import settings


engine = create_engine(url = settings.database_url)

SessionLocal = sessionmaker(bind = engine)

def get_db():
    db = SessionLocal() # Open a fresh session for this request.
    try:
        yield db # hand it to the route; route runs HERE.
    finally:
        db.close() # always runs, even if the route raised.


        
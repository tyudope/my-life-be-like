from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.database import get_db
from app.schemas import BookCreate, BookRead, BookUpdate
from app.models import Book

from sqlalchemy import select

router = APIRouter(prefix = "/books", tags = ["books"])



@router.post("", response_model = BookRead)
def create_book(payload:BookCreate, db:Session = Depends(get_db)):

    db_book = Book(**payload.model_dump())

    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    return db_book



@router.get("", response_model = list[BookRead])
def read_books(db:Session = Depends(get_db)):

    books = db.scalars(select(Book)).all()
    return books
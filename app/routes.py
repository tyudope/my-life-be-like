from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
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


@router.get("/{book_id}", response_model=BookRead)
def read_book_by_id(book_id:int, db:Session = Depends(get_db)):

    book = db.get(Book, book_id)
    if book is None:
        return HTTPException(status_code=404, detail = "Book not found.")
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_by_id(book_id:int, db:Session=Depends(get_db)):

    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")

    db.delete(book)
    db.commit()
    return None


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id:int, payload:BookUpdate, db:Session = Depends(get_db)):
    book = db.get(Book, book_id)

    if book is None:
        raise HTTPException(status_code=404, detail = "Book not found.")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book
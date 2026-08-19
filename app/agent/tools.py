from app.models import Book
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select




def get_books(db:Session, status:str = "all"):
    stmt = select(Book)

    if status == "ongoing":
        stmt = stmt.where(Book.completed_page < Book.total_page)

    elif status == "completed":
        stmt = stmt.where(Book.completed_page == Book.total_page)


    # "all" -> no filter.
    books = db.scalars(stmt).all()

    return[
        {"name":b.name, "completed_page":b.completed_page, "total_page":b.total_page} for b in books
    ]


GET_BOOKS_TOOL = {
    "name":"get_books",
    "description":"Retrieves the user's books and their reading progress, filtered by status. Use this when the user asks about their reading, "
                 "their progress, or wants book recommendations (call it first to see what they've already read  and their taste)",# prompt
    "input_schema":{
        "type":"object",
        "properties":{
            "status":{
                "type":"string",
                "enum":["all","ongoing", "completed"],
                "description":"Which books to return 'all' for every book, 'ongoing' for books still being read(not yet finished), 'completed' for books fully read. Defaults to 'all'"
            }
        },
        "required":[] # status has a default, so not required.
    }
}


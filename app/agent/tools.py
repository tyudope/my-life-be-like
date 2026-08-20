from app.models import Book, BodyWeight, Exercise, ExerciseSet, Workout
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


def get_exercise_history(db: Session, exercise_name: str, limit: int = 20):
    stmt = (
        select(ExerciseSet, Exercise, Workout)
        .join(Exercise, ExerciseSet.exercise_id == Exercise.id)
        .join(Workout, ExerciseSet.workout_id == Workout.id)
        .where(Exercise.name.ilike(f"%{exercise_name}%"))
        .order_by(Workout.date.desc(), ExerciseSet.set_number.asc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()

    return [
        {
            "exercise": exercise.name,
            "workout": workout.name,
            "date": workout.date.isoformat(),
            "set_number": ex_set.set_number,
            "weight": ex_set.weight,
            "reps": ex_set.reps,
        }
        for ex_set, exercise, workout in rows
    ]


GET_EXERCISE_HISTORY_TOOL = {
    "name": "get_exercise_history",
    "description": "Retrieves past sets logged for a given exercise (weight, reps, set number, workout, date), most recent first. "
                    "Use this before giving any advice on progression, form, deload, or plateaus for a specific lift — "
                    "you need to see what the user actually did before judging whether they should add weight, hold, or back off.",
    "input_schema": {
        "type": "object",
        "properties": {
            "exercise_name": {
                "type": "string",
                "description": "Name (or partial name) of the exercise to look up, e.g. 'bench press' or 'squat'. Matched case-insensitively."
            },
            "limit": {
                "type": "integer",
                "description": "Max number of sets to return, most recent first. Defaults to 20."
            }
        },
        "required": ["exercise_name"]
    }
}


def get_bodyweight(db: Session, limit: int = 30):
    stmt = select(BodyWeight).order_by(BodyWeight.date.desc()).limit(limit)
    rows = db.scalars(stmt).all()

    # returned oldest -> newest so a trend reads left-to-right, same way a chart would
    return [
        {"weight": entry.weight, "date": entry.date.isoformat()}
        for entry in reversed(rows)
    ]


GET_BODYWEIGHT_TOOL = {
    "name": "get_bodyweight",
    "description": "Retrieves the user's recent bodyweight log, ordered oldest to newest. Use this when the user asks about "
                    "weight trend, cutting/bulking progress, or when deciding whether training load or nutrition advice "
                    "should account for a change in bodyweight.",
    "input_schema": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Max number of most recent entries to return. Defaults to 30."
            }
        },
        "required": []
    }
}


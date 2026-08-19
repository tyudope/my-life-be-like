from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models import Book, BodyWeight, Exercise, Workout, ExerciseSet
from app.schemas import (
    BookCreate, BookRead, BookUpdate,
    BodyWeightCreate, BodyWeightRead, BodyWeightUpdate,
    ExerciseCreate, ExerciseRead, ExerciseUpdate,
    WorkoutCreate, WorkoutRead, WorkoutUpdate,
    ExerciseSetCreate, ExerciseSetRead, ExerciseSetUpdate,
)

router = APIRouter()


# ---------- Books ----------
books = APIRouter(prefix="/books", tags=["books"])

@books.post("", response_model=BookRead)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@books.get("", response_model=list[BookRead])
def read_books(db: Session = Depends(get_db)):
    return db.scalars(select(Book)).all()

@books.get("/{book_id}", response_model=BookRead)
def read_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@books.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book

@books.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()


# ---------- Bodyweight ----------
bodyweight = APIRouter(prefix="/bodyweight", tags=["bodyweight"])

@bodyweight.post("", response_model=BodyWeightRead)
def create_bodyweight(payload: BodyWeightCreate, db: Session = Depends(get_db)):
    entry = BodyWeight(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@bodyweight.get("", response_model=list[BodyWeightRead])
def read_bodyweights(db: Session = Depends(get_db)):
    return db.scalars(select(BodyWeight)).all()

@bodyweight.get("/{entry_id}", response_model=BodyWeightRead)
def read_bodyweight(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(BodyWeight, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Bodyweight entry not found")
    return entry

@bodyweight.patch("/{entry_id}", response_model=BodyWeightRead)
def update_bodyweight(entry_id: int, payload: BodyWeightUpdate, db: Session = Depends(get_db)):
    entry = db.get(BodyWeight, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Bodyweight entry not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry

@bodyweight.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bodyweight(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(BodyWeight, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Bodyweight entry not found")
    db.delete(entry)
    db.commit()


# ---------- Exercises ----------
exercises = APIRouter(prefix="/exercises", tags=["exercises"])

@exercises.post("", response_model=ExerciseRead)
def create_exercise(payload: ExerciseCreate, db: Session = Depends(get_db)):
    exercise = Exercise(**payload.model_dump())
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise

@exercises.get("", response_model=list[ExerciseRead])
def read_exercises(db: Session = Depends(get_db)):
    return db.scalars(select(Exercise)).all()

@exercises.get("/{exercise_id}", response_model=ExerciseRead)
def read_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@exercises.patch("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(exercise_id: int, payload: ExerciseUpdate, db: Session = Depends(get_db)):
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exercise, field, value)
    db.commit()
    db.refresh(exercise)
    return exercise

@exercises.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    db.delete(exercise)
    db.commit()


# ---------- Workouts ----------
workouts = APIRouter(prefix="/workouts", tags=["workouts"])

@workouts.post("", response_model=WorkoutRead)
def create_workout(payload: WorkoutCreate, db: Session = Depends(get_db)):
    workout = Workout(**payload.model_dump())
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout

@workouts.get("", response_model=list[WorkoutRead])
def read_workouts(db: Session = Depends(get_db)):
    return db.scalars(select(Workout)).all()

@workouts.get("/{workout_id}", response_model=WorkoutRead)
def read_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout

@workouts.patch("/{workout_id}", response_model=WorkoutRead)
def update_workout(workout_id: int, payload: WorkoutUpdate, db: Session = Depends(get_db)):
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workout, field, value)
    db.commit()
    db.refresh(workout)
    return workout

@workouts.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(workout)
    db.commit()


# ---------- Exercise sets ----------
sets = APIRouter(prefix="/sets", tags=["sets"])

@sets.post("", response_model=ExerciseSetRead)
def create_set(payload: ExerciseSetCreate, db: Session = Depends(get_db)):
    # verify the referenced workout and exercise exist → clean 404 instead of a raw DB error
    if db.get(Workout, payload.workout_id) is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    if db.get(Exercise, payload.exercise_id) is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    ex_set = ExerciseSet(**payload.model_dump())
    db.add(ex_set)
    db.commit()
    db.refresh(ex_set)
    return ex_set

@sets.get("", response_model=list[ExerciseSetRead])
def read_sets(db: Session = Depends(get_db)):
    return db.scalars(select(ExerciseSet)).all()

@sets.get("/{set_id}", response_model=ExerciseSetRead)
def read_set(set_id: int, db: Session = Depends(get_db)):
    ex_set = db.get(ExerciseSet, set_id)
    if ex_set is None:
        raise HTTPException(status_code=404, detail="Set not found")
    return ex_set

@sets.patch("/{set_id}", response_model=ExerciseSetRead)
def update_set(set_id: int, payload: ExerciseSetUpdate, db: Session = Depends(get_db)):
    ex_set = db.get(ExerciseSet, set_id)
    if ex_set is None:
        raise HTTPException(status_code=404, detail="Set not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ex_set, field, value)
    db.commit()
    db.refresh(ex_set)
    return ex_set

@sets.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(set_id: int, db: Session = Depends(get_db)):
    ex_set = db.get(ExerciseSet, set_id)
    if ex_set is None:
        raise HTTPException(status_code=404, detail="Set not found")
    db.delete(ex_set)
    db.commit()


# ---------- Combine all ----------
router.include_router(books)
router.include_router(bodyweight)
router.include_router(exercises)
router.include_router(workouts)
router.include_router(sets)
from app.database import Base
from sqlalchemy import String, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


#Book
class Book(Base):

    __tablename__ = "book"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index = True)
    name:Mapped[str] = mapped_column(String(100))
    total_page:Mapped[int]
    completed_page:Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


# Exercise
class Exercise(Base):
    __tablename__ = "exercise"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index = True)
    name:Mapped[str] = mapped_column(String(100), nullable=False)


# Workout
class Workout(Base):
    __tablename__ = "workout"

    id:Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str] = mapped_column(String(20), nullable=False)
    date:Mapped[datetime] = mapped_column(server_default=func.now())
    sets:Mapped[list["ExerciseSet"]] = relationship(back_populates="workout")



# ExerciseSet

class ExerciseSet(Base):

    __tablename__ = "exerciseset"

    id:Mapped[int] = mapped_column(primary_key=True)
    weight:Mapped[float]
    set_number:Mapped[int]
    reps:Mapped[int]
    workout_id:Mapped[int] = mapped_column(ForeignKey("workout.id"))
    exercise_id:Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    workout:Mapped["Workout"] = relationship(back_populates="sets")
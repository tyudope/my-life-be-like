from pydantic import Field, BaseModel, ConfigDict

from datetime import datetime

class StrictModel(BaseModel):
    model_config = ConfigDict(extra = "forbid")


# Book schemas
class BookCreate(StrictModel):

    name:str = Field(..., max_length=100)
    total_page:int = Field(...)
    completed_page:int = Field(default=0) # optional, a new book starts at 0

# This is what comes back from the database
class BookRead(StrictModel):

    model_config = ConfigDict(from_attributes=True)

    id:int = Field(...)
    name:str = Field(..., max_length=100)
    total_page:int = Field(...)
    completed_page:int = Field(...)
    created_at:datetime = Field(...)


class BookUpdate(StrictModel):
    name:str | None = Field(default=None, max_length=100)
    total_page:int | None = Field(default=None)
    completed_page:int | None = Field(default=None)



# Bodyweight schemas

class BodyWeightCreate(StrictModel):

    weight:float = Field(...)


class BodyWeightRead(StrictModel):
    model_config = ConfigDict(from_attributes=True)

    id:int = Field(...)
    weight:float = Field(...)
    date:datetime = Field(...)


class BodyWeightUpdate(StrictModel):
    weight:float | None = Field(default=None)


# Exercise schemas

class ExerciseCreate(StrictModel):

    name:str = Field(..., max_length=100)

class ExerciseRead(StrictModel):
    model_config = ConfigDict(from_attributes=True)
    id:int = Field(...)
    name:str = Field(...)

class ExerciseUpdate(StrictModel):

    name:str | None = Field(default=None, max_length=100)





# Workout schemas
class WorkoutCreate(StrictModel):

    name:str = Field(..., max_length=20)


class WorkoutRead(StrictModel):

    model_config = ConfigDict(from_attributes=True)

    id:int = Field(...)
    name:str = Field(..., max_length=20)
    date:datetime = Field(...)


class WorkoutUpdate(StrictModel):

    name:str | None = Field(default= None, max_length=20)


# ExerciseSet schemas

class ExerciseSetCreate(StrictModel):

    weight:float = Field(...)
    set_number:int = Field(...)
    reps:int = Field(...)
    workout_id:int = Field(...)
    exercise_id:int = Field(...)

class ExerciseSetRead(StrictModel):

    model_config = ConfigDict(from_attributes=True)

    id:int = Field(...)
    weight:float = Field(...)
    set_number:int = Field(...)
    reps:int = Field(...)
    workout_id:int = Field(...)
    exercise_id:int = Field(...)


class ExerciseSetUpdate(StrictModel):
    weight:float | None = Field(default=None)
    set_number:int | None = Field(default=None)
    reps:int | None = Field(default = None)

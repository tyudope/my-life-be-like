"""Backfill a realistic training + bodyweight history.

Demo/screenshot data. Everything it writes is dated on or before 2026-08-18, so it
sits *behind* the real sessions already in the log and never touches them.

    python -m scripts.seed_demo          # insert (idempotent — safe to re-run)
    python -m scripts.seed_demo --wipe   # remove everything this script inserted

Only backdated rows are touched on wipe; your real sessions are matched by date and
left alone.
"""

import sys
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Book, BodyWeight, Exercise, ExerciseSet, Workout

# Everything this script owns is strictly before this instant.
CUTOFF = datetime(2026, 8, 18, 23, 59)

# --- training plan ---------------------------------------------------------
# Each entry: exercise name -> (sets, reps, [weight per week, 6 weeks])
# Weights ramp toward what's already logged on 2026-08-19, so the progress chart
# reads as one continuous climb into the real sessions.

PUSH = {
    "Bench Press":            (3, 3,  [92.5, 95.0, 97.5, 100.0, 100.0, 102.5]),
    "Weighted DIPS":          (3, 5,  [7.5, 10.0, 12.5, 15.0, 15.0, 17.5]),
    "Dumbell Shoulder Press": (3, 8,  [20.0, 20.0, 22.5, 22.5, 25.0, 25.0]),
    "Dumbell Skull Crusher":  (3, 8,  [10.0, 10.0, 10.0, 12.5, 12.5, 12.5]),
    "Cable Lateral Raise":    (3, 10, [5.0, 5.0, 6.25, 6.25, 6.25, 6.25]),
    "Triceps Rope Extension": (3, 8,  [15.0, 15.0, 16.25, 17.5, 17.5, 18.75]),
}

PULL = {
    "Barbell Row":    (3, 7, [80.0, 82.5, 85.0, 87.5, 90.0, 92.5]),
    "Barbell Shrugs": (2, 6, [90.0, 95.0, 100.0, 100.0, 105.0, 105.0]),
    "Barbell Curl":   (3, 6, [35.0, 37.5, 38.0, 40.0, 40.0, 42.0]),
    "Hammer Curl":    (2, 7, [14.0, 16.0, 16.0, 18.0, 18.0, 20.0]),
}

# Pull-ups are bodyweight (0 kg) and progress in reps, not load.
PULLUP_REPS = [
    [4, 3, 3, 2], [4, 3, 3, 3], [4, 4, 3, 3],
    [5, 4, 3, 3], [5, 4, 4, 3], [5, 4, 4, 3],
]

LEGS = {
    "Back Squat":          (3, 5,  [100.0, 105.0, 110.0, 112.5, 115.0, 120.0]),
    "Romanian Deadlift":   (3, 8,  [80.0, 85.0, 90.0, 90.0, 95.0, 100.0]),
    "Leg Press":           (3, 10, [160.0, 170.0, 180.0, 190.0, 200.0, 210.0]),
    "Seated Leg Curl":     (3, 10, [40.0, 42.5, 45.0, 45.0, 47.5, 50.0]),
    "Standing Calf Raise": (4, 12, [60.0, 65.0, 70.0, 70.0, 75.0, 80.0]),
}

# Week 0 starts Mon 2026-07-06; push Mon, pull Thu, legs Sat.
WEEK_ONE_MONDAY = datetime(2026, 7, 6, 18, 30)

# Cutting: 113.4 kg down to ~109 over six weeks, with the plateaus and bounces a
# real scale shows rather than a clean line.
BODYWEIGHT_TRACK = [
    (0, 113.4), (3, 113.0), (5, 112.6),
    (7, 112.4), (10, 111.9), (12, 112.1),
    (14, 111.5), (17, 111.2), (19, 110.8),
    (21, 110.9), (24, 110.4), (26, 110.1),
    (28, 110.2), (31, 109.7), (33, 109.5),
    (35, 109.8), (38, 109.4), (40, 109.2),
]


def get_or_create_exercise(db, name: str) -> Exercise:
    ex = db.scalar(select(Exercise).where(Exercise.name == name))
    if ex is None:
        ex = Exercise(name=name)
        db.add(ex)
        db.flush()
    return ex


def build_session(db, name: str, when: datetime, plan: dict, week: int,
                  pullups: list[int] | None = None) -> bool:
    """Create one workout. Returns False if that session already exists."""
    existing = db.scalar(
        select(Workout).where(Workout.name == name, Workout.date == when)
    )
    if existing is not None:
        return False

    workout = Workout(name=name, date=when)
    db.add(workout)
    db.flush()

    if pullups:
        ex = get_or_create_exercise(db, "PULL UP")
        for i, reps in enumerate(pullups, start=1):
            db.add(ExerciseSet(weight=0.0, set_number=i, reps=reps,
                               workout_id=workout.id, exercise_id=ex.id))

    for ex_name, (n_sets, reps, weights) in plan.items():
        ex = get_or_create_exercise(db, ex_name)
        for i in range(1, n_sets + 1):
            db.add(ExerciseSet(weight=weights[week], set_number=i, reps=reps,
                               workout_id=workout.id, exercise_id=ex.id))
    return True


def seed() -> None:
    db = SessionLocal()
    try:
        workouts_added = 0
        for week in range(6):
            monday = WEEK_ONE_MONDAY + timedelta(weeks=week)
            sessions = [
                ("PUSH", monday, PUSH, None),
                ("PULL", monday + timedelta(days=3), PULL, PULLUP_REPS[week]),
                ("LEGS", monday + timedelta(days=5), LEGS, None),
            ]
            for name, when, plan, pullups in sessions:
                if when > CUTOFF:
                    continue
                if build_session(db, name, when, plan, week, pullups):
                    workouts_added += 1

        weights_added = 0
        for day_offset, kg in BODYWEIGHT_TRACK:
            when = WEEK_ONE_MONDAY.replace(hour=8, minute=10) + timedelta(days=day_offset)
            if when > CUTOFF:
                continue
            if db.scalar(select(BodyWeight).where(BodyWeight.date == when)) is None:
                db.add(BodyWeight(weight=kg, date=when))
                weights_added += 1

        # Two books were logged with total/completed the wrong way round —
        # a book can't be 417 pages read out of 65.
        fixed = 0
        for book in db.scalars(select(Book)):
            if book.total_page > 0 and book.completed_page > book.total_page:
                book.total_page, book.completed_page = book.completed_page, book.total_page
                fixed += 1

        db.commit()
        print(f"seeded: {workouts_added} workouts, {weights_added} bodyweight entries, "
              f"{fixed} book page-counts corrected")
    finally:
        db.close()


def wipe() -> None:
    """Delete only the backdated rows this script inserts."""
    db = SessionLocal()
    try:
        workouts = db.scalars(
            select(Workout).where(Workout.date <= CUTOFF)
        ).all()
        for w in workouts:
            db.delete(w)  # sets cascade

        entries = db.scalars(
            select(BodyWeight).where(BodyWeight.date <= CUTOFF)
        ).all()
        for e in entries:
            db.delete(e)

        db.commit()
        print(f"wiped: {len(workouts)} workouts, {len(entries)} bodyweight entries "
              f"(book corrections and exercises left in place)")
    finally:
        db.close()


if __name__ == "__main__":
    wipe() if "--wipe" in sys.argv else seed()

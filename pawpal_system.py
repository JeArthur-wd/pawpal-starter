"""PawPal+ logic layer: backend classes for pet care planning."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from itertools import combinations
from typing import Optional

# Plans never span days, so all time arithmetic is anchored to one arbitrary date.
_ANCHOR = date(2000, 1, 1)


def _dt(t: time) -> datetime:
    """Convert a time of day to a datetime on the anchor date for arithmetic."""
    return datetime.combine(_ANCHOR, t)


def _fmt(dt: datetime) -> str:
    """Format a datetime as HH:MM."""
    return dt.strftime("%H:%M")


class Priority(Enum):
    """How important a task is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Frequency(Enum):
    """How often a task repeats."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


_PRIORITY_VALUES = {Priority.LOW: 1, Priority.MEDIUM: 2, Priority.HIGH: 3}
_RECURRENCE_STEP = {Frequency.DAILY: timedelta(days=1), Frequency.WEEKLY: timedelta(days=7)}


# eq=False: tasks compare by identity, so identical tasks for different pets stay distinct.
@dataclass(eq=False)
class Task:
    """A single unit of pet care (walk, feeding, meds, grooming, enrichment)."""

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: Optional[time] = None
    frequency: Frequency = Frequency.ONCE
    last_completed: Optional[date] = None
    due_date: Optional[date] = None  # None = due whenever; set on recurring copies
    pet_name: str = ""  # stamped by Pet.add_task
    scheduled_start: Optional[time] = None
    reason: str = ""

    def mark_complete(self, on: date) -> None:
        """Record that the task was completed on the given date."""
        self.last_completed = on

    def is_due(self, on: date) -> bool:
        """Return True if the task is not yet completed and its due date has arrived."""
        if self.last_completed is not None:
            return False
        return self.due_date is None or self.due_date <= on

    def priority_value(self) -> int:
        """Map priority to a number for sorting (higher = more important)."""
        return _PRIORITY_VALUES[self.priority]

    def next_occurrence(self, on: date) -> Optional[Task]:
        """Return an uncompleted copy due one day (daily) or week (weekly) after `on`, else None."""
        step = _RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        return replace(
            self, last_completed=None, due_date=on + step, scheduled_start=None, reason=""
        )


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str = "dog"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and stamp it with this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_pending_tasks(self, on: date) -> list[Task]:
        """Return tasks that are due and not yet completed on the given date."""
        return [t for t in self.tasks if t.is_due(on)]


@dataclass
class Owner:
    """The pet owner, whose time and preferences constrain the plan."""

    name: str
    available_minutes: int = 120
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


def _slot_start(task: Task) -> Optional[time]:
    """Return the time a task occupies: its scheduled start, else its preferred time."""
    return task.scheduled_start if task.scheduled_start is not None else task.preferred_time


def _span(task: Task) -> tuple[datetime, datetime]:
    """Return the (start, end) datetimes a timed task occupies."""
    start = _dt(_slot_start(task))
    return start, start + timedelta(minutes=task.duration_minutes)


class Scheduler:
    """Builds a daily plan from the owner's tasks and explains the choices."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []

    def generate_plan(self, on: date) -> list[Task]:
        """Choose and order tasks that fit the owner's time budget for the day.

        Tasks come from Owner.get_all_tasks() so every pet is covered. They are
        placed in priority order, each into the earliest free slot at or after its
        preferred time, until the time budget or the end of the day runs out.
        """
        self.plan = []
        self.skipped = []

        day_start = _dt(self.owner.day_start)
        day_end = _dt(self.owner.day_end)
        remaining = self.owner.available_minutes
        busy: list[tuple[datetime, datetime]] = []  # placed slots, kept sorted

        due = [t for t in self.owner.get_all_tasks() if t.is_due(on)]
        for task in self.sort_tasks(due):
            task.scheduled_start = None

            if task.duration_minutes > remaining:
                task.reason = (
                    f"needs {task.duration_minutes} min but only "
                    f"{remaining} min of the time budget is left."
                )
                self.skipped.append(task)
                continue

            earliest = day_start
            if task.preferred_time is not None:
                earliest = max(day_start, _dt(task.preferred_time))
            start = self._find_slot(busy, earliest, task.duration_minutes)
            end = start + timedelta(minutes=task.duration_minutes)

            if end > day_end:
                task.reason = f"no free slot before the day ends at {_fmt(day_end)}."
                self.skipped.append(task)
                continue

            busy.append((start, end))
            busy.sort()
            remaining -= task.duration_minutes
            task.scheduled_start = start.time()
            task.reason = self._placement_reason(task, start, day_start)
            self.plan.append(task)

        self.plan.sort(key=lambda t: t.scheduled_start)
        return self.plan

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority, then preferred time (unset last), then shortest first."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority_value(),
                t.preferred_time is None,
                t.preferred_time or time.min,
                t.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by the time they occupy (scheduled start, else preferred time); untimed last.

        Keys are `datetime.time` objects, which compare chronologically, so no string
        parsing is needed. (Zero-padded "HH:MM" strings would also sort correctly.)
        """
        return sorted(
            tasks, key=lambda t: (_slot_start(t) is None, _slot_start(t) or time.min)
        )

    def filter_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks (default: all the owner's) by pet name and/or completion status.

        A criterion left as None is ignored, so the filters can be combined freely.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return [
            t
            for t in tasks
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or (t.last_completed is not None) == completed)
        ]

    def mark_task_complete(self, task: Task, on: date) -> Optional[Task]:
        """Complete a task and, if it recurs, add its next occurrence to the same pet.

        Returns the newly created task, or None for a one-off task or one that was
        already completed (so completing twice never creates a duplicate).
        """
        if task.last_completed is not None:
            return None
        task.mark_complete(on)
        following = task.next_occurrence(on)
        if following is not None:
            for pet in self.owner.pets:
                if task in pet.tasks:  # Task uses identity equality, so this is exact
                    pet.add_task(following)
                    break
        return following

    def conflict_warnings(self, on: date, tasks: Optional[list[Task]] = None) -> list[str]:
        """Return a warning message for each pair of timed tasks whose windows overlap.

        Covers tasks for the same pet and for different pets (default: every task
        due on `on`). Never raises; an empty list means no conflicts.
        """
        if tasks is None:
            tasks = [t for t in self.owner.get_all_tasks() if t.is_due(on)]
        warnings = []
        for a, b in self._overlapping_pairs(tasks):
            (a_start, a_end), (b_start, b_end) = _span(a), _span(b)
            who = "same pet" if a.pet_name == b.pet_name else "different pets"
            warnings.append(
                f"Warning: '{a.title}' ({a.pet_name}, {_fmt(a_start)}-{_fmt(a_end)}) overlaps "
                f"'{b.title}' ({b.pet_name}, {_fmt(b_start)}-{_fmt(b_end)}) [{who}]"
            )
        return warnings

    def detect_conflicts(self) -> list[Task]:
        """Return planned tasks whose time slots overlap."""
        conflicted: list[Task] = []
        for a, b in self._overlapping_pairs(self.plan):
            for task in (a, b):
                if task not in conflicted:
                    conflicted.append(task)
        return conflicted

    @staticmethod
    def _overlapping_pairs(tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return every pair of timed tasks whose time windows overlap."""
        timed = [t for t in tasks if _slot_start(t) is not None]
        return [
            (a, b)
            for a, b in combinations(timed, 2)
            if _span(a)[0] < _span(b)[1] and _span(b)[0] < _span(a)[1]
        ]

    def explain_plan(self) -> str:
        """Describe why each task was scheduled or skipped."""
        if not self.plan and not self.skipped:
            return "No tasks to plan."

        lines = []
        if self.plan:
            lines.append("Planned:")
            for t in self.plan:
                start = _dt(t.scheduled_start)
                end = start + timedelta(minutes=t.duration_minutes)
                lines.append(
                    f"  {_fmt(start)}-{_fmt(end)}  {t.title} ({t.pet_name}) "
                    f"[{t.priority.value}] - {t.reason}"
                )
        if self.skipped:
            lines.append("Skipped:")
            for t in self.skipped:
                lines.append(f"  {t.title} ({t.pet_name}) [{t.priority.value}] - {t.reason}")
        return "\n".join(lines)

    @staticmethod
    def _find_slot(
        busy: list[tuple[datetime, datetime]], earliest: datetime, minutes: int
    ) -> datetime:
        """Return the earliest start at or after `earliest` that avoids every busy slot."""
        candidate = earliest
        length = timedelta(minutes=minutes)
        for b_start, b_end in busy:  # sorted by start
            if candidate + length <= b_start:
                break
            candidate = max(candidate, b_end)
        return candidate

    @staticmethod
    def _placement_reason(task: Task, start: datetime, day_start: datetime) -> str:
        """Explain in one sentence why the task landed at its start time."""
        base = f"{task.priority.value} priority"
        if task.preferred_time is None:
            return f"{base}, placed in the first free slot."
        preferred = _dt(task.preferred_time)
        if start == preferred:
            return f"{base}, scheduled at its preferred time."
        if preferred < day_start:
            return (
                f"{base}, preferred {_fmt(preferred)} is before the day starts at "
                f"{_fmt(day_start)}, so it starts then."
            )
        return (
            f"{base}, preferred {_fmt(preferred)} was already taken, "
            f"moved to the next free slot."
        )

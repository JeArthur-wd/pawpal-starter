"""PawPal+ logic layer: backend classes for pet care planning."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional

# Plans never span days, so all time arithmetic is anchored to one arbitrary date.
_ANCHOR = date(2000, 1, 1)
_WEEK = timedelta(days=7)


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
    pet_name: str = ""  # stamped by Pet.add_task
    scheduled_start: Optional[time] = None
    reason: str = ""

    def mark_complete(self, on: date) -> None:
        """Record that the task was completed on the given date."""
        self.last_completed = on

    def is_due(self, on: date) -> bool:
        """Return True if the task should appear in the plan for the given date."""
        if self.last_completed is None:
            return True
        if self.frequency is Frequency.ONCE:
            return False
        if self.frequency is Frequency.DAILY:
            return self.last_completed < on
        return on - self.last_completed >= _WEEK

    def priority_value(self) -> int:
        """Map priority to a number for sorting (higher = more important)."""
        return _PRIORITY_VALUES[self.priority]

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh, uncompleted copy for the next occurrence, or None for one-off tasks."""
        if self.frequency is Frequency.ONCE:
            return None
        return replace(self, last_completed=None, scheduled_start=None, reason="")


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

    def detect_conflicts(self) -> list[Task]:
        """Return planned tasks whose time slots overlap."""
        slots = [
            (t, _dt(t.scheduled_start), _dt(t.scheduled_start) + timedelta(minutes=t.duration_minutes))
            for t in self.plan
            if t.scheduled_start is not None
        ]
        conflicted: list[Task] = []
        for i, (task, start, end) in enumerate(slots):
            for other, o_start, o_end in slots[i + 1:]:
                if start < o_end and o_start < end:
                    for t in (task, other):
                        if t not in conflicted:
                            conflicted.append(t)
        return conflicted

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

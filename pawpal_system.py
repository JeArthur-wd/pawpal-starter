"""PawPal+ logic layer: backend classes for pet care planning (stubs only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


@dataclass
class Task:
    """A single unit of pet care (walk, feeding, meds, grooming, enrichment)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    preferred_time: Optional[time] = None
    frequency: str = "once"  # "once" | "daily" | "weekly"
    completed: bool = False
    pet_name: str = ""
    scheduled_start: Optional[time] = None
    reason: str = ""

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def is_due(self, on: date) -> bool:
        """Return True if the task should appear in the plan for the given date."""
        pass

    def priority_value(self) -> int:
        """Map priority to a number for sorting (higher = more important)."""
        pass

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh copy for the next occurrence, or None for one-off tasks."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str = "dog"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that have not been completed."""
        pass


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
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        pass


class Scheduler:
    """Builds a daily plan from the owner's tasks and explains the choices."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []

    def generate_plan(self, on: date) -> list[Task]:
        """Choose and order tasks that fit the owner's time budget for the day."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority, then preferred time or duration."""
        pass

    def detect_conflicts(self) -> list[Task]:
        """Return planned tasks whose time slots overlap."""
        pass

    def explain_plan(self) -> str:
        """Describe why each task was scheduled or skipped."""
        pass

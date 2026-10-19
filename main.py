"""Terminal demo for the PawPal+ logic layer."""

from datetime import date, datetime, time, timedelta

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task


def print_schedule(owner: Owner, scheduler: Scheduler, today: date) -> None:
    """Print the scheduler's plan as a readable table."""
    print(f"Today's Schedule for {owner.name} - {today:%A, %B %d, %Y}")
    print("=" * 66)
    print(f"{'Time':<13}{'Task':<18}{'Pet':<10}{'Priority':<10}{'Min':>4}")
    print("-" * 66)
    for task in scheduler.plan:
        start = datetime.combine(today, task.scheduled_start)
        end = start + timedelta(minutes=task.duration_minutes)
        print(
            f"{start:%H:%M}-{end:%H:%M}  {task.title:<18}{task.pet_name:<10}"
            f"{task.priority.value:<10}{task.duration_minutes:>4}"
        )
    print("-" * 66)

    planned = sum(t.duration_minutes for t in scheduler.plan)
    print(f"Planned {planned} of {owner.available_minutes} available minutes.")

    if scheduler.skipped:
        print("\nSkipped:")
        for task in scheduler.skipped:
            print(f"  {task.title} ({task.pet_name}): {task.reason}")

    print("\nWhy this plan:")
    for task in scheduler.plan:
        print(f"  {task.title} ({task.pet_name}): {task.reason}")


def print_tasks(tasks: list[Task]) -> None:
    """Print one task per line as 'HH:MM  Title (Pet)'."""
    for task in tasks:
        when = task.preferred_time.strftime("%H:%M") if task.preferred_time else "--:--"
        print(f"  {when}  {task.title} ({task.pet_name})")


def demo_algorithms(today: date) -> None:
    """Show sorting, filtering, conflict warnings and recurring tasks."""
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    whiskers = Pet("Whiskers", "cat")
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # Added deliberately out of time order.
    mochi.add_task(Task("Evening walk", 30, Priority.MEDIUM, time(18, 0), Frequency.DAILY))
    whiskers.add_task(Task("Give medication", 5, Priority.HIGH, time(12, 30)))
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, time(7, 30), Frequency.DAILY))
    whiskers.add_task(Task("Breakfast", 10, Priority.HIGH, time(8, 30), Frequency.DAILY))
    mochi.add_task(Task("Vet check-in call", 15, Priority.LOW, time(12, 30)))
    mochi.add_task(Task("Brush teeth", 5, Priority.LOW, time(7, 40)))
    whiskers.add_task(Task("Bath", 20, Priority.LOW, time(16, 0), Frequency.WEEKLY))
    whiskers.add_task(Task("Play session", 20, Priority.MEDIUM))

    scheduler = Scheduler(owner)
    all_tasks = owner.get_all_tasks()

    print("\n\n=== Sorting: tasks as entered ===")
    print_tasks(all_tasks)
    print("\n=== Sorting: Scheduler.sort_by_time() ===")
    print_tasks(scheduler.sort_by_time(all_tasks))

    print("\n=== Filtering: Scheduler.filter_tasks(pet_name='Mochi') ===")
    print_tasks(scheduler.filter_tasks(pet_name="Mochi"))

    print("\n=== Conflict detection: Scheduler.conflict_warnings() ===")
    for warning in scheduler.conflict_warnings(today):
        print(" ", warning)

    print("\n=== Recurring tasks: Scheduler.mark_task_complete() ===")
    for title in ("Morning walk", "Bath", "Give medication"):
        task = next(t for t in all_tasks if t.title == title)
        following = scheduler.mark_task_complete(task, today)
        if following:
            print(f"  Completed '{title}' ({task.frequency.value}) -> next due {following.due_date}")
        else:
            print(f"  Completed '{title}' (once) -> no next occurrence")

    print("\n=== Filtering by status: completed=True / completed=False ===")
    print("Completed:")
    print_tasks(scheduler.filter_tasks(completed=True))
    print(f"Still pending today ({today}):")
    print_tasks([t for t in scheduler.filter_tasks(completed=False) if t.is_due(today)])


def main() -> None:
    today = date.today()

    owner = Owner("Jordan", available_minutes=100)
    mochi = Pet("Mochi", "dog")
    whiskers = Pet("Whiskers", "cat")
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, time(7, 30), Frequency.DAILY))
    mochi.add_task(Task("Evening walk", 25, Priority.MEDIUM, time(18, 0), Frequency.DAILY))
    mochi.add_task(Task("Grooming", 45, Priority.LOW))
    whiskers.add_task(Task("Breakfast", 10, Priority.HIGH, time(8, 0), Frequency.DAILY))
    whiskers.add_task(Task("Give medication", 5, Priority.HIGH, time(12, 30)))
    whiskers.add_task(Task("Play session", 20, Priority.MEDIUM))

    scheduler = Scheduler(owner)
    scheduler.generate_plan(today)
    print_schedule(owner, scheduler, today)
    demo_algorithms(today)


if __name__ == "__main__":
    main()

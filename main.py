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


if __name__ == "__main__":
    main()

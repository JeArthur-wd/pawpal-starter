from datetime import date

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    today = date(2026, 10, 19)
    task = Task("Morning walk", 30)
    assert task.last_completed is None
    assert task.is_due(today)

    task.mark_complete(today)

    assert task.last_completed == today
    assert not task.is_due(today)


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10))
    assert len(pet.tasks) == 1

    pet.add_task(Task("Grooming", 45))
    assert len(pet.tasks) == 2

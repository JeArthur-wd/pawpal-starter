from datetime import date, time, timedelta

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task

TODAY = date(2026, 10, 19)


def make_owner():
    owner = Owner("Jordan")
    mochi, whiskers = Pet("Mochi"), Pet("Whiskers", "cat")
    owner.add_pet(mochi)
    owner.add_pet(whiskers)
    return owner, mochi, whiskers


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30)
    assert task.last_completed is None
    assert task.is_due(TODAY)

    task.mark_complete(TODAY)

    assert task.last_completed == TODAY
    assert not task.is_due(TODAY)


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10))
    assert len(pet.tasks) == 1

    pet.add_task(Task("Grooming", 45))
    assert len(pet.tasks) == 2


def test_sort_by_time_orders_chronologically_with_untimed_last():
    owner, mochi, _ = make_owner()
    for title, at in [("Evening", time(18, 0)), ("Untimed", None), ("Morning", time(7, 30))]:
        mochi.add_task(Task(title, 10, preferred_time=at))

    ordered = Scheduler(owner).sort_by_time(owner.get_all_tasks())

    assert [t.title for t in ordered] == ["Morning", "Evening", "Untimed"]


def test_filter_tasks_by_pet_and_completion():
    owner, mochi, whiskers = make_owner()
    walk, feed = Task("Walk", 20), Task("Feed", 10)
    mochi.add_task(walk)
    whiskers.add_task(feed)
    walk.mark_complete(TODAY)
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(pet_name="Whiskers") == [feed]
    assert scheduler.filter_tasks(completed=True) == [walk]
    assert scheduler.filter_tasks(completed=False) == [feed]
    assert scheduler.filter_tasks(pet_name="Mochi", completed=False) == []


def test_completing_daily_task_creates_next_day_copy_on_same_pet():
    owner, mochi, _ = make_owner()
    walk = Task("Walk", 30, frequency=Frequency.DAILY)
    mochi.add_task(walk)

    following = Scheduler(owner).mark_task_complete(walk, TODAY)

    assert following is not None and following is not walk
    assert following.due_date == TODAY + timedelta(days=1)
    assert following in mochi.tasks and following.pet_name == "Mochi"
    assert not walk.is_due(TODAY)
    assert not following.is_due(TODAY)
    assert following.is_due(TODAY + timedelta(days=1))


def test_completing_weekly_task_is_due_in_seven_days_and_once_task_has_no_copy():
    owner, mochi, _ = make_owner()
    bath = Task("Bath", 20, frequency=Frequency.WEEKLY)
    vet = Task("Vet", 60)
    mochi.add_task(bath)
    mochi.add_task(vet)
    scheduler = Scheduler(owner)

    assert scheduler.mark_task_complete(bath, TODAY).due_date == TODAY + timedelta(days=7)
    assert scheduler.mark_task_complete(vet, TODAY) is None
    assert len(mochi.tasks) == 3


def test_conflict_warnings_flag_overlap_for_same_and_different_pets():
    owner, mochi, whiskers = make_owner()
    mochi.add_task(Task("Walk", 30, preferred_time=time(7, 30)))
    mochi.add_task(Task("Brush", 5, preferred_time=time(7, 40)))
    whiskers.add_task(Task("Meds", 5, preferred_time=time(12, 30)))
    mochi.add_task(Task("Call", 15, preferred_time=time(12, 30)))

    warnings = Scheduler(owner).conflict_warnings(TODAY)

    assert len(warnings) == 2
    assert any("Walk" in w and "Brush" in w and "same pet" in w for w in warnings)
    assert any("Meds" in w and "Call" in w and "different pets" in w for w in warnings)


def test_conflict_warnings_ignore_back_to_back_and_untimed_tasks():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, preferred_time=time(8, 0)))
    mochi.add_task(Task("Feed", 10, preferred_time=time(8, 30)))  # starts as Walk ends
    mochi.add_task(Task("Play", 20))  # no time, can't conflict

    assert Scheduler(owner).conflict_warnings(TODAY) == []
    assert Scheduler(Owner("Empty")).conflict_warnings(TODAY) == []


def test_generate_plan_covers_all_pets_and_respects_time_budget():
    owner, mochi, whiskers = make_owner()
    owner.available_minutes = 40
    mochi.add_task(Task("Walk", 30, Priority.HIGH))
    whiskers.add_task(Task("Feed", 10, Priority.MEDIUM))
    whiskers.add_task(Task("Groom", 45, Priority.LOW))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(TODAY)

    assert {t.title for t in plan} == {"Walk", "Feed"}
    assert [t.title for t in scheduler.skipped] == ["Groom"]
    assert scheduler.detect_conflicts() == []


# --- Edge cases ---


def test_pets_with_no_tasks_and_owner_with_no_pets_plan_cleanly():
    owner, _, _ = make_owner()  # two pets, zero tasks
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan(TODAY) == []
    assert scheduler.explain_plan() == "No tasks to plan."
    assert Scheduler(Owner("Solo")).generate_plan(TODAY) == []


def test_two_tasks_at_the_exact_same_time_warn_and_are_planned_back_to_back():
    owner, mochi, whiskers = make_owner()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, time(9, 0)))
    whiskers.add_task(Task("Feed", 10, Priority.HIGH, time(9, 0)))
    scheduler = Scheduler(owner)

    assert len(scheduler.conflict_warnings(TODAY)) == 1
    plan = scheduler.generate_plan(TODAY)

    assert [(t.title, t.scheduled_start) for t in plan] == [
        ("Feed", time(9, 0)),
        ("Walk", time(9, 10)),
    ]
    assert scheduler.detect_conflicts() == []


def test_high_priority_task_gets_the_limited_time_budget_first():
    owner, mochi, _ = make_owner()
    owner.available_minutes = 30
    mochi.add_task(Task("Play", 30, Priority.LOW))
    mochi.add_task(Task("Meds", 30, Priority.HIGH))

    plan = Scheduler(owner).generate_plan(TODAY)

    assert [t.title for t in plan] == ["Meds"]


def test_task_that_cannot_finish_before_the_day_ends_is_skipped_with_a_reason():
    owner, mochi, _ = make_owner()  # day ends at 20:00
    mochi.add_task(Task("Late walk", 30, preferred_time=time(19, 45)))
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan(TODAY) == []
    assert "day ends" in scheduler.skipped[0].reason


def test_preferred_time_before_the_day_starts_is_moved_to_day_start():
    owner, mochi, _ = make_owner()  # day starts at 08:00
    mochi.add_task(Task("Early", 20, preferred_time=time(6, 0)))

    plan = Scheduler(owner).generate_plan(TODAY)

    assert plan[0].scheduled_start == time(8, 0)


def test_completed_daily_task_leaves_todays_plan_and_returns_tomorrow():
    owner, mochi, _ = make_owner()
    walk = Task("Walk", 30, frequency=Frequency.DAILY)
    mochi.add_task(walk)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(walk, TODAY)

    assert scheduler.generate_plan(TODAY) == []
    tomorrow_plan = scheduler.generate_plan(TODAY + timedelta(days=1))

    assert len(tomorrow_plan) == 1 and tomorrow_plan[0] is not walk


def test_recurring_copy_keeps_the_task_details():
    meds = Task("Meds", 5, Priority.HIGH, time(8, 0), Frequency.DAILY)

    following = meds.next_occurrence(TODAY)

    assert following is not meds and following.last_completed is None
    assert (following.title, following.duration_minutes, following.priority) == ("Meds", 5, Priority.HIGH)
    assert (following.preferred_time, following.frequency) == (time(8, 0), Frequency.DAILY)


def test_task_is_not_due_before_its_due_date_but_is_on_it():
    tomorrow = TODAY + timedelta(days=1)
    task = Task("Walk", 30, due_date=tomorrow)

    assert not task.is_due(TODAY)
    assert task.is_due(tomorrow)


def test_completing_the_same_task_twice_does_not_create_a_second_copy():
    owner, mochi, _ = make_owner()
    walk = Task("Walk", 30, frequency=Frequency.DAILY)
    mochi.add_task(walk)
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(walk, TODAY)
    again = scheduler.mark_task_complete(walk, TODAY)

    assert again is None
    assert len(mochi.tasks) == 2  # the original plus one copy

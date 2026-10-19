# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- **Multi-pet task tracking:** one owner, many pets, each with its own tasks (title, duration, priority, optional preferred time, repeat frequency).
- **Priority-aware daily planning:** tasks from every pet are combined, and the most important ones get the limited time budget first (`Scheduler.generate_plan`, `Scheduler.sort_tasks`).
- **Time-budget and day-window limits:** tasks that do not fit the owner's available minutes or the end of the day are skipped, with the reason shown.
- **Sorting by time:** tasks listed in chronological order, untimed tasks last (`Scheduler.sort_by_time`).
- **Filtering:** view by pet and/or by pending or completed status (`Scheduler.filter_tasks`).
- **Conflict warnings:** overlapping time windows are flagged in plain language, for the same pet or different pets, without crashing (`Scheduler.conflict_warnings`).
- **Daily and weekly recurrence:** completing a recurring task automatically adds the next occurrence (+1 day or +7 days), and completing the same task twice never duplicates it (`Scheduler.mark_task_complete`).
- **Plan explanations:** every planned or skipped task carries a one-sentence reason (`Scheduler.explain_plan`).
- **Streamlit app and CLI demo:** `streamlit run app.py` for the interactive planner, `python main.py` for a terminal walkthrough.

## Implementation summary

The logic layer lives in `pawpal_system.py` and is built from four classes plus two enums (`Priority`, `Frequency`). The design is in `diagrams/uml.mmd`.

- **`Task`** (dataclass) is one care activity: title, duration, priority, optional preferred time, frequency and the date it was last completed. `is_due(date)` is true while the task is uncompleted and its optional `due_date` has arrived, which decides whether it belongs in a given day's plan.
- **`Pet`** (dataclass) holds a name, species and its list of tasks. `add_task` also stamps the task with the pet's name so the plan can say who it is for.
- **`Owner`** (dataclass) holds the constraints (time budget, day window, preferences) and a list of pets. `get_all_tasks()` returns every pet's tasks in one flat list.
- **`Scheduler`** is the planning logic. `generate_plan(date)` reads from `Owner.get_all_tasks()`, keeps the tasks that are due, sorts them by priority, then preferred time, then shortest first, and places each in the earliest free slot at or after its preferred time. Tasks that don't fit the time budget or the day window are skipped, and every task records a `reason`. `detect_conflicts()` finds overlapping slots and `explain_plan()` turns the reasons into text.

The data flow is `Owner` -> `Pet`s -> `Task`s -> `Scheduler` -> an ordered plan with reasons. `main.py` is a terminal demo of that flow, and `tests/test_pawpal.py` holds the first automated tests.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output of `python main.py`, which builds one owner with two pets and six tasks and prints the generated plan:

```
Today's Schedule for Jordan - Monday, October 19, 2026
==================================================================
Time         Task              Pet       Priority   Min
------------------------------------------------------------------
08:00-08:30  Morning walk      Mochi     high        30
08:30-08:40  Breakfast         Whiskers  high        10
08:40-09:00  Play session      Whiskers  medium      20
12:30-12:35  Give medication   Whiskers  high         5
18:00-18:25  Evening walk      Mochi     medium      25
------------------------------------------------------------------
Planned 90 of 100 available minutes.

Skipped:
  Grooming (Mochi): needs 45 min but only 10 min of the time budget is left.

Why this plan:
  Morning walk (Mochi): high priority, preferred 07:30 is before the day starts at 08:00, so it starts then.
  Breakfast (Whiskers): high priority, preferred 08:00 was already taken, moved to the next free slot.
  Play session (Whiskers): medium priority, placed in the first free slot.
  Give medication (Whiskers): high priority, scheduled at its preferred time.
  Evening walk (Mochi): medium priority, scheduled at its preferred time.


=== Sorting: tasks as entered ===
  18:00  Evening walk (Mochi)
  07:30  Morning walk (Mochi)
  12:30  Vet check-in call (Mochi)
  07:40  Brush teeth (Mochi)
  12:30  Give medication (Whiskers)
  08:30  Breakfast (Whiskers)
  16:00  Bath (Whiskers)
  --:--  Play session (Whiskers)

=== Sorting: Scheduler.sort_by_time() ===
  07:30  Morning walk (Mochi)
  07:40  Brush teeth (Mochi)
  08:30  Breakfast (Whiskers)
  12:30  Vet check-in call (Mochi)
  12:30  Give medication (Whiskers)
  16:00  Bath (Whiskers)
  18:00  Evening walk (Mochi)
  --:--  Play session (Whiskers)

=== Filtering: Scheduler.filter_tasks(pet_name='Mochi') ===
  18:00  Evening walk (Mochi)
  07:30  Morning walk (Mochi)
  12:30  Vet check-in call (Mochi)
  07:40  Brush teeth (Mochi)

=== Conflict detection: Scheduler.conflict_warnings() ===
  Warning: 'Morning walk' (Mochi, 07:30-08:00) overlaps 'Brush teeth' (Mochi, 07:40-07:45) [same pet]
  Warning: 'Vet check-in call' (Mochi, 12:30-12:45) overlaps 'Give medication' (Whiskers, 12:30-12:35) [different pets]

=== Recurring tasks: Scheduler.mark_task_complete() ===
  Completed 'Morning walk' (daily) -> next due 2026-10-20
  Completed 'Bath' (weekly) -> next due 2026-10-26
  Completed 'Give medication' (once) -> no next occurrence

=== Filtering by status: completed=True / completed=False ===
Completed:
  07:30  Morning walk (Mochi)
  12:30  Give medication (Whiskers)
  16:00  Bath (Whiskers)
Still pending today (2026-10-19):
  18:00  Evening walk (Mochi)
  12:30  Vet check-in call (Mochi)
  07:40  Brush teeth (Mochi)
  08:30  Breakfast (Whiskers)
  --:--  Play session (Whiskers)
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The 18 tests in `tests/test_pawpal.py` cover the logic layer in `pawpal_system.py`:

- **Sorting:** `sort_by_time` returns tasks in chronological order with untimed tasks last.
- **Filtering:** `filter_tasks` by pet name, by completion status, and both together.
- **Recurrence:** completing a daily task adds a copy due the next day, a weekly one in seven days, and a one-off task creates nothing. The copy keeps the task's details, stays on the same pet, and is hidden until its due date. Completing the same task twice never creates a second copy.
- **Conflicts:** `conflict_warnings` flags overlapping windows for the same pet and for different pets, including two tasks at the exact same time. Back-to-back and untimed tasks are not flagged, and an empty list of tasks doesn't crash.
- **Planning:** all pets' tasks are combined, high priority gets the limited time budget first, tasks that don't fit the budget or the day window are skipped with a reason, an early preferred time moves to the start of the day, and the generated plan has no overlaps.
- **Basics and empty cases:** marking a task complete changes its status, adding a task grows the pet's list, and pets with no tasks (or an owner with no pets) produce an empty plan.

```
$ python -m pytest
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-8.4.2, pluggy-1.6.0
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1, cov-4.1.0
collected 18 items

tests\test_pawpal.py ..................                                  [100%]

============================= 18 passed in 0.10s ==============================
```

**Confidence level: 4 / 5 stars (★★★★☆).** The scheduling, sorting, recurrence and conflict rules are each checked on normal inputs and on edge cases, and writing the edge-case tests found a real bug (completing a recurring task twice created a duplicate), which is now fixed. I stop short of 5 because the Streamlit UI is only checked by hand, the tests don't cover tasks that cross midnight or two pets with the same name, and the scheduler is greedy rather than optimal.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sort by priority | `Scheduler.sort_tasks()` | Priority first, then preferred time, then shortest first. Decides which tasks get the limited time budget. |
| Sort by time | `Scheduler.sort_by_time()` | Chronological by scheduled start, else preferred time. Tasks with no time go last. Keys are `datetime.time` objects, so no string parsing is needed. |
| Filter by pet or status | `Scheduler.filter_tasks()` | Optional `pet_name` and `completed` arguments that combine freely. Defaults to all of the owner's tasks across every pet. |
| Time-budget filtering | `Scheduler.generate_plan()` | Skips a task when it needs more minutes than remain or no slot fits before the day ends, and records why. |
| Conflict warnings | `Scheduler.conflict_warnings()` | Returns readable warning strings for overlapping time windows, for the same pet or different pets. Never raises. `Scheduler.detect_conflicts()` does the same check on the finished plan and returns the tasks. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a daily or weekly task adds a new copy to the same pet with `due_date` = completion date + 1 day (daily) or + 7 days (weekly). One-off tasks create nothing. `Task.is_due()` hides the new copy until its date. |

**Design notes**
- Conflict checks compare each task's window (start time plus duration), so a 30-minute walk at 07:30 conflicts with a task at 07:40. Back-to-back tasks (one ends exactly when the next starts) are not conflicts.
- `generate_plan` never produces overlapping slots: it moves a later or lower-priority task to the next free slot. `conflict_warnings` is for telling the owner that the times they asked for clash.
- Only tasks with a time can conflict, because tasks without a preferred time get their slot from the scheduler.

## 📸 Demo Walkthrough

Run the interactive app with `streamlit run app.py`, or the terminal demo with `python main.py`.

### What you can do in the app

The page has five sections, top to bottom:

1. **About you:** set your name and how many minutes you have for pet care today. This is the time budget the planner respects.
2. **Your pets:** add pets by name and species. Empty or duplicate names are rejected with a warning.
3. **Add a task:** choose a pet, then set the task name, duration, priority, how often it repeats (once, daily, weekly) and, optionally, a preferred time.
4. **Your tasks:** a table sorted by time, with filters for pet and status. Overlapping times appear as yellow warnings under the table. A "Finished a task?" picker marks a task complete, and a daily or weekly task immediately gets its next occurrence.
5. **Today's schedule:** "Generate schedule" builds the day's plan from every pet's due tasks and shows each task's time slot with the reason it was placed there. Anything that does not fit is listed with why.

### Example workflow

1. Add two pets, Mochi (dog) and Whiskers (cat).
2. Add a daily "Morning walk" for Mochi at 08:00, a "Give medication" task for Whiskers at 12:30, and a low-priority "Vet check-in call" for Mochi, also at 12:30.
3. In **Your tasks**, the list is sorted by time, and a warning says the call overlaps the medication (different pets).
4. Click **Mark complete** on "Morning walk". It shows as done, and a new "Morning walk" appears due tomorrow.
5. Click **Generate schedule**. The higher-priority medication keeps 12:30 and the call is moved to the next free slot, with the reason in the "Why" column.

### Scheduler behaviors shown

- **Sorting:** `sort_by_time` puts tasks entered out of order into chronological order.
- **Filtering:** `filter_tasks` limits the list to one pet or to completed or pending tasks.
- **Conflict warnings:** `conflict_warnings` reports overlapping windows without raising an error.
- **Recurrence:** `mark_task_complete` creates the next daily or weekly task.
- **Budgeting:** `generate_plan` skips what does not fit and says why.

### Sample CLI output

Excerpt from `python main.py` (the full output is in the Sample Output section above):

```
Today's Schedule for Jordan - Monday, October 19, 2026
==================================================================
Time         Task              Pet       Priority   Min
------------------------------------------------------------------
08:00-08:30  Morning walk      Mochi     high        30
08:30-08:40  Breakfast         Whiskers  high        10
08:40-09:00  Play session      Whiskers  medium      20
12:30-12:35  Give medication   Whiskers  high         5
18:00-18:25  Evening walk      Mochi     medium      25
------------------------------------------------------------------
Planned 90 of 100 available minutes.

Skipped:
  Grooming (Mochi): needs 45 min but only 10 min of the time budget is left.

=== Sorting: Scheduler.sort_by_time() ===
  07:30  Morning walk (Mochi)
  07:40  Brush teeth (Mochi)
  08:30  Breakfast (Whiskers)
  12:30  Vet check-in call (Mochi)
  12:30  Give medication (Whiskers)
  16:00  Bath (Whiskers)
  18:00  Evening walk (Mochi)
  --:--  Play session (Whiskers)

=== Conflict detection: Scheduler.conflict_warnings() ===
  Warning: 'Morning walk' (Mochi, 07:30-08:00) overlaps 'Brush teeth' (Mochi, 07:40-07:45) [same pet]
  Warning: 'Vet check-in call' (Mochi, 12:30-12:45) overlaps 'Give medication' (Whiskers, 12:30-12:35) [different pets]

=== Recurring tasks: Scheduler.mark_task_complete() ===
  Completed 'Morning walk' (daily) -> next due 2026-10-20
  Completed 'Bath' (weekly) -> next due 2026-10-26
  Completed 'Give medication' (once) -> no next occurrence
```

*No screenshot is included; the walkthrough and CLI output above describe the app's behavior.*

### Design files

The class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (Mermaid). `diagrams/uml.mmd` holds the same diagram.

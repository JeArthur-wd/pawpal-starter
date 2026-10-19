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

## Implementation summary

The logic layer lives in `pawpal_system.py` and is built from four classes plus two enums (`Priority`, `Frequency`). The design is in `diagrams/uml.mmd`.

- **`Task`** (dataclass) is one care activity: title, duration, priority, optional preferred time, frequency and the date it was last completed. `is_due(date)` uses frequency and `last_completed` to decide whether it belongs in a given day's plan.
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
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

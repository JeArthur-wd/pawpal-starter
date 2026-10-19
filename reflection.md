# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML has four classes. `Owner`, `Pet` and `Task` hold data, and `Scheduler` holds the planning behavior. I kept the logic out of the data classes so the scheduler can be tested on its own.

- **`Owner`** is the person whose day is being planned. It holds the constraints: a time budget (`available_minutes`), an availability window (`day_start`, `day_end`) and a `preferences` dict. It owns a list of `Pet`s and can return every task across all of them with `get_all_tasks()`.
- **`Pet`** holds basic info (`name`, `species`) and its own list of `Task`s. It adds tasks and reports which ones are still pending.
- **`Task`** is one unit of care (walk, feeding, meds). It stores `title`, `duration_minutes`, `priority`, `frequency`, an optional `preferred_time` and a `completed` flag. It also carries the scheduler's output, `scheduled_start` and `reason`. Its methods mark it complete, say whether it is due on a date, convert priority to a sortable number and create the next occurrence of a recurring task.
- **`Scheduler`** is the only class with planning logic. It takes an `Owner`, sorts and filters tasks to fit the time budget in `generate_plan()`, and records what was `plan`ned and `skipped`. It also detects overlapping time slots and builds the `explain_plan()` text.

The relationships are `Owner` owns many `Pet`s, `Pet` has many `Task`s, and `Scheduler` plans for one `Owner`. I deliberately left out separate `DailyPlan` and `ScheduledTask` classes to keep the first version small.

**b. Design changes**

Yes. After writing the class skeletons, I asked an AI assistant to review `pawpal_system.py` for missing relationships and logic bottlenecks. I applied four of its suggestions before implementing any logic:

1. **`priority` and `frequency` became enums (`Priority`, `Frequency`).** They were plain strings, so a typo like `"hgih"` would silently sort wrong. Enums fail fast and give `priority_value()` a fixed set of values to map.
2. **`Task.completed: bool` became `last_completed: Optional[date]`.** A single flag can't represent a recurring task: a daily walk finished yesterday must be due again today. `mark_complete` and `Pet.get_pending_tasks` now take a date, so `is_due(date)` has something to compare against.
3. **`Task` now uses `@dataclass(eq=False)`.** The default dataclass equality compares every field, so two identical tasks for different pets would count as equal and break `list.remove` and `in` checks. Tasks now compare by identity.
4. **`Pet.add_task` is documented as responsible for stamping `Task.pet_name`.** Nothing assigned that link before, so the scheduler could not say which pet a task belonged to.

I did not apply the other suggestions, which can wait. Those are a real `Task`-to-`Pet` reference instead of a name string, separating the task definition from one day's plan result, an `end_time` field, and reconciling `available_minutes` with the `day_start`/`day_end` window. I'll revisit them in Phase 6 if the implementation shows they matter. `diagrams/uml.mmd` is updated to match.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI coding assistant at every stage: brainstorming the objects and their attributes and methods from the scenario, drafting the Mermaid UML, generating the class skeletons, reviewing those skeletons for design problems, implementing the four classes, writing the `main.py` demo, and drafting the first two tests.

The most helpful prompt was asking it to review my skeleton specifically for "missing relationships or potential logic bottlenecks". That produced concrete, checkable problems instead of general advice. One example is that a boolean `completed` flag can't represent a daily task that is due again tomorrow. Telling it to stay within the four classes in my UML also kept the code matching the diagram.

**b. Judgment and verification**

**What I accepted and rejected.** The first brainstorm proposed six classes, including separate `DailyPlan` and `ScheduledTask` classes. I scoped the design down to four and folded the plan output into `Task` (`scheduled_start`, `reason`) and `Scheduler` (`plan`, `skipped`) to keep the first version simple. The design review made eight suggestions. I accepted four (enums, `last_completed` instead of `completed`, `eq=False` on `Task`, `Pet.add_task` stamping the pet name) and deferred the other four (a real `Task`-to-`Pet` reference, separating the task definition from one day's result, an `end_time` field, and reconciling `available_minutes` with the day window). I also kept `diagrams/uml.mmd` as the filename instead of the suggested `uml_draft.mmd`, because the repo history shows it was renamed to match what the grader expects.

**How I verified the result.** I did not trust the implementation until I ran it. The `main.py` demo exposed two problems in the first run: the morning walk's reason said its 07:30 preferred time was "unavailable" when it was actually before the 08:00 start of the day, and skip reasons printed "Skipped: ... Skipped:". Both were wrong even though the schedule itself was right, so I fixed the wording in `pawpal_system.py` and re-ran. I also checked by hand that a daily task completed today is not due again until tomorrow, and that `detect_conflicts` catches forced overlaps. That conflict check was ad hoc and is not in the test suite yet. The two automated tests (task completion and task addition) pass, but the scheduler's ordering, budget and conflict behavior still need real tests.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

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

**Later change (Phase 4): recurrence became instance-based.** Originally a recurring task was "due again" whenever `is_due()` compared `last_completed` with today, so the same object repeated forever. The Phase 4 requirement said completing a daily or weekly task should create a new instance, and doing both would have made a task reappear on the day it was finished. I replaced the date comparison with a `due_date` field: `Scheduler.mark_task_complete()` marks the task done and adds a copy from `Task.next_occurrence(on)` due `on` plus one day or seven. `is_due()` is now just "not completed and the due date has arrived". Completed tasks also stay in the pet's list as history, which makes the completed/pending filter meaningful.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers six constraints:

- **Time budget (hard):** the owner's `available_minutes`. A task that needs more minutes than remain is skipped.
- **Day window (hard):** nothing may start before `day_start` or finish after `day_end`.
- **Due date and completion (hard):** only tasks that are due today and not yet completed are planned.
- **Priority (decides who wins):** high-priority tasks are placed first, so they get the scarce minutes.
- **Preferred time (soft):** honored when the slot is free, otherwise the task moves to the next free slot, and the reason says so.
- **No overlaps:** tasks never share a time slot.

I ranked them by what goes wrong if the rule is ignored. Skipping a medication to keep a low-priority play session at its preferred time is worse than moving the play session, so priority outranks preferred time. The time budget and the day window are hard limits because the owner cannot do more than they have time for. The owner's `preferences` dict exists on `Owner` but the scheduler does not read it yet.

**b. Tradeoffs**

**Conflict detection checks overlapping windows, but only warns and only for timed tasks.** `Scheduler.conflict_warnings()` compares each task's requested window (preferred time plus duration), so a 30-minute walk at 07:30 conflicts with a task at 07:40, not just with one at exactly 07:30. It only returns a warning message, and `generate_plan` resolves clashes on its own by moving the later or lower-priority task to the next free slot. A task with no preferred time can never be flagged, because the scheduler picks its slot.

I compare every pair of tasks with `itertools.combinations`, which is O(n^2), instead of sorting once and sweeping, which is O(n log n). The pairwise version is shorter, easier to read and obviously correct. A pet owner has a handful of tasks a day, so the speed difference is not measurable. I would switch to the sweep only if a plan could hold hundreds of tasks.

The same readability-over-optimality choice shows up in `generate_plan`. It fills the time budget greedily in priority order, so one long high-priority task can crowd out several short ones that would have fit together. Greedy is easy to explain to the owner ("highest priority first"), which matters because the app is meant to justify its plan.

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI coding assistant at every stage: brainstorming the objects and their attributes and methods from the scenario, drafting the Mermaid UML, generating the class skeletons, reviewing those skeletons for design problems, implementing the four classes, writing the `main.py` demo, and drafting the first two tests.

The most helpful prompt was asking it to review my skeleton specifically for "missing relationships or potential logic bottlenecks". That produced concrete, checkable problems instead of general advice. One example is that a boolean `completed` flag can't represent a daily task that is due again tomorrow. Telling it to stay within the four classes in my UML also kept the code matching the diagram.

**b. Judgment and verification**

**What I accepted and rejected.** The first brainstorm proposed six classes, including separate `DailyPlan` and `ScheduledTask` classes. I scoped the design down to four and folded the plan output into `Task` (`scheduled_start`, `reason`) and `Scheduler` (`plan`, `skipped`) to keep the first version simple. The design review made eight suggestions. I accepted four (enums, `last_completed` instead of `completed`, `eq=False` on `Task`, `Pet.add_task` stamping the pet name) and deferred the other four (a real `Task`-to-`Pet` reference, separating the task definition from one day's result, an `end_time` field, and reconciling `available_minutes` with the day window). I also kept `diagrams/uml.mmd` as the filename instead of the suggested `uml_draft.mmd`, because the repo history shows it was renamed to match what the grader expects.

**How I verified the result.** I did not trust the implementation until I ran it. The `main.py` demo exposed two problems in the first run: the morning walk's reason said its 07:30 preferred time was "unavailable" when it was actually before the 08:00 start of the day, and skip reasons printed "Skipped: ... Skipped:". Both were wrong even though the schedule itself was right, so I fixed the wording in `pawpal_system.py` and re-ran. I also checked by hand that a daily task completed today is not due again until tomorrow, and that `detect_conflicts` catches forced overlaps. Those checks are now real tests (section 4). Verification also caught two more problems that reading the code did not. Writing an edge-case test for "complete the same task twice" failed and showed that `mark_task_complete` created a duplicate daily task, so I made it ignore already-completed tasks. Driving the Streamlit app with Streamlit's test runner showed that "Mark complete" appeared to succeed but changed nothing, because `st.selectbox` returns a copy of an object option, so I was completing a throwaway copy. I changed the picker to select by index and look the task up in the live list.

**c. AI strategy**

- **Most effective features:** asking the assistant to review my own skeleton for specific problems ("missing relationships or logic bottlenecks") gave concrete, checkable findings. Letting it edit several files at once and run the code itself (the demo, `pytest`, and Streamlit's test runner) mattered most, because its changes were checked immediately instead of trusted. Giving it an edge-case list and asking for tests worked well too.
- **A suggestion I modified:** the first brainstorm proposed six classes, including `DailyPlan` and `ScheduledTask`. I cut it to four to keep the design small, and later deferred the review's bigger refactors (a real `Task`-to-`Pet` reference, separating a task from its day's plan result) because they would have rippled through the code for little gain at this size.
- **Separate chat sessions:** I did not use separate sessions. I worked through the phases in one long session. What kept it organized was the phase checklists, one commit per phase, and updating the README and reflection as I went. In hindsight a fresh session for testing would have been worth it: the assistant that wrote the code also wrote most of the tests, so a second set of eyes might have found the edge cases sooner.
- **Being the lead architect:** the AI is quick and produces plausible code, but it does not know which tradeoffs matter to the user. I set the scope (four classes, not six), chose which suggestions to apply and which to defer, and decided where the design had to change (instance-based recurrence). The AI's confident output was only as good as my checking. The bugs that mattered showed up only when the code was run, not when it was read.

---

## 4. Testing and Verification

**a. What you tested**

The 18 tests in `tests/test_pawpal.py` cover:

- **Basics:** marking a task complete changes its status, and adding a task grows a pet's task list.
- **Sorting:** `sort_by_time` gives chronological order with untimed tasks last.
- **Filtering:** by pet, by completion status, and both together.
- **Recurrence:** a daily task completed today creates a copy due tomorrow on the same pet, a weekly one is due in seven days, a one-off task creates nothing, the copy keeps the task's details, and completing the same task twice creates no second copy.
- **Conflicts:** overlapping windows are flagged for the same pet and for different pets, including two tasks at the exact same time. Back-to-back and untimed tasks are not flagged.
- **Planning:** all pets' tasks are combined, high priority gets the limited budget, tasks that do not fit are skipped with a reason, early preferred times move to the start of the day, and plans never overlap.
- **Empty cases:** a pet with no tasks, and an owner with no pets, produce an empty plan instead of an error.

The scheduler is the one part that can fail silently by producing a plausible but wrong plan, so these checks matter most there. They were also useful as a design tool: the "complete twice" test failed on its first run and exposed a real duplication bug.

**b. Confidence**

I am fairly confident, about 4 out of 5. Every scheduling rule is tested on normal and edge inputs, and all 18 tests pass. The gaps are the Streamlit UI, which I only exercised through a scripted run and by hand, and the cases I have not tested yet.

If I had more time I would test:

- two pets with the same name (`Task.pet_name` is only a string, and the UI blocks duplicate names but the logic layer does not);
- tasks that cross midnight or are longer than the whole day window;
- a plan regenerated for a different date (`generate_plan` writes the start time and reason onto the tasks themselves, so the previous plan is overwritten);
- weekly recurrence across month and year boundaries;
- the Streamlit flows as automated tests, since the selectbox-copy bug could only be found that way.

---

## 5. Reflection

**a. What went well**

I am most satisfied with keeping the logic separate from the interface. `pawpal_system.py` knows nothing about Streamlit or printing, so the same classes drive the CLI demo, the tests and the app. I am also pleased that every planned or skipped task carries a plain-language reason, so the app can explain its plan instead of just presenting it.

**b. What you would improve**

- **Plan results live on the tasks.** `generate_plan` writes `scheduled_start` and `reason` onto each `Task`, so regenerating overwrites them. I would bring back a separate `ScheduledTask` or `DailyPlan` object that I deferred in Phase 1.
- **Identity by name.** A task knows its pet only by a name string. A real reference or an id would remove the duplicate-name ambiguity.
- **Unused preferences.** `Owner.preferences` is stored but never read.
- **No persistence.** All data is lost when the app restarts. Saving to a JSON file would fix that.
- **Greedy planning.** A long high-priority task can crowd out several short ones. A knapsack-style search would pack the day better, at the cost of a plan that is harder to explain.

**c. Key takeaway**

Run the code before you trust it, especially code that an AI wrote confidently. The most important defects in this project were not visible in the source: a misleading explanation in the demo output, a duplicate task created by a double completion, and a UI button that reported success while changing nothing. Each one showed up only when the code was run or driven through the interface. The AI can draft quickly, but deciding what to build, what to defer and how to check it was my job.

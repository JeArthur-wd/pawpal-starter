from datetime import date, datetime, time, timedelta

import streamlit as st

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

PRIORITY_ICON = {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}


def hhmm(t: time | None) -> str:
    return t.strftime("%H:%M") if t is not None else "--:--"


def time_range(task: Task) -> str:
    """Format a planned task's slot as 'HH:MM-HH:MM'."""
    start = datetime.combine(date.today(), task.scheduled_start)
    return f"{start:%H:%M}-{start + timedelta(minutes=task.duration_minutes):%H:%M}"


def task_row(task: Task, today: date) -> dict:
    """One row of the task table: the time shown is the scheduled start, else the preferred time."""
    when = task.scheduled_start if task.scheduled_start is not None else task.preferred_time
    if task.last_completed is not None:
        status = "✅ Done"
    elif task.is_due(today):
        status = "Due today"
    else:
        status = f"Due {task.due_date:%b %d}"
    return {
        "Time": hhmm(when),
        "Task": task.title,
        "Pet": task.pet_name,
        "Priority": f"{PRIORITY_ICON[task.priority]} {task.priority.value}",
        "Min": task.duration_minutes,
        "Repeats": task.frequency.value,
        "Status": status,
    }


st.title("🐾 PawPal+")
st.caption("Plan your pets' care for the day: add pets and tasks, spot clashes, and get a schedule with reasons.")

owner = st.session_state.owner
scheduler = Scheduler(owner)
today = date.today()

# --- Owner -----------------------------------------------------------------
st.subheader("1. About you")
col_name, col_minutes = st.columns(2)
with col_name:
    owner.name = st.text_input("Your name", value=owner.name)
with col_minutes:
    owner.available_minutes = int(
        st.number_input(
            "Minutes available for pet care today",
            min_value=10,
            max_value=720,
            step=5,
            value=owner.available_minutes,
        )
    )

# --- Pets ------------------------------------------------------------------
st.subheader("2. Your pets")
col_pet, col_species = st.columns(2)
with col_pet:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_species:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    new_name = pet_name.strip()
    if not new_name:
        st.warning("Please enter a pet name.")
    elif any(p.name.lower() == new_name.lower() for p in owner.pets):
        st.warning(f"You already have a pet named {new_name}.")
    else:
        owner.add_pet(Pet(new_name, species))
        st.success(f"Added {new_name} the {species}.")

if owner.pets:
    st.table([{"Name": p.name, "Species": p.species, "Tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

# --- Add a task --------------------------------------------------------------
st.subheader("3. Add a task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    col_for, col_title = st.columns(2)
    with col_for:
        chosen_pet_name = st.selectbox("For which pet?", [p.name for p in owner.pets])
    with col_title:
        task_title = st.text_input("Task", value="Morning walk")

    col_dur, col_pri, col_rep = st.columns(3)
    with col_dur:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col_pri:
        priority = st.selectbox(
            "Priority", list(Priority), index=1, format_func=lambda p: p.value.title()
        )
    with col_rep:
        frequency = st.selectbox("Repeats", list(Frequency), format_func=lambda f: f.value.title())

    col_check, col_time = st.columns(2)
    with col_check:
        wants_time = st.checkbox("Prefer a specific time")
    with col_time:
        preferred = st.time_input("Preferred time", value=time(8, 0), disabled=not wants_time)

    if st.button("Add task"):
        if not task_title.strip():
            st.warning("Please give the task a name.")
        else:
            pet = next(p for p in owner.pets if p.name == chosen_pet_name)
            pet.add_task(
                Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    preferred_time=preferred if wants_time else None,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{task_title.strip()}' for {chosen_pet_name}.")

# --- Task list: sorted, filtered, conflicts, completion -----------------------
st.subheader("4. Your tasks")
if not owner.get_all_tasks():
    st.info("No tasks yet. Add one above.")
else:
    col_f_pet, col_f_status = st.columns(2)
    with col_f_pet:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col_f_status:
        status_filter = st.selectbox("Show status", ["All", "Pending", "Completed"])

    # Reserve this spot now and fill it after the "Mark complete" button below has run,
    # so the table never shows stale statuses.
    task_area = st.container()

    pending = scheduler.filter_tasks(completed=False)
    if pending:
        col_pick, col_done = st.columns([3, 1])
        with col_pick:
            # Select by index: st.selectbox returns a *copy* of object options, and
            # completing a copy would never reach the owner's real task.
            pick = st.selectbox(
                "Finished a task?",
                range(len(pending)),
                format_func=lambda i: f"{pending[i].title} ({pending[i].pet_name})",
            )
            to_complete = pending[pick]
        with col_done:
            st.write("")  # nudge the button down to line up with the selectbox
            mark_done = st.button("Mark complete")
        if mark_done:
            following = scheduler.mark_task_complete(to_complete, today)
            if following is not None:
                st.success(
                    f"Nice work! '{to_complete.title}' is done. Its next "
                    f"{to_complete.frequency.value} occurrence is due {following.due_date:%A, %b %d}."
                )
            else:
                st.success(f"Nice work! '{to_complete.title}' is done.")

    with task_area:
        visible = scheduler.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        )
        if visible:
            st.table([task_row(t, today) for t in scheduler.sort_by_time(visible)])
            st.caption("Sorted by time. Tasks without a time are listed last.")
        else:
            st.info("No tasks match these filters.")

        clashes = scheduler.conflict_warnings(today)
        for message in clashes:
            st.warning(message.removeprefix("Warning: "), icon="⚠️")
        if clashes:
            st.caption(
                "These tasks ask for overlapping times. Change one start time to fix it, or leave "
                "them: PawPal+ will keep the higher-priority task where it is and move the other "
                "to the next free slot."
            )

# --- Schedule -----------------------------------------------------------------
st.subheader("5. Today's schedule")
st.caption(f"{today:%A, %B %d}. Built from every pet's tasks that are due today.")

if st.button("Generate schedule"):
    plan = scheduler.generate_plan(today)
    if not plan and not scheduler.skipped:
        st.info("Nothing to schedule today. Add some tasks first.")
    else:
        planned_minutes = sum(t.duration_minutes for t in plan)
        st.success(
            f"Planned {len(plan)} task(s): {planned_minutes} of "
            f"{owner.available_minutes} available minutes."
        )
        if plan:
            st.table(
                [
                    {
                        "Time": time_range(t),
                        "Task": t.title,
                        "Pet": t.pet_name,
                        "Priority": f"{PRIORITY_ICON[t.priority]} {t.priority.value}",
                        "Min": t.duration_minutes,
                        "Why": t.reason,
                    }
                    for t in plan
                ]
            )
        if scheduler.skipped:
            st.warning(f"{len(scheduler.skipped)} task(s) did not fit today:")
            for t in scheduler.skipped:
                st.write(f"- **{t.title}** ({t.pet_name}): {t.reason}")

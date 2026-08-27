import random
from collections import defaultdict

DAYS_MON_FRI = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DAYS_MON_SUN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_timetable(planner):
    if planner.day_option == "mon_fri":
        days = DAYS_MON_FRI
    else:
        days = DAYS_MON_SUN

    subjects = list(planner.subjects.all())
    subjects_sorted = sorted(subjects, key=lambda x: x.priority)

    timetable = defaultdict(list)

    subject_cycle = []

    for subject in subjects_sorted:
        subject_cycle.extend([subject.subject_name] * (4 - subject.priority))

    if not subject_cycle:
        return {}

    index = 0

    for day in days:
        for hour in range(planner.free_hours_per_day):
            subject_name = subject_cycle[index % len(subject_cycle)]
            timetable[day].append({
                "hour": hour + 1,
                "subject": subject_name,
                "status": "pending"
            })
            index += 1

    return dict(timetable)
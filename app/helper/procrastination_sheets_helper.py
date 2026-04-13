from app.models.procrastination_sheet import ProcrastinationSheet


MAX_PROCRASTINATION_TASKS = 20


def get_sheet_stats(sheet: ProcrastinationSheet) -> dict:
    total_tasks = len(sheet.tasks)
    completed_tasks = sum(1 for task in sheet.tasks if task.is_completed)
    remaining_tasks = max(MAX_PROCRASTINATION_TASKS - total_tasks, 0)

    expected_values = [task.expected_difficulty for task in sheet.tasks if task.expected_difficulty is not None]
    actual_values = [task.actual_difficulty for task in sheet.tasks if task.actual_difficulty is not None]
    expected_satisfaction_values = [task.expected_satisfaction for task in sheet.tasks if task.expected_satisfaction is not None]
    actual_satisfaction_values = [task.actual_satisfaction for task in sheet.tasks if task.actual_satisfaction is not None]

    avg_expected_difficulty = round(sum(expected_values) / len(expected_values), 1) if expected_values else None
    avg_actual_difficulty = round(sum(actual_values) / len(actual_values), 1) if actual_values else None
    avg_expected_satisfaction = round(sum(expected_satisfaction_values) / len(expected_satisfaction_values), 1) if expected_satisfaction_values else None
    avg_actual_satisfaction = round(sum(actual_satisfaction_values) / len(actual_satisfaction_values), 1) if actual_satisfaction_values else None

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "entries_remaining": remaining_tasks,
        "avg_expected_difficulty": avg_expected_difficulty,
        "avg_actual_difficulty": avg_actual_difficulty,
        "avg_expected_satisfaction": avg_expected_satisfaction,
        "avg_actual_satisfaction": avg_actual_satisfaction,
    }
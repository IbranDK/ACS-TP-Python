def slack(task: Task) -> int:
    return task.D - task.C


def is_feasible(task: Task) -> bool:
    return slack(task) >= 0


def deadline_type(task: Task) -> str:
    if task.D == task.T:
        return "неявный (D=T)"
    if task.D <= task.T:
        return "ограниченный (D<=T)"
    return "произвольный (D>T)"
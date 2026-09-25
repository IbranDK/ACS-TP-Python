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
from typing import Iterable

def _norm(s: str) -> str:
    return s.strip().lower().replace("ё", "е")


def _is_hard(task: Task) -> bool:
    return _norm(task.hardness) == "жесткое"


def classify_system(tasks: Iterable[Task]) -> str:
    tasks_list = list(tasks)
    return "жёсткого реального времени" if any(_is_hard(t) for t in tasks_list) else "мягкого реального времени"


def critical_task(tasks: Iterable[Task]) -> Task | None:
    hard_tasks = [t for t in tasks if _is_hard(t)]
    return min(hard_tasks, key=slack) if hard_tasks else None


def required_reaction_time(tasks: Iterable[Task]) -> int:
    tasks_list = list(tasks)
    base = [t for t in tasks_list if _is_hard(t)] or tasks_list
    return min(t.D for t in base)


def utilization(tasks: Iterable[Task]) -> float:
    total = 0.0
    for t in tasks:
        if t.T <= 0:
            raise ValueError(f"Некорректный период T у задачи '{t.name}': {t.T}")
        total += t.C / t.T
    return total


def classify_architecture(n_cpu: int, has_network: bool) -> str:
    if has_network:
        return "распределённая"
    if n_cpu <= 1:
        return "однопроцессорная"
    return "многопроцессорная"
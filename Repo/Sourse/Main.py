from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


# =========================
# Model
# =========================

@dataclass(frozen=True)
class Task:
    name: str
    hardness: str  # "жёсткое" / "твёрдое" / "мягкое"
    C: int         # execution time, ms
    D: int         # relative deadline, ms
    T: int         # period, ms


# =========================
# Helpers (normalization)
# =========================

def _norm(s: str) -> str:
    return s.strip().lower().replace("ё", "е")


def _is_hard(task: Task) -> bool:
    return _norm(task.hardness) == "жесткое"


# =========================
# Required calculation functions
# =========================

def slack(task: Task) -> int:
    """L = D - C"""
    return task.D - task.C


def is_feasible(task: Task) -> bool:
    """Deadline is feasible by simple slack check: L >= 0"""
    return slack(task) >= 0


def deadline_type(task: Task) -> str:
    """By relation between D and T"""
    if task.D == task.T:
        return "неявный (D=T)"
    if task.D <= task.T:
        return "ограниченный (D<=T)"
    return "произвольный (D>T)"


def classify_system(tasks: Iterable[Task]) -> str:
    """Hard RT if at least one hard task exists, otherwise soft RT (per assignment)."""
    tasks_list = list(tasks)
    return "жёсткого реального времени" if any(_is_hard(t) for t in tasks_list) else "мягкого реального времени"


def critical_task(tasks: Iterable[Task]) -> Task | None:
    """Task with minimal slack among hard tasks. If no hard tasks -> None."""
    hard_tasks = [t for t in tasks if _is_hard(t)]
    if not hard_tasks:
        return None
    return min(hard_tasks, key=slack)


def required_reaction_time(tasks: Iterable[Task]) -> int:
    """
    R_треб = min(D) among hard tasks; if no hard tasks -> among all tasks.
    """
    tasks_list = list(tasks)
    if not tasks_list:
        raise ValueError("Список задач пуст.")
    base = [t for t in tasks_list if _is_hard(t)] or tasks_list
    return min(t.D for t in base)


def utilization(tasks: Iterable[Task]) -> float:
    """U = sum(Ci / Ti)"""
    total = 0.0
    for t in tasks:
        if t.T <= 0:
            raise ValueError(f"Некорректный период T у задачи '{t.name}': {t.T}")
        total += t.C / t.T
    return total


def classify_architecture(n_cpu: int, has_network: bool) -> str:
    """Per assignment rule: network => distributed; else by CPU count."""
    if has_network:
        return "распределённая"
    if n_cpu <= 1:
        return "однопроцессорная"
    return "многопроцессорная"


# =========================
# JSON I/O
# =========================

def load_variant_json(path: Path) -> tuple[list[Task], int, bool]:
    """
    Expected JSON:
    {
      "system": {"n_cpu": 1, "has_network": true},
      "tasks": [{"name": "...", "hardness": "...", "C": 1, "D": 5, "T": 5}, ...]
    }
    """
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    system = data.get("system", {})
    n_cpu = int(system.get("n_cpu", 1))
    has_network = bool(system.get("has_network", False))

    raw_tasks = data.get("tasks", [])
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("Поле 'tasks' отсутствует или пустое.")

    tasks: list[Task] = []
    for i, item in enumerate(raw_tasks, start=1):
        try:
            task = Task(
                name=str(item["name"]),
                hardness=str(item["hardness"]),
                C=int(item["C"]),
                D=int(item["D"]),
                T=int(item["T"]),
            )
        except KeyError as e:
            raise ValueError(f"В задаче #{i} нет обязательного поля: {e}") from e

        if task.C < 0 or task.D < 0 or task.T <= 0:
            raise ValueError(
                f"Некорректные значения (C,D,T) у задачи '{task.name}': C={task.C}, D={task.D}, T={task.T}"
            )

        tasks.append(task)

    return tasks, n_cpu, has_network


# =========================
# Output
# =========================

def print_table(tasks: list[Task]) -> None:
    headers = ["Задача", "Класс", "C", "D", "T", "L", "Выполнимо", "Тип дедлайна"]
    rows: list[list[str]] = []

    for t in tasks:
        L = slack(t)
        rows.append([
            t.name,
            t.hardness,
            str(t.C),
            str(t.D),
            str(t.T),
            str(L),
            "да" if L >= 0 else "нет",
            deadline_type(t),
        ])

    cols = list(zip(headers, *rows))
    widths = [max(len(x) for x in col) for col in cols]

    def fmt_row(values: list[str]) -> str:
        return " | ".join(v.ljust(w) for v, w in zip(values, widths))

    sep = "-+-".join("-" * w for w in widths)

    print(fmt_row(headers))
    print(sep)
    for r in rows:
        print(fmt_row(r))


def print_conclusion(tasks: list[Task], n_cpu: int, has_network: bool) -> None:
    sys_class = classify_system(tasks)
    arch = classify_architecture(n_cpu, has_network)
    crit = critical_task(tasks)
    r_req = required_reaction_time(tasks)
    u = utilization(tasks)

    all_slack_ok = all(is_feasible(t) for t in tasks)
    u_ok = (u <= 1.0)

    print("\nЗаключение:")
    print(f"- Класс системы: {sys_class}")
    print(f"- Архитектура: {arch} (CPU={n_cpu}, сеть={'да' if has_network else 'нет'})")

    if crit is not None:
        print(f"- Критическая задача (среди жёстких): {crit.name} (L={slack(crit)} мс)")
    else:
        print("- Критическая задача: отсутствует (жёсткие задачи не заданы)")

    print(f"- Требуемое время реакции R_треб = {r_req} мс")
    print(f"- Коэффициент загрузки U = {u:.4f}; необходимое условие U<=1: {'выполнено' if u_ok else 'НЕ выполнено'}")
    print(f"- Проверка дедлайнов по запасу (L>=0): {'все выполнимы' if all_slack_ok else 'есть невыполнимые'}")


# =========================
# CLI
# =========================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Практическая №1: классификация СРВ и расчёт временных характеристик (JSON input)"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Путь к JSON файлу варианта (например: data/variant.json)"
    )
    args = parser.parse_args()

    tasks, n_cpu, has_network = load_variant_json(args.input)

    print_table(tasks)
    print_conclusion(tasks, n_cpu, has_network)


if __name__ == "__main__":
    main()
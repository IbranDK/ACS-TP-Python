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
import json
from typing import Any

def load_variant_json(path: Path) -> tuple[list[Task], int, bool]:
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
            tasks.append(Task(
                name=str(item["name"]),
                hardness=str(item["hardness"]),
                C=int(item["C"]),
                D=int(item["D"]),
                T=int(item["T"]),
            ))
        except KeyError as e:
            raise ValueError(f"В задаче #{i} нет обязательного поля: {e}") from e

    return tasks, n_cpu, has_network
def main() -> None:
    parser = argparse.ArgumentParser(description="Практическая №1: классификация СРВ (JSON input)")
    parser.add_argument("-i", "--input", type=Path, required=True, help="Путь к JSON файлу варианта")
    args = parser.parse_args()

    tasks, n_cpu, has_network = load_variant_json(args.input)

    print_table(tasks)
    print_conclusion(tasks, n_cpu, has_network)
#!/usr/bin/env python3
"""tool_probe.py — умеет ли локальная модель ВЫЗЫВАТЬ ИНСТРУМЕНТЫ.

🔴 ЗАЧЕМ ОТДЕЛЬНЫЙ СТЕНД, ЕСЛИ ЕСТЬ `bench.py`. Тот меряет качество ТЕКСТА:
сожми, извлеки, классифицируй. Но владельцу нужно другое — заменить агентную
работу, то есть чтобы модель читала файлы, правила их и запускала проверки.

Модель не трогает файлы никогда — ни локальная, ни Claude. Файлы трогает
ОБОЛОЧКА, а модель лишь говорит ей: «вызови инструмент `прочитать_файл`
с аргументом `reports/pitfalls.md`». Всё различие между «собеседником»
и «помощником» — в этом одном умении.

Отсюда предмет замера: выдаёт ли модель СТРУКТУРНО ВЕРНЫЙ вызов инструмента,
а не рассказ о том, что она бы его вызвала.

ЧТО ПРОВЕРЯЕТСЯ — три ступени, и они разной высоты:
    1. один вызов          выбрать инструмент и заполнить аргумент
    2. выбор из двух       не перепутать чтение файла с запуском команды
    3. второй ход          получив результат инструмента, сделать верный
                           СЛЕДУЮЩИЙ шаг, а не начать сначала

🔴 Третья ступень и есть настоящий барьер. По независимому BFCL v4 модели
3–4B дают на многоходовых сценариях 0,4–22 % против 61 % у Sonnet 4.5:
одиночный вызов они берут, цепочка рассыпается. Работа с 70 репозиториями —
это цепочка, а не один вызов.

ЧЕГО СТЕНД НЕ МЕРИТ:
  · длинный контекст: инструментов два, а не двадцать, и файлов в промпте нет;
  · устойчивость: один прогон на задачу;
  · реальную оболочку: `aider` и подобные умеют принимать правки ТЕКСТОМ,
    в обход вызова инструментов, — модель, провалившая этот стенд, может
    оказаться пригодной там. Это проверяется отдельно и здесь не проверено.

ЗАПУСК
    tool_probe.py --model gemma4:e2b
    tool_probe.py --show
    tool_probe.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ЛАБА = Path(__file__).resolve().parent
РЕЗУЛЬТАТЫ = ЛАБА / "tool-results.tsv"
API = "http://127.0.0.1:11434/api/chat"

ИНСТРУМЕНТЫ = [
    {
        "type": "function",
        "function": {
            "name": "прочитать_файл",
            "description": "Прочитать текстовый файл репозитория и вернуть его содержимое",
            "parameters": {
                "type": "object",
                "properties": {
                    "путь": {"type": "string",
                             "description": "путь от корня репозитория"},
                },
                "required": ["путь"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "запустить_проверку",
            "description": "Запустить скрипт-проверку репозитория и вернуть её вывод",
            "parameters": {
                "type": "object",
                "properties": {
                    "скрипт": {"type": "string",
                               "description": "имя скрипта из каталога scripts/"},
                },
                "required": ["скрипт"],
            },
        },
    },
]


def вызовы(ответ: dict) -> list[tuple[str, dict]]:
    """[(имя инструмента, аргументы)] из ответа Ollama. Пусто — вызова не было."""
    из = []
    for в in (ответ.get("message", {}) or {}).get("tool_calls", []) or []:
        ф = в.get("function", {})
        арг = ф.get("arguments", {})
        if isinstance(арг, str):
            try:
                арг = json.loads(арг)
            except ValueError:
                арг = {}
        из.append((ф.get("name", ""), арг))
    return из


def ступень_1(ответ: dict) -> bool:
    """Один вызов: прочитать именно тот файл, о котором спросили."""
    в = вызовы(ответ)
    if len(в) != 1:
        return False
    имя, арг = в[0]
    путь = str(арг.get("путь", "")).strip().lstrip("./")
    return имя == "прочитать_файл" and путь == "reports/pitfalls.md"


def ступень_2(ответ: dict) -> bool:
    """Выбор из двух: тут нужен запуск проверки, а не чтение файла."""
    в = вызовы(ответ)
    if len(в) != 1:
        return False
    имя, арг = в[0]
    скрипт = str(арг.get("скрипт", "")).strip()
    return имя == "запустить_проверку" and "revision_check" in скрипт


def ступень_3(ответ: dict) -> bool:
    """Второй ход: получив вывод проверки с одним падением, прочитать ИМЕННО
    тот файл, который в падении назван, — а не начать сначала."""
    в = вызовы(ответ)
    if len(в) != 1:
        return False
    имя, арг = в[0]
    путь = str(арг.get("путь", "")).strip().lstrip("./")
    return имя == "прочитать_файл" and путь == "00-infrastructure/45-roadmap-and-tasks.md"


ЗАДАЧИ = [
    {
        "имя": "один-вызов",
        "вес": 1,
        "что": "выбрать инструмент и заполнить аргумент",
        "сообщения": [
            {"role": "system", "content": "Ты помощник с инструментами. Когда для "
                                          "ответа нужны данные из репозитория — "
                                          "вызывай инструмент, не выдумывай."},
            {"role": "user", "content": "Сколько карточек PIT в файле "
                                        "reports/pitfalls.md?"},
        ],
        "грейдер": ступень_1,
    },
    {
        "имя": "выбор-из-двух",
        "вес": 2,
        "что": "не перепутать чтение файла с запуском проверки",
        "сообщения": [
            {"role": "system", "content": "Ты помощник с инструментами. Когда для "
                                          "ответа нужны данные из репозитория — "
                                          "вызывай инструмент, не выдумывай."},
            {"role": "user", "content": "Проверь, зелёный ли сейчас гейт ревизии "
                                        "репозитория. Он запускается скриптом "
                                        "revision_check.py."},
        ],
        "грейдер": ступень_2,
    },
    {
        "имя": "второй-ход",
        "вес": 3,
        "что": "🔴 цепочка: верный следующий шаг после результата инструмента",
        "сообщения": [
            {"role": "system", "content": "Ты помощник с инструментами. Когда для "
                                          "ответа нужны данные из репозитория — "
                                          "вызывай инструмент, не выдумывай."},
            {"role": "user", "content": "Проверь гейт ревизии и разберись с тем, "
                                        "что он найдёт."},
            {"role": "assistant", "content": "",
             "tool_calls": [{"function": {"name": "запустить_проверку",
                                          "arguments": {"скрипт": "revision_check.py"}}}]},
            {"role": "tool", "content": "[OK] Битые ссылки\n[OK] Имена файлов\n"
                                        "[FAIL] Роадмап отстал от журнала: 1\n"
                                        "    · 00-infrastructure/45-roadmap-and-tasks.md "
                                        "описывает этап, закрытый три версии назад\n"
                                        "[OK] Секреты\n\nИТОГ: DRIFT (fail: 1)"},
        ],
        "грейдер": ступень_3,
    },
]


def спросить(модель: str, сообщения: list[dict], таймаут: int) -> tuple[dict, dict]:
    тело = json.dumps({
        "model": модель, "messages": сообщения, "tools": ИНСТРУМЕНТЫ,
        "stream": False, "think": False,
        "options": {"temperature": 0, "num_predict": 200},
    }).encode("utf-8")
    запрос = urllib.request.Request(API, data=тело,
                                    headers={"Content-Type": "application/json"})
    начало = time.time()
    try:
        with urllib.request.urlopen(запрос, timeout=таймаут) as о:
            д = json.loads(о.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        return {}, {"ошибка": f"{type(e).__name__}: {e}"[:120],
                    "секунд": round(time.time() - начало, 1)}
    return д, {"секунд": round(time.time() - начало, 1),
               "токенов": д.get("eval_count", 0)}


def selftest() -> int:
    """Грейдеры обязаны отличать вызов от РАССКАЗА о вызове."""
    верный = {"message": {"tool_calls": [{"function": {
        "name": "прочитать_файл", "arguments": {"путь": "reports/pitfalls.md"}}}]}}
    assert ступень_1(верный)
    # 🔴 Самый частый отказ малой модели: она ОПИСЫВАЕТ вызов текстом.
    словами = {"message": {"content": "Я вызову прочитать_файл('reports/pitfalls.md')",
                           "tool_calls": []}}
    assert not ступень_1(словами), "рассказ о вызове не является вызовом"
    чужой = {"message": {"tool_calls": [{"function": {
        "name": "прочитать_файл", "arguments": {"путь": "README.md"}}}]}}
    assert not ступень_1(чужой), "не тот файл — не зачёт"
    два = {"message": {"tool_calls": [
        {"function": {"name": "прочитать_файл", "arguments": {"путь": "reports/pitfalls.md"}}},
        {"function": {"name": "запустить_проверку", "arguments": {"скрипт": "x.py"}}}]}}
    assert not ступень_1(два), "лишний вызов — не зачёт"
    строкой = {"message": {"tool_calls": [{"function": {
        "name": "запустить_проверку",
        "arguments": '{"скрипт": "revision_check.py"}'}}]}}
    assert ступень_2(строкой), "аргументы строкой JSON обязаны разбираться"
    assert not ступень_2(верный), "чтение файла вместо запуска — не зачёт"
    цепочка = {"message": {"tool_calls": [{"function": {
        "name": "прочитать_файл",
        "arguments": {"путь": "00-infrastructure/45-roadmap-and-tasks.md"}}}]}}
    assert ступень_3(цепочка)
    assert not ступень_3(строкой), "повтор проверки вместо следующего шага — не зачёт"
    print("🟢 канарейка стенда инструментов: рассказ о вызове не считается "
          "вызовом, чужой аргумент и лишний вызов не проходят, аргументы "
          "строкой разбираются")
    return 0


def дописать(строки: list[dict]) -> None:
    поля = ("дата", "модель", "ступень", "балл", "секунд", "вызовов", "заметка")
    первый = not РЕЗУЛЬТАТЫ.is_file()
    with РЕЗУЛЬТАТЫ.open("a", encoding="utf-8") as ф:
        if первый:
            ф.write("\t".join(поля) + "\n")
        for с in строки:
            ф.write("\t".join(str(с.get(п, "")).replace("\t", " ") for п in поля) + "\n")


def показать() -> int:
    if not РЕЗУЛЬТАТЫ.is_file():
        print("🟡 результатов нет")
        return 1
    строки = [с.split("\t") for с in
              РЕЗУЛЬТАТЫ.read_text(encoding="utf-8").splitlines() if с.strip()]
    данные = [dict(zip(строки[0], с)) for с in строки[1:]]
    веса = {з["имя"]: з["вес"] for з in ЗАДАЧИ}
    последние: dict[tuple[str, str], dict] = {}
    for с in данные:
        последние[(с["модель"], с["ступень"])] = с
    по_моделям: dict[str, list[dict]] = {}
    for (м, _), с in последние.items():
        по_моделям.setdefault(м, []).append(с)
    for модель, прогоны in sorted(по_моделям.items()):
        взято = sum(веса.get(п["ступень"], 1) for п in прогоны if п["балл"] == "1")
        балл = взято * 100 // sum(веса.values())
        значок = "🟢" if балл >= 80 else "🟡" if балл >= 50 else "🔴"
        print(f"{значок} {модель}: {балл}/100 вызов инструментов")
        for п in sorted(прогоны, key=lambda п: п["ступень"]):
            print(f"   {'🟢' if п['балл'] == '1' else '🔴'} {п['ступень']:14} "
                  f"{п['секунд']:>7} с  вызовов: {п['вызовов']:<2} {п['заметка'][:60]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.show or not a.model:
        return показать()

    строки = []
    for з in ЗАДАЧИ:
        print(f"── {a.model} · {з['имя']} ({з['что']})", flush=True)
        ответ, замер = спросить(a.model, з["сообщения"], a.timeout)
        если_вызовы = вызовы(ответ)
        if "ошибка" in замер:
            балл, заметка = 0, замер["ошибка"]
        else:
            балл = int(bool(з["грейдер"](ответ)))
            текст = (ответ.get("message", {}) or {}).get("content", "") or ""
            заметка = (", ".join(f"{и}({list(а.values())[0] if а else ''})"
                                 for и, а in если_вызовы)
                       if если_вызовы else f"вызова нет: {' '.join(текст.split())[:80]}")
        print(f"   {'🟢' if балл else '🔴'} {замер['секунд']} с · {заметка[:100]}",
              flush=True)
        строки.append({"дата": dt.date.today().isoformat(), "модель": a.model,
                       "ступень": з["имя"], "балл": балл,
                       "секунд": замер["секунд"], "вызовов": len(если_вызовы),
                       "заметка": заметка[:120]})
    дописать(строки)
    return 0


if __name__ == "__main__":
    sys.exit(main())

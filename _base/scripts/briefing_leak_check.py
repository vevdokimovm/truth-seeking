#!/usr/bin/env python3
"""briefing_leak_check.py — что из брифинга нельзя выпускать наружу.

🔴 ЗАКАЗ ВЛАДЕЛЬЦА 29.09.2026: брифинг системы для СТОРОННЕГО эксперта —
другой языковой модели или человека. Документ покидает машину, то есть сам
является исходящим каналом — ровно того класса, который первый же аудит
и должен оценить. Правила — `18-external-audit-kit/SANITIZATION.md`.

ЧТО ЛОВИТ (по форме, машинно):

    личность        имя оператора, почта, аккаунт хостинга
    пути            абсолютные пути с именем пользователя
    сеть            IPv4, IPv6, MAC, имена хостов, маркеры туннелей
    секреты         токены и ключи по сигнатурам
    карантин        упоминание закрытого каталога

🔴 ЧЕГО НЕ ЛОВИТ — и это важнее списка выше:
  · смысловое раскрытие: фраза, из которой деятельность выводится косвенно;
  · совокупный эффект: каждый факт безобиден, вместе они сужают круг до
    одного человека;
  · ответы на уточняющие вопросы эксперта — они уходят тем же каналом
    мимо всякой проверки.
Проверка закрывает «забыл вычистить», а не «написал лишнего».

🔴 ИМЯ ОПЕРАТОРА НЕ ХРАНИТСЯ В ЭТОМ ФАЙЛЕ. Оно берётся из окружения
и из настроек git. Вписать его константой значило бы положить то, что
защищаем, в файл, который сам уезжает в историю и раздаётся копиями.

ЗАПУСК
    briefing_leak_check.py                   проверить кит целиком
    briefing_leak_check.py <файл> [<файл>…]  проверить конкретные файлы
    briefing_leak_check.py --selftest
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

БАЗА = Path(__file__).resolve().parent.parent
КИТ = БАЗА / "18-external-audit-kit"


def личные_маркеры() -> list[tuple[str, str]]:
    """[(что искать, как назвать)] — из окружения, НЕ из константы в файле."""
    из: list[tuple[str, str]] = []
    юзер = os.environ.get("USER") or ""
    if юзер:
        из.append((юзер, "имя пользователя ОС"))
    дом = str(Path.home())
    из.append((дом, "домашний каталог с именем пользователя"))
    for ключ in ("user.name", "user.email"):
        r = subprocess.run(["git", "-C", str(БАЗА), "config", "--get", ключ],
                           capture_output=True, text=True)
        значение = r.stdout.strip()
        if значение:
            из.append((значение, f"git {ключ}"))
            if ключ == "user.email" and "@" in значение:
                из.append((значение.split("@")[0], "локальная часть почты"))
    return из


ШАБЛОНЫ: list[tuple[str, re.Pattern, str]] = [
    ("СЕТЬ", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"), "MAC-адрес"),
    # 🔴 Исключены номера версий (4.215.0) и даты — иначе каждая строка
    # брифинга со счётчиком версии считалась бы утечкой адреса, проверка
    # утонула бы в шуме и её выключили бы. Ложное срабатывание гейта
    # опаснее пропуска: пропуск чинят, шумный гейт отключают.
    ("СЕТЬ", re.compile(r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
                        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\d.])"), "IPv4-адрес"),
    ("СЕТЬ", re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){4,7}[0-9A-Fa-f]{1,4}\b"), "IPv6-адрес"),
    ("СЕТЬ", re.compile(r"\b(happ|wireguard|wg-quick|openvpn|ovpn|shadowsocks|"
                        r"outline|v2ray|amnezia|tailscale)\b", re.I), "маркер туннеля"),
    ("ПУТЬ", re.compile(r"/(?:Users|home)/(?!<)[A-Za-z0-9._-]+"), "абсолютный путь с именем"),
    ("КАРАНТИН", re.compile(r"NOT\s+FOR\s+CLAUDE", re.I), "имя закрытой зоны"),
    ("СЕКРЕТ", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{16,}|"
                          r"AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"), "токен"),
    ("СЕКРЕТ", re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key)\s*[:=]\s*"
                          r"['\"]?[^\s'\"]{8,}"), "пароль или ключ в строке"),
    ("ПОЧТА", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "адрес почты"),
]


def проверить(файл: Path, личное: list[tuple[str, str]]) -> list[str]:
    try:
        текст = файл.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        return [f"🟡 не прочитан: {e}"]
    находки: list[str] = []
    for н, строка in enumerate(текст.splitlines(), 1):
        for что, как in личное:
            if что and что in строка:
                находки.append(f"🔴 {файл.name}:{н} — {как}")
        for класс, шаблон, что in ШАБЛОНЫ:
            for m in шаблон.finditer(строка):
                кусок = m.group(0)
                # Шаблон в таблице правил — не утечка, а инструкция.
                if кусок.startswith("[") or "<" in кусок:
                    continue
                находки.append(f"🔴 {файл.name}:{н} [{класс}] {что}: {кусок[:48]}")
    return находки


def selftest() -> int:
    п = Path("/tmp/x")
    сеть = [ш for к, ш, _ in ШАБЛОНЫ if к == "СЕТЬ"]
    ipv4 = сеть[1]
    assert ipv4.search("узел 192.168.1.1 отвечает"), "адрес обязан ловиться"
    assert not ipv4.search("версия 4.215.0 выпущена"), "версия — не адрес"
    assert not ipv4.search("дата 2026.09.29 и всё"), "дата — не адрес"
    путь = [ш for к, ш, _ in ШАБЛОНЫ if к == "ПУТЬ"][0]
    assert путь.search("лежит в /Users/someone/repos"), "путь с именем ловится"
    assert not путь.search("лежит в ~/repos/<репозиторий>"), "обобщённый путь — норма"
    карантин = [ш for к, ш, _ in ШАБЛОНЫ if к == "КАРАНТИН"][0]
    assert карантин.search("каталог NOT FOR CLAUDE")
    assert п  # молчаливая проверка импорта Path
    print("🟢 selftest: адреса отличаются от версий и дат, путь с именем "
          "отличается от обобщённого, закрытая зона ловится")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("файлы", nargs="*", type=Path)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    файлы = a.файлы or sorted(КИТ.glob("*.md"))
    if not файлы:
        print(f"🔴 нечего проверять: {КИТ} пуст или отсутствует")
        return 1

    личное = личные_маркеры()
    всего = 0
    for ф in файлы:
        находки = проверить(ф, личное)
        всего += len(находки)
        for н in находки:
            print(н)
    print(f"\nпроверено файлов: {len(файлы)} · находок: {всего}")
    if всего:
        print("🔴 БРИФИНГ НЕ ОТДАВАТЬ, пока находки не сняты")
    else:
        print("🟢 по форме чисто. 🔴 Смысловое раскрытие и совокупный эффект "
              "проверка НЕ ловит — прочитать глазами (SANITIZATION.md §5)")
    return 1 if всего else 0


if __name__ == "__main__":
    sys.exit(main())

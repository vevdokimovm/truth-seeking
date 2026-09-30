"""Канарейка класса PIT-J на стыке `pack_release.py` ↔ `publish.py`.

Проверяется РАЗЛИЧЕНИЕ двух исходов, а не один «хороший»:

  1. архив собран последним действием  → проверка молчит;
  2. файл репы правлен ПОСЛЕ упаковки  → проверка возражает.

Второй — главный. Ровно он держался незамеченным: упаковка шла четвёртым
шагом ритуала, а «состояние на закрытие» дописывало указатель в `WATCHLOG.md`
после неё, и архив расходился с рабочей копией на каждом батче. Отказ всплывал
позже, в другом скрипте, и выглядел разовой неудачей выпуска.

Герметично: игрушечная репа во временном каталоге, свой каталог артефактов
через `BASE_ARTIFACTS`. Ни сети, ни настоящих реп, ни записи в артефакты базы.

ЗАПУСК: python3 tests/bin/archive_freshness_canary.py   (из корня base-repo)
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

БАЗА = Path(__file__).resolve().parent.parent.parent


def построить_игрушку(корень: Path) -> Path:
    """Минимальная репа, которую упаковщик согласен считать репой."""
    репа = корень / "repos" / "igrushka"
    (репа / "reports" / "releases").mkdir(parents=True)
    (репа / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (репа / ".repo-id").write_text("igrushka\n", encoding="utf-8")
    (репа / "WATCHLOG.md").write_text("# igrushka\n\n## §0. Где стоим\n",
                                      encoding="utf-8")
    # Упаковщик отказывается паковать меньше шести файлов («это не репа»)
    # и предупреждает об отсутствии служебных файлов в корне (канон 43 §3а).
    for i in range(8):
        (репа / f"doc-{i}.md").write_text(f"# документ {i}\n", encoding="utf-8")
    for имя, текст in ((".repo-class", "knowledge\n"),
                       ("CHANGELOG.md", "## [1.0.0]\n"),
                       ("README.md", "# igrushka\n")):
        (репа / имя).write_text(текст, encoding="utf-8")
    return репа


def main() -> int:
    корень = Path(tempfile.mkdtemp(prefix="kanareyka-arhiv-"))
    try:
        арт = корень / "artifacts"
        арт.mkdir()
        репа = построить_игрушку(корень)

        env = dict(os.environ, BASE_ARTIFACTS=str(арт))
        r = subprocess.run(
            [sys.executable, str(БАЗА / "scripts/pack_release.py"), str(репа)],
            capture_output=True, text=True, env=env)
        if r.returncode != 0:
            print("🔴 игрушечный архив не собрался:")
            print(r.stdout + r.stderr)
            return 1

        os.environ["BASE_ARTIFACTS"] = str(арт)
        sys.path.insert(0, str(БАЗА / "scripts"))
        from publish import проверить_архив

        архив = арт / "igrushka-v1.0.0.zip"
        до = проверить_архив(архив, "igrushka", "1.0.0", репа)
        print(f"  [1] архив собран последним      → бед: {len(до)}")

        (репа / "WATCHLOG.md").write_text(
            "# igrushka\n\n## §0. Где стоим\n"
            "> 🧭 состояние дописано ПОСЛЕ упаковки\n", encoding="utf-8")
        после = проверить_архив(архив, "igrushka", "1.0.0", репа)
        print(f"  [2] WATCHLOG правлен после неё  → бед: {len(после)}")
        for б in после:
            print(f"      · {б}")

        ок = not до and bool(после)
        print("\n  🟢 канарейка жива: свежий архив проходит, расхождение ловится"
              if ок else
              "\n  🔴 КАНАРЕЙКА МЁРТВА: проверка не различает эти два случая")
        return 0 if ок else 1
    finally:
        shutil.rmtree(корень, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

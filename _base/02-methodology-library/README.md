# 02-methodology-library — библиотека универсальных методичек

> **Что это.** Общий фонд предметных методичек, гайдов и справочников, перенесённых из
> FINPILOT (донор — приватная репа `personal-finance-dss`, срез v5.25.0, 2026-07-09).
> Решение о переносе и его логика — `../reports/adr/adr-001-methodology-library.md`;
> полная карта «что взято / что пропущено / почему» — `../reports/merges/merge-manifest-v1-6-0.md`.
> **Второй свип (v1.8.0):** дочёсаны `knowledge/business/` и `knowledge/science/guides/` донора —
> +9 универсалий (наука: публикации/степени; бизнес: CustDev-курс, международные рынки; QA).
>
> **Принцип — «all in, отбор потом»** (`18-documentation-philosophy.md` §2): лучше внести всё
> универсальное сразу и убрать лишнее на ревизии, чем выбирать сейчас и потерять. Файлы внесены
> **as-is** (имена и содержимое донора, включая боевые примеры из FINPILOT — они намеренно
> оставлены как живые иллюстрации). Инфраструктура реп сюда НЕ входит — она в `00-infrastructure/`.

## Судьба библиотеки (правило ревизии)

При плановой ревизии (`21-revision-protocol.md`) каждый файл получает один из исходов:
**остаётся** (нужен всем репам как общий фонд) · **переезжает** в тематическую репу из колонки
«кандидат» · **сливается** с существующим доком · **удаляется** (устарел/не пригодился).
До ревизии — ничего не выбрасывать.

## Навигатор

| Файл | Про что | Кандидат-репа при растаскивании |
|---|---|---|
| `architecture-guide.md` | Проектирование архитектуры ПО: слои, компоненты, приёмы | `it-base` |
| `audience-research-guide.md` | Исследование аудитории: методы, протоколы интервью, опросники | `it-base` / `misc-vault` |
| `business-models-guide.md` | Бизнес-модели: типы, выбор, юнит-экономика | `it-base` / `misc-vault` |
| `business-schemas-processes-methodology.md` | Бизнес-схемы и процессы: нотации, как рисовать | `it-base` |
| `color-contrast-accessibility-methodology.md` | Цвет, контраст, доступность UI (WCAG) | `it-base` |
| `cybersecurity-methodology.md` | Кибербезопасность: модели угроз, практики, чек-листы | `it-base` |
| `dev-methodologies-principles.md` | Методологии/принципы разработки (Agile, YAGNI, приоритизация) | `it-base` |
| `development-process-methodology.md` | Процесс разработки: канон ROADMAP+WATCHLOG, task-tracking | остаётся (родня докам 04/19/24) |
| `diagrams-notations-gost-methodology.md` | Диаграммы, нотации, ГОСТы (UML, C4, ER, draw.io-грабли) | `it-base` |
| `expertise-social-promotion-methodology.md` | Заход через экспертность, продвижение в соцсетях | `misc-vault` |
| `incident-process-documentation-methodology.md` | Документирование инцидентов и процессов (расширенная теория) | остаётся (пара к `reports/documentation-methodology.md`) |
| `languages-tools-production-methodology.md` | Языки и инструменты в продакшене IT | `it-base` |
| `market-analysis-reference.md` | Анализ рынка: TAM/SAM/SOM, бенчмарки, источники | `it-base` / `misc-vault` |
| `research-analysis-academic-methodology.md` | Анализ исследований: академический фокус | `edu-base` |
| `research-analysis-business-methodology.md` | Анализ исследований: бизнес-метрики | `it-base` |
| `scientific-article-gost.md` | Научная статья по ГОСТ: структура, оформление, подача | `edu-base` / `academic-portfolio` |
| `software-lifecycle-standard.md` | Стандарт управления жизненным циклом программного комплекса | `it-base` |
| `team-roles-process-methodology.md` | Команда, роли, процесс и контроль задач в IT | `it-base` |
| `naming-convention.md` | Конвенция имён code-репы (файлы, отчёты, миграции) — образец | остаётся (референс для code-реп) |
| `solution-factory-course.md` | Конспект питч-курса «Фабрика решений»: CustDev, PSF/PMF, JTBD, TAM/SAM/SOM, юнит-экономика (примеры FINPILOT — боевые) | `it-base` / `misc-vault` |
| `market-entry-domestic-vs-international.md` | Карта факторов «домашний рынок vs международный» — прикладывается к любому продукту | `it-base` / `misc-vault` |
| `market-analysis-benchmarks-international.md` | Бенчмарки международной оценки: пороги TAM/SAM/SOM и метрик, отличия от РФ-оценки | `it-base` / `misc-vault` |
| `scopus-wos-publication-guide.md` | Публикации Scopus/WoS: базы, квартили, процесс подачи, инструменты проверки | `edu-base` / `academic-portfolio` |
| `rinc-vak-publication-guide.md` | Публикации РИНЦ/ВАК: требования, процесс, статусы | `edu-base` / `academic-portfolio` |
| `academic-degrees-kandidat-doktor.md` | Кандидат и доктор наук: путь, требования, процедуры | `edu-base` / `academic-portfolio` |
| `academic-degrees-titles-ru-world.md` | Степени и звания: система РФ против мировой (PhD и др.) | `edu-base` / `academic-portfolio` |
| `article-chat-bootstrap-prompt.md` | Bootstrap-промпт чата написания научной статьи (рабочий шаблон Claude-сессии) | `edu-base` |
| `QA.md` | QA-регламент code-репы: уровни тестирования (smoke/fast/full/deep), формат фиксации дефектов — образец | остаётся (референс для code-реп) |
| `sandbox-runbook.md` | Раннбук песочницы Claude: готовые команды, известные грабли | остаётся (сквозной инструмент) |
| `tool-call-channel-failures.md` | Сбой канала тул-коллов Claude: симптомы и протокол | остаётся (выжимка — `15-gotchas` §14) |
| `engineering-practices.md` | Инженерные практики code-репы: TDD, гейты, DoD — образец | остаётся (референс для code-реп) |
| `test-run-optimization.md` | Что гонять и когда: узкий цикл vs полный прогон тестов | остаётся (референс для code-реп) |
| `llm-transformers-study-guide.md` | Учебный справочник по LLM/трансформерам: архитектура (токены/embedding/attention/softmax), стадии обучения (pretrain/SFT/RLHF), «LLM OS», безопасность (jailbreak/prompt injection/data poisoning), глоссарий | **`edu-base`** / `it-base` (тематический учебный контент — кандидат на переезд, `01` §2.5) |

> Шаблоны требований (`requirements_sop*.md`, `srs-guide.md`) и юзабилити-отчёта уехали не сюда,
> а в свои типовые папки — `../reports/requirements/` и `../reports/testing/` (диспетчер `19` §1).

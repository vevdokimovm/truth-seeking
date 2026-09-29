# Часть 1 — смерть в заключении (A: H-01…H-08) и правоохранители / сделка / сокрытие (F: H-31…H-38)

> **Дата прохода:** 2026-09-25 · **Метод:** `HYPOTHESES.md` «Как использовать» + `efta_search.py` (FTS5 по страницам) + сверка цитат с оригиналом через `efta_page_png.py`.
>
> **Охват корпуса (честно):** проиндексированы целиком DS1–8 и DS12 (14 824 документа, ~40,5 тыс. страниц: файлы FBI, большое жюри, записи MCC/BOP, почта SDNY, дело 2019 г.) и лишь ~1–2 тыс. документов DS11. **DS9, DS10 и основная часть DS11 (~2,7 млн страниц) не обработаны.** Поэтому «нет попаданий» = «⚪ в обработанной части нет данных», а не опровержение, если только документ прямо не противоречит утверждению.
>
> **Шкала:** 🟢 документы подтверждают · 🟡 частично (факт есть, умысел/интерпретация не доказаны) · 🔴 документы опровергают · ⚪ в обработанной части нет данных.
>
> **Правило цитат:** «✓ сверено глазами» = цитата сличена с отрендеренной страницей оригинала (archive.org), а не с OCR/текстовым слоем. Этика: имена жертв не приводятся; «упомянут ≠ виновен».
>
> **Важная оговорка по типам документов.** Главный документ блока A — отчёт DOJ OIG о содержании Эпштейна в MCC — в корпусе представлен **рабочим черновиком (март 2023, «DRAFT, Limited Official Use»)**, а не финальной публичной версией (июнь 2023); плюс черновик пресс-релиза OIG с правкой. Выводы по существу в черновике совпадают с тем, что известно из финальной версии, но это нужно помнить.

---

## A. Смерть в заключении

### H-01 — официальная версия (суицид через повешение, без посторонних) верна

**Вердикт: 🟡 → склоняется к 🟢 по факту суицида, 🟢 по халатности.** Прошлая сессия: 🟡. Корпус **укрепляет** официальную версию: в обработанной части есть сразу три независимых по ведомству вывода (OCME — причина/род смерти; FBI — «no criminality», дело закрыто 05.12.2022; OIG — «не найдено доказательств, противоречащих выводу FBI»). До чистого 🟢 не поднимаю: сам протокол вскрытия OCME в обработанной части не найден (только пересказы и FOIA-переписка о его редактировании), а видео с камеры у двери камеры отсутствует (см. H-05).

- `EFTA00035805 p.1` (DS8, меморандум OIG о получении закрывающего EC FBI) — "The FBI has found no criminality pertaining to the death of inmate Epstein and has closed their case (90A-NY-3151227) on December 5, 2022." ✓ сверено глазами
- `EFTA00035986 p.3` (DS8, черновик отчёта OIG, март 2023) — "The Medical Examiner who performed the autopsy told the OIG that Epstein's injuries were consistent with suicide by hanging and that there was no evidence of defensive wounds that would be expected if his death had been a homicide." ✓ сверено глазами
- `EFTA00035824 p.2` (DS8, черновик пресс-релиза OIG 22.06.2023) — "The OIG reviewed the available recorded video footage and found that, between approximately 10:40 p.m. on August 9 and about 6:30 a.m. on August 10, no one was seen entering Epstein's cell tier from the SHU common area." ✓ сверено глазами
- `EFTA00024007 p.1` (DS8, письмо SDNY; дубли `EFTA00018899`, `EFTA00031006`) — "OCME has officially concluded Epstein's cause of death was hanging and the manner of death was suicide." (текстовый слой, глазами не сверялось)

**Запросы:** `"manner of death"`, `"cause of death"`, `"medical examiner"`, `autopsy`, `"suicide watch"`, `"no criminality"`/`criminality`, `"90A-NY-3151227"`, `"pronounced dead"`, `"Office of the Inspector General" AND cellmate`.
**Не проверено:** полный протокол вскрытия OCME (есть в FOIA-переписке 2021 как «OCME Report of Autopsy», `EFTA00023398`, сам отчёт не найден) — искать в DS9–11 по `"Report of Autopsy"`, `"M19-"` (номер дела OCME), `"Roman"`; финальная версия отчёта OIG — `"Investigation and Review of the Federal Bureau of Prisons' Custody"`.

### H-02 — Эпштейн убит, суицид — прикрытие

**Вердикт: 🟡 → ближе к 🔴 для «доказанного убийства».** Прошлая сессия: 🟡. Корпус содержит **только заявления об убийстве** (частный патологоанатом семьи в пересказе СМИ, наводки граждан), но ни одного следственного документа, который бы их подтверждал; официальные выводы трёх ведомств прямо противоположны. Факт перелома подъязычной кости подтверждён документом, но сам же документ квалифицирует его как совместимый с повешением. Полностью 🔴 не ставлю: видео с яруса не сохранилось (H-05), а протокол вскрытия в обработанной части не найден.

- `EFTA00027265 p.1` (DS8, предварительные итоги вскрытия, письмо NYPD/FBI task force 11.08.2019) — "Ligature marks around the neck, petechia hemorrhage in the eyes, fractured hyoid bone-All the injuries noted are consistent with the circumstances surrounding the death." ✓ сверено глазами. Там же: "the family hired private pathologist, Dr. Baden Michael, who was present for the autopsy." ✓
- `EFTA00031393 p.1` (DS8, внутренняя переписка, отправители зачернены, 30.10.2019) — реакция на заявление Бадена Fox News: "Obviously we can't officially comment but we are confident it's bunk — this guy is pretty controversial and they should consider the source". ✓ сверено глазами. *Это мнение сотрудников, не экспертиза.*
- `EFTA00038986 p.1` (DS8, **наводка гражданина** в FBI NTOC, 22.02.2023, подписана именем брата Эпштейна) — "Jeffrey Epstein was murdered in his jail cell. I have reason to believe he was killed because he was about to name names." ✓ сверено глазами. *Это доказательство того, что утверждение было сделано, а не того, что оно верно; в той же наводке назван предполагаемый заказчик — публичная фигура; упомянут ≠ виновен, никаких подтверждений в корпусе нет.*
- `EFTA00019348 p.3` (DS8, внутреннее расследование BOP по эпизоду 23.07.2019) — сам Эпштейн 31.07.2019: "Epstein stated he has never had any issues with Tartaglione, he is not threatened by Tartaglione, and he do not want to make up something that isn't there." ✓ сверено глазами. (Противовес: в хронологии защиты Тартальоне, `EFTA00018224 p.1`, записано "JE claims NT assaulted him" — версии Эпштейна о 23.07 расходятся между документами.)

**Запросы:** `hyoid`, `Baden`, `petechia*`, `ligature`, `strangulation OR homicide`, `Epstein AND murdered AND (tip OR NTOC)`, `Tartaglione AND (attack* OR assault*)`, `"still alive"`.
**Не проверено:** полный протокол вскрытия и гистология; заключение Бадена целиком (в корпусе только пересказ СМИ); FD-302 заключённых-свидетелей по ночи 9–10.08 (есть серийный номер дела `90A-NY-3151227`, в обработанной части ~6 протоколов FD-302 персонала). В DS9–11 искать `"90A-NY-3151227"`, `"second autopsy"`, `"inmate interview" AND Epstein`.

### H-03 — охрана умышленно обеспечила отсутствие надзора как часть плана

**Вердикт: 🟡.** Прошлая сессия: 🟡 — **без изменений**. Фальсификация обходов и пересчётов доказана документально (обвинительное заключение, признания, OIG). Умысел на убийство не подтверждён ни одним документом; OIG, наоборот, оценил поведение дежурных как несовместимое с осведомлённостью о вреде.

- `EFTA00009747 p.12` (DS8, обвинительное заключение US v. Noel & Thomas, 19-cr-830; дубли `EFTA00010968`, `EFTA00017915`, `EFTA00015438`, `EFTA00031025`) — "NOEL told Supervisor-1 "we did not complete the 3 a.m. nor 5 a.m. rounds." THOMAS stated, "we messed up," and "I messed up, she's not to blame, we didn't do any rounds."" ✓ сверено глазами
- `EFTA00035986 p.19` (DS8, черновик OIG) — "primarily remained seated in the SHU Officers' Station—sometimes without moving for a period of time, suggesting that they were asleep—and conducted a variety of internet searches on MCC New York computers." ✓ сверено глазами
- `EFTA00035986 p.17` (DS8, черновик OIG) — "reaction on the morning of August 10 upon finding Epstein hanging in his cell … was consistent with their being unaware of any potential harm to Epstein" (текстовый слой; на странице обширные серые плашки редактирования)
- `EFTA00009747 p.12` — "as confirmed by video surveillance, no one else entered the SHU … and no one entered the tier in which Epstein was housed." ✓ сверено глазами

**Запросы:** `"Tova Noel" OR Noel`, `"Michael Thomas"`, `"count slip*"`, `"we messed up"`, `polygraph* AND (Noel OR Thomas OR MCC)`, `NEAR(bribe* guard*, 15)`.
**Не проверено:** полные FD-302/OIG-интервью Ноэль и Томаса (выполнены как условие DPA в июне 2021, `EFTA00022014`); результаты «internet searches» (есть `EFTA00027177` — «timeline … of the video review and internet search history»). В DS9–11: `"Noel" AND interview AND OIG`, `"internet search"`.

### H-04 — «пропавшая минута» в видео скрывает момент убийства

**Вердикт: ⚪.** Прошлая сессия: 🟡 (аномалия задокументирована прессой/DOJ). В обработанной части корпуса **нет ни одного документа о «пропавшей минуте»**: это свойство видеофайла, опубликованного DOJ в июле 2025, а сопроводительные материалы 2025 г. в DS1–8/DS12 не попали. Ни подтвердить, ни опровергнуть по корпусу нельзя.

- Косвенно: `EFTA00017950 p.2` (DS8, техническая справка FBI 14.08.2019) — камера общего зала SHU была на работающем DVR #1, с которого FBI экспортировало запись: "Another team from FBI FAVU is currently on-site working on exporting video from the third camera of interest connected to DVR system #1, which is currently operational". ✓ сверено глазами

**Запросы:** `"missing minute"`, `NEAR(video gap, 10)`, `NEAR(footage minute, 10)`, `NEAR(video missing, 8)`, `NEAR(video skip*, 8)`, `"11:58"`, `"11:59"`, `NEAR(midnight reset, 10)`, `"metadata" AND video AND Epstein`.
**Не проверено:** отчёт FAVU/CART по экспорту видео с DVR #1 и метаданные файла 2025 г. В DS9–11: `FAVU`, `"DVR system #1"`, `"video export"`, `"NiceVision"`, `timestamp`.

### H-05 — две неисправные камеры у блока — умышленный саботаж

**Вердикт: 🟡.** Прошлая сессия: 🟡 — **без изменений по вердикту, но с важным уточнением фактуры**: отказ произошёл на **целом регистраторе** (DVR #2, яруса SHU) 29.07.2019 — **до** смерти, а контракт на замену устаревшей системы подписан в сентябре 2018 (до ареста). Отказ был «recognized on August 8, 2019», то есть за 2 дня до смерти, и не был устранён. Это документирует халатность и хроническую проблему, но ничего не говорит об умысле. Отдельный факт: изъятие дисков «на ходу» могло повредить данные (сделано при попытке восстановления).

- `EFTA00017950 p.2` (DS8, справка FBI 14.08.2019) — "on 07/29/19, DVR system #2 had two to three hard drives fail causing most of that system to stop recording. Two of the three camera feeds of obvious interest resided on DVR system #2, meaning they were not recording at the time of the suicide on 08/10/19." ✓ сверено глазами
- `EFTA00035807 p.1` (DS8, меморандум OIG) — "the MCC New York's camera system failure recognized on August 8, 2019"; вложение №1: "MCC New York GSA Contract for a Camera System Upgrade dated September 21, 2018." ✓ сверено глазами
- `EFTA00026545 p.2` (DS8, письмо SDNY суду по делу Тартальоне, 08.01.2020) — "the FBI has determined that, on or about July 29, 2019, the Tier DVR suffered a system failure. As a result, the FBI been unable to recover any footage from the Tier DVR, and is unlikely to recover any video." ✓ сверено глазами
- `EFTA00036136 p.1` (DS8, меморандум завхоза MCC 13.08.2019) — "when the FBI took the sixteen (16) hard drives out of the RAID without it finishing the rebuild it might have corrupted any data on the drives." ✓ сверено глазами
- `EFTA00035986 p.3` (DS8, черновик OIG, сноска 1) — "As detailed in the report, MCC New York had a history of security camera problems." ✓ сверено глазами

**Запросы:** `DVR`, `DVR AND (fail* OR malfunction* OR record*)`, `camera* NEAR(malfunction 10)`, `camera* AND (repair* OR "work order" OR inoperable OR broken) AND MCC`, `"SigNet" AND (August OR camera)`.
**Не проверено:** итог работы DFAS-DSAU по восстановлению дисков DVR #2; сам наряд-заказ на ремонт от 19.07.2019 и сервисная заявка SigNet от 08.08.2019 (перечислены во вложениях `EFTA00035800`, `EFTA00035807`, но тексты не найдены). В DS9–11: `"DFAS"`, `"hard drive" AND rebuild`, `"Service Request # 24975"`.

### H-06 — сокамерника убрали намеренно, чтобы оставить Эпштейна одного

**Вердикт: 🟡.** Прошлая сессия: 🟡 — **без изменений**. Уточнение фактуры: по документам сокамерника перевели **9 августа (за день до смерти)**, а не «за 6 дней»; перевод назван «routine, pre-arranged» и значился в суточном списке выбытия. Нарушение предписания психологов о сокамернике и то, что персонал об этом знал, — доказано. Цели «оставить одного» в документах нет; OIG описывает цепочку непереданных распоряжений.

- `EFTA00009747 p.7` (DS8, обвинительное заключение) — "On August 9, 2019, Epstein's cellmate was transferred out of the MCC in a routine, pre-arranged transfer at approximately 8 a.m. Despite the MCC's psychological staff's direction that Epstein have a cellmate, no new cellmate was assigned to Epstein's cell." ✓ сверено глазами
- `EFTA00035970 p.12` (DS8, черновик OIG) — "The OIG investigation found that each of these employees knew that Epstein was required to have a cellmate at all times per the Psychology Department's directive." ✓ сверено глазами
- `EFTA00035824 p.2` (DS8, черновик пресс-релиза OIG) — "MCC New York staff knew that Epstein did not have a cellmate as was required, but did not take steps to ensure that Epstein was assigned a new cellmate." ✓ сверено глазами

**Запросы:** `cellmate`, `NEAR(cellmate transferred, 10)`, `"cellmate" AND "Psychology"`, `"psychological observation"`, `WAB`.
**Не проверено:** основание перевода сокамерника (в описи `EFTA00035116` — «Court documentation regarding WAB 8/9/19», сам документ не найден). В DS9–11: `"WAB"`, `"85993-054"` (рег. номер из описи — не персональные данные жертвы), `"designation" AND transfer`.

### H-07 — смерть инсценирована, Эпштейн жив («body double»)

**Вердикт: 🔴 (в пределах обработанной части).** Прошлая сессия: ⚪ не оценивалось. Прямого документа «опознание ДНК/по зубам» в корпусе нет, но есть **непрерывная документированная цепочка хранения тела** (камера → больница → отпечатки и фото → охрана тела конвоем BOP → морг OCME → вскрытие в присутствии патологоанатома, нанятого семьёй). Версия «жив» в корпусе встречается только как пересказ слухов, которые SDNY пытался развеять перед потерпевшими.

- `EFTA00034505 p.2` (DS8, хронология BOP для SDNY) — "10:00 am CMC and IDO arrive at Beekman Hospital. Fingerprints and photographs taken of inmate Epstein." ✓ сверено глазами
- `EFTA00033860 p.1` (DS8, меморандум конвойного BOP 10.08.2019) — "I was responsible for watching the remains until further instruction was given along with another correctional officer." … "1257 Staff from OCME depart from New York Presbyterian hospital and transport remains to city morgue location". ✓ сверено глазами
- `EFTA00027265 p.1` (DS8) — на вскрытии присутствовал патологоанатом, нанятый семьёй (см. H-02). ✓ сверено глазами
- `EFTA00023920 p.3` (DS8, статья Daily Beast в почте SDNY, 29.10.2019) — "The U.S. Attorney's Office wanted to put to rest some of those conspiracy theories— that he was killed, that he's still alive." (текстовый слой; это пересказ адвоката в СМИ)

**Запросы:** `"body double"`, `"still alive"`, `NEAR(Epstein alive, 5)`, `"not dead"`, `NEAR(body identif*, 8)`, `cremat*`, `NEAR(body switch*, 8)`, `NEAR(faked death, 5)`, `decedent`, `NEAR(body released, 10)`, `"pronounced dead"`.
**Не проверено:** формальное опознание в протоколе OCME, дактилоскопическое сличение FBI. В DS9–11: `"positive identification"`, `"identified by"`, `fingerprint AND OCME`.

### H-08 — смерть Брюнеля (Париж, 2022) — тоже убийство, «устранение свидетелей»

**Вердикт: ⚪.** Прошлая сессия: ⚪ — **без изменений**. В обработанной части нет ни одного документа об обстоятельствах смерти Брюнеля; он упоминается лишь как «deceased» в заметках DANY. Корпус документирует мотивную часть нарратива лишь частично: в 2019 Брюнель через адвоката **отказался** сотрудничать с SDNY; французское следствие (три судьи) вело дело в 2021.

- `EFTA02731082 p.65` (DS12, привилегированный меморандум SDNY) — "the attorney indicated that Brunel was not willing to meet with us for a proffer and would invoke his Fifth Amendment privilege against self-incrimination if subpoenaed to testify in the grand jury." ✓ сверено глазами
- `EFTA02731662 p.3` (DS12, заметки о материалах DANY; дубль `EFTA02731737`) — "John Luc Brunel [deceased JE associate]". ✓ сверено глазами
- `EFTA00021720 p.2` (DS8, отчёт DOJ CRM о встрече с французскими судьями, 07.01.2021) — "There are three investigating judges assigned to this case, which is pretty unusual...and suggests its importance for them." (текстовый слой)
- Контрсигнал: `EFTA00029100 p.15` (DS8, ходатайство защиты Максвелл, сноска 9) — пересказ заметок AUSA 2016 г.: Брюнель "is wanting to cooperate". ✓ сверено глазами. *Это позиция защиты, пересказывающая чужие заметки, а не факт готовности к сотрудничеству.*

**Запросы:** `Brunel`, `Brunel AND (died OR death OR suicide OR deceased OR hanged)`, `"La Sante" OR "Sante prison"`, `"MC2"`.
**Не проверено:** французские материалы (MLAT) и любые документы 2022 г. В DS9–11: `Brunel AND 2022`, `"La Santé"`, `MLAT AND France`.

---

## F. Правоохранители, сделка 2007–2008, сокрытие

### H-31 — NPA 2007 г. было умышленным прикрытием, а не обычной сделкой

**Вердикт: 🟡.** Прошлая сессия: 🟡 — **без изменений**. Нарушение CVRA (жертв не консультировали и вводили в заблуждение) установлено судом; OPR DOJ квалифицировал решение Акосты как «poor judgment». Но тот же OPR прямо **не нашёл** признаков коррупции, влияния богатства/связей или цели «заставить жертв молчать». Оговорка: OPR — внутренний орган DOJ; независимой проверки мотива в обработанной части нет.

- `EFTA00011475 p.12` (DS8, резюме отчёта OPR, ноябрь 2020; дубли `EFTA00013359`, `EFTA00023059`) — "OPR did not find evidence that his decision was based on corruption or other impermissible considerations, such as Epstein's wealth, status, or associations." ✓ сверено глазами
- `EFTA00011475 p.12` — "Nevertheless, OPR concludes that Acosta's decision to resolve the federal investigation through the NPA constitutes poor judgment." ✓ сверено глазами. И: "OPR did not find evidence that the lack of consultation was for the purpose of silencing victims." ✓
- `EFTA00011475 p.8` (DS8, резюме OPR) — пересказ вывода суда: "the government affirmatively misled victims about the status of the federal investigation." (текстовый слой)

**Запросы:** `"Non-Prosecution Agreement"`, `"Crime Victims"`, `"violated the CVRA" OR "violated the Crime Victims"`, `"affirmatively misled"`, `"Office of Professional Responsibility"`, `"poor judgment"`, `Villafana`, `Sloman`, `Lefkowitz`, `Marra`.
**Не проверено:** полный текст отчёта OPR (в обработанной части — резюме), решение судьи Марры 2019 г. в оригинале. В DS9–11: `"Doe v. United States" AND 9:08-cv-80736`, `"breakfast meeting"`.

### H-32 — Акосте велели «отступить», потому что Эпштейн «принадлежал разведке»

**Вердикт: 🟡 → склоняется к 🔴.** Прошлая сессия: ⚪. Корпус содержит **оба конца цитаты**: (1) саму фразу — но только как пересказ статьи Daily Beast, пересланный AUSA SDNY; (2) **показания самого Акосты под запись в OPR**, где он дважды отрицает, что знал о статусе «intelligence asset» или говорил кому-либо об этом. Документального подтверждения фразы (источник, запись интервью переходной команды) нет. Не ставлю 🔴 безоговорочно: отрицание фигуранта — не опровержение, а оговорка про «classified information» оставляет ему пространство.

- `EFTA00030182 p.1` (DS8, письмо AUSA SDNY 10.07.2019, пересказ СМИ) — "I was told Epstein 'belonged to intelligence' and to leave it alone," he told his interviewers in the Trump transition". ✓ сверено глазами. *Это цитата из статьи, а не документ переходной команды.*
- `EFTA00009116 p.105` (DS7, стенограмма интервью OPR с А. Акостой, с. 404) — на вопрос, знал ли он, что Эпштейн был "an intelligence asset of some sort": "-- I'm not aware of it." … "Did defense counsel ever say to you that Epstein had that status?" — "Not to my recollection." ✓ сверено глазами
- `EFTA00009116 p.106` (DS7, та же стенограмма, с. 405) — "I also don't know where press reports … that I told someone that he was an intelligence asset. I do not know where that came from." … "the answer is no, and no." ✓ сверено глазами

**Запросы:** `"belonged to intelligence"`, `Acosta AND intelligence`, `Acosta AND (CIA OR Mossad OR "intelligence asset")`, `Epstein AND "intelligence asset"`, `"above my pay grade"`.
**Не проверено:** материалы переходной команды 2016–2017, первичный источник Daily Beast. В DS9–11: `"transition" AND Acosta`, `"intelligence asset"`, `"Vicky Ward"`.

### H-33 — мемо DOJ/FBI 07.2025 («списка клиентов нет») — инструмент прикрытия

**Вердикт: ⚪.** Прошлая сессия: ⚪ — **без изменений**. Самого мемо июля 2025 г. и сопровождающих документов в обработанной части нет. Строки «client list» в корпусе относятся к **спискам клиентов адвокатов потерпевших** (для встречи с DOJ, 2020), а не к «списку клиентов Эпштейна». Есть след масштабной обработки файлов FBI в марте 2025 (см. «Неожиданные находки»), но выводов этой обработки в корпусе нет.

- `EFTA00038298 p.1` (DS8, письмо FBI 27.10.2020) — "Attached is Brittany's client list." (текстовый слой; речь о клиентах адвоката потерпевших)
- `EFTA02730274 p.1` (DS12, листинг каталога FBI) — "\\ids-fs-prod\prod\DCU\THE BIG E\3-TIFs\3.12.2025 …" (текстовый слой; путь к папкам обработки марта 2025)

**Запросы:** `"client list"`, `blackmail*`, `"no credible evidence"`, `"Epstein Files Transparency"`, `Patel`, `Bongino`, `"2025"`.
**Не проверено:** всё 2025–2026 гг. В DS9–11: `"no client list"`, `"incriminating client list"`, `memo AND July 2025`, `"third parties"`.

### H-34 — DOJ избыточно редактировал/удерживал документы ради защиты элит

**Вердикт: ⚪ (для спора 2025–2026 гг.).** Прошлая сессия: 🟡. Документов по делу *Phang v. Blanche*, журналам редактирования и спору 2025–2026 в обработанной части нет — вердикт прошлой сессии корпусом **не подтверждается и не опровергается**. Что корпус документирует: практику **законных** изъятий ранее (FOIA-иск Radar Online v. FBI, 2021 — категорическое удержание по исключению 7(A) на время следствия) и точечные редакции из соображений приватности (фото из протокола вскрытия). Мотива «защита элит» в этих документах нет.

- `EFTA00015219 p.25` (DS8, черновик декларации FBI RIDS по делу Radar Online v. FBI, 2021) — "the FBI has described the types of responsive records from the pending investigative files, which are being withheld in full pursuant to FOIA Exemption (b)(7)(A)." ✓ сверено глазами
- `EFTA00023398 p.2` (DS8, переписка SDNY о FOIA-выдаче протокола вскрытия, 2021) — "To the extent we're redacting the closeup photos from page 13, shouldn't we also redact the entire photo on page 12?" (текстовый слой)

**Запросы:** `"redaction log"`, `"privilege log"`, `Phang`, `"Democracy Defenders"`, `"deliberative process"`, `"Epstein files"`.
**Не проверено:** журналы редактирования EFTA-выгрузки, пропуски Bates-номеров (сверка с `library/05`). В DS9–11: `"redaction"`, `"withheld in full"`, `"Exemption 7(C)"`.

### H-35 — DOJ логировал поисковые запросы сотрудников Конгресса

**Вердикт: ⚪.** Прошлая сессия: 🟢 (по прессе/`library/05`). В обработанной части корпуса документов об этом нет — это события февраля 2026 г., вне охвата DS1–8/DS12. Корпус вердикт прошлой сессии **не подтверждает и не опровергает**. Единственное попадание `"search history"` (`EFTA00027177`) относится к поисковой истории **охранников MCC** в ночь смерти — другой сюжет.

**Запросы:** `Jayapal`, `"search history"`, `Congress* AND (review OR oversight) AND Epstein AND files`, `"reading room"`.
**Не проверено:** всё 2026 г.; скорее всего, в EFTA-выгрузку это вообще не входит.

### H-36 — протоколы FD-302 о соучастниках умышленно изъяты из публикации

**Вердикт: ⚪ (с документированным фоном).** Прошлая сессия: 🟡. В обработанной части **очень мало FD-302** (≈6 документов, почти все — допросы персонала MCC по делу о смерти). Опись дела FBI в DS12 перечисляет десятки интервью (включая попытку допроса Брюнеля), то есть 302-е **существуют**, но их текстов в DS1–8/DS12 нет. Утверждать «умышленно изъяты» нельзя, пока не обработаны DS9–11: отсутствие в 40 тыс. страниц из 2,7 млн — не доказательство изъятия.

- `EFTA00015219 p.25–26` (DS8, декларация FBI 2021) — FD-302 входят в категории, удерживаемые целиком по 7(A) на время следствия (см. H-34). ✓ сверено глазами (с. 25)
- `EFTA02730741 p.126` (DS12, опись сериалов дела 50D-NY-3027571) — строка "(U) Interivew of Jean Brunel" среди перечня интервью. (текстовый слой; дубль описи `EFTA02730486`)
- `EFTA02730271 p.2` (DS12, разведсправка FBI NY 2022) — ссылки вида "(FBI I FD-302 50D-NY-3027571, serial 5801 …)" — 302-е цитируются во внутренних продуктах FBI. (текстовый слой)

**Запросы:** `"FD-302"`, `"FD 302"`, `"Date of entry"`, `"Date of transcription"`, `"interview of"`.
**Не проверено:** главный объём 302-х, вероятно, в DS9–11. Искать `"FD-302" AND 50D-NY-3027571`, `"Date of entry"`, `"Continuation of FD-302"` и сверять с описью сериалов DS12.

### H-37 — отставка Бонди (04.2026) — следствие сокрытия по файлам Эпштейна

**Вердикт: ⚪.** Прошлая сессия: 🟡 (по прессе). В корпусе единственное попадание по `Bondi` — OCR-вариант фамилии адвоката «Bondy» в списке юрфирм. События 2026 г. вне охвата.

**Запросы:** `Bondi`, `Blanche`, `resignation AND "attorney general"`.
**Не проверено:** всё 2026 г.; в EFTA-выгрузку, вероятно, не входит.

### H-38 — мягкое наказание охранников MCC — институциональное прикрытие

**Вердикт: 🟡.** Прошлая сессия: 🟡 — **без изменений**. Корпус документирует **и мягкость, и официальную мотивировку**: DPA (6 мес. надзора, 100 часов общественных работ, признание вины, обязательное сотрудничество с OIG) обоснован «практикой Департамента в подавляющем большинстве» подобных дел о фальсификации пересчётов и поддержан FBI и OIG. Это объяснение проверяемо, но в корпусе нет статистики по «другим делам», чтобы его проверить. Трактовка «прикрытие» остаётся интерпретацией.

- `EFTA00029185 p.2` (DS8, UMR SDNY в офис Генпрокурора, 20.05.2021; дубль `EFTA00013389`) — "deferring the defendants' prosecution is an outcome consistent with the interests of justice, the mitigating personal circumstances of the defendants, and the Department's practice in the overwhelming majority of other cases in which correctional officers have been investigated or charged with falsifying count or round forms." ✓ сверено глазами
- `EFTA00029185 p.2` — "This outcome is supported by the investigative agencies, the Department of Justice, Office of the Inspector General, as well as the Federal Bureau of Investigation". ✓ сверено глазами
- `EFTA00023087 p.1` (DS8, DPA Tova Noel, 19 Cr. 830 (AT), 25.05.2021) — срок отсрочки "for the period of six months from the date of this Agreement." (текстовый слой)

**Запросы:** `"deferred prosecution"`, `"deferred prosecution" AND (Noel OR Thomas)`, `"community service"`, `"Noel/Thomas FOIA"`.
**Не проверено:** данные о «других случаях» фальсификации пересчётов; протоколы интервью Ноэль/Томаса с OIG (июнь 2021). В DS9–11: `"count slip" AND "deferred"`, `"Noel" AND OIG AND interview`.

---

## Неожиданные находки

1. **Утраченное видео эпизода 23.07.2019.** Защита Тартальоне заранее (25.07) запросила сохранить видео у их общей с Эпштейном камеры; MCC сохранило **видео другого яруса** из-за ошибки в компьютерной системе, и нужная запись перестала существовать. — `EFTA00026545 p.1` (DS8, письмо SDNY суду, 08.01.2020): "the MCC inadvertently preserved video from the wrong tier within the MCC, and, as a result, video from outside the defendant's cell on July 22 – 23, 2019 no longer exists." ✓ сверено глазами. Это вторая, независимая от 10.08 потеря ключевого видео — сильнейший документированный аргумент дискурса «видео исчезают», при этом с документированным бытовым объяснением.
2. **За 12 дней до смерти обсуждалось возможное сотрудничество Эпштейна.** — `EFTA00038617 p.2` (DS8, хронология FBI CID, утв. 17.07.2024): "On July 29, 2019, FBI and SDNY met with Epstein's attorneys, who, in very general terms, discussed the possibility of a resolution of the case, and the possibility of the defendant's cooperation." ✓ сверено глазами. Даёт документальную опору тезису о «мотиве» в H-02, но сам факт переговоров ≠ доказательство убийства. Там же: FBI после смерти открыло дело именно как "investigation into the possible assault of a federal inmate". ✓
3. **Отказ камер был известен до смерти и связан с давно назревшей заменой.** DVR яруса SHU отказал 29.07, «recognized on August 8», контракт на замену подписан 21.09.2018; установка новой системы началась 12.08.2019 — через два дня после смерти. — `EFTA00017950 p.2`, `EFTA00035807 p.1` ✓ сверено глазами (цитаты в H-05).
4. **Внутренняя реакция на заявление Бадена.** — `EFTA00031393 p.1` (DS8, 30.10.2019): "we are confident it's bunk … so do what you can to tamp down any hysteria." ✓ сверено глазами. Сторонники версии сокрытия прочтут это как «установку гасить», скептики — как управление коммуникациями при уже имеющемся заключении OCME; сам документ ни то, ни другое не доказывает.
5. **SDNY в 2016 г. получал предложение возбудить дело против Максвелл и Эпштейна** — по версии защиты Максвелл, со ссылкой на заметки AUSA. — `EFTA00029100 p.15` (DS8, ответ защиты Максвелл): "The record is surpassingly clear: In February 2016 and the weeks and months after, [зачернено] attorneys "pitched" a prosecution of Maxwell and Epstein." ✓ сверено глазами. *Это позиция стороны в процессе.* Релевантно дискурсу «почему не преследовали раньше».
6. **Охранник MCC, дежуривший в ночь смерти в соседнем блоке, позже обвинён во взятке (не связанной с Эпштейном).** — `EFTA00025524 p.1` (DS8, служебная сводка SDNY, 18.09.2020): "Adams was working in the SAMS unit the night of Epstein's suicide, and we interviewed him … this charge spun out of that" (текстовый слой; по сути эпизода — сексуальное вымогательство у посетительницы, провозившей контрабанду). Показывает общий уровень злоупотреблений в MCC, связи со смертью Эпштейна документы не устанавливают.
7. **FBI провело массовую переобработку файлов в марте 2025 («THE BIG E»).** — `EFTA02730274 p.1` (DS12, листинг каталогов FBI, 194 стр.) — пути вида "DCU\THE BIG E\3-TIFs\3.12.2025". Это предшествует мемо июля 2025 (H-33); содержания выводов в корпусе нет.
8. **FBI отбирало «сомнительные» версии и само заводило NTOC-наводки об убийстве в дело.** Опись дела содержит строку "NTOC2020 … E-Tip: Involvement with Jeffrey Epstein, Sex Trafficking, and Murder" (`EFTA02730486 p.134`, DS12, текстовый слой) — то есть наводки регистрировались, а не выбрасывались; их проверка в корпусе не отражена.

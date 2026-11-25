# Radar de Vacantes

A daily, automated report of remote job openings, filtered by my own rules.

Every day it pulls new remote jobs from the [Himalayas](https://himalayas.app) public API, keeps only the ones that fit my profile, discards the rest with the exact rule that removed each one, and writes a short Markdown report. It never applies on my behalf: it finds, filters and explains; I decide.

## Why I built it

I'm a Finance and International Business student looking for remote roles in finance, data and automation. Reviewing job boards by hand, I went through 394 postings and kept finding the same problems: titles that hide senior requirements, "worldwide" jobs that only hire in the US, the same description copied across several companies, and commission-only sales roles disguised as junior positions. This project turns those manual checks into rules that run on their own.

## How it works

```
config.json ──► himalayas.py ──► filtros.py ──► informe.py ──► informes/YYYY-MM-DD_HHMM.md
 (searches,      (fetch, paginate,   (rules: keep      (report with reasons
  thresholds)     de-duplicate)       or discard)       and official links)
                         │
                  datos/vistas.json  (jobs already reviewed are not repeated)
```

| Rule | Discards a job when… |
|---|---|
| Expired | its expiry date has passed |
| Contract type | it is not Full Time or Contractor |
| Location | it does not accept Colombia (worldwide jobs pass) |
| Time zone | none of its allowed time zones is within ±3 h of UTC-5 |
| Seniority | its level or title is senior, lead, manager, director… |
| Location contradiction | the label allows Colombia but the text requires US/UK/EU work authorization |
| Commission | the text describes commission-only pay |
| Experience | it asks for more years of experience than I have (configurable) |
| Certifications | it requires a certification I don't hold (CPA, CFA, PMP…) |
| Copied template | the same description appears under different companies, or the title starts with "Copy of" |

## Design decisions

- **API, not an AI agent, for fetching.** The pipeline runs unattended every day, so it uses plain HTTP calls: deterministic, testable, free, and every discard is auditable.
- **Rules in code, settings in a file.** Searches, thresholds and accepted contract types live in `config.json`, so the same tool can be pointed at someone else's profile without touching the code.
- **Explain every decision.** The report says why each job passed and which rule removed each discarded one.
- **Planned next step: AI reads, code decides.** An AI reader will extract structured signals from each description (required years, certifications, impersonation clues) as JSON, and the existing rules will compare them to my profile. The AI informs; it doesn't decide.

## Run it

Requires Python 3.10+ and no external packages.

```
python radar.py                # daily run: only new jobs
python radar.py --sin-memoria  # review everything again (demo/testing)
python pruebas.py              # run the rule tests (no internet needed)
```

On Windows, `ejecutar_radar.bat` is the entry point for the Task Scheduler daily run.

## Use it for your own job search

The tool is profile-agnostic: everything personal lives in `config.json` (searches, country, thresholds) and a private `perfil.md`. Templates (`perfil.ejemplo.md`, `CLAUDE.ejemplo.md`) and a step-by-step guide in Spanish ([GUIA.md](GUIA.md)) let anyone set it up for their own search. The repository also ships a small Claude Code agent team (`.claude/agents`) for reviewing a vacancy, drafting an application or explaining the code.

## Data and terms

Job data comes from the Himalayas public API. Following its terms, application links are used unmodified, every report credits Himalayas as the source, and generated reports are not published or redistributed (only `informes/ejemplo.md` is kept in the repository).

## How it was built

Built together with Claude Code. The rules come from my own manual review of 394 postings, and I made the product decisions; Claude Code wrote most of the code, tested it against real API data and fixed what the documentation got wrong.

---

*Mariana Venus Gutiérrez Varón — Cali, Colombia*

# foren-statistics

A Python pipeline that parses Speechwire tournament results for Nebraska forensics (speech and debate) competitors and computes season statistics, head-to-head records, Elo ratings, a judge accuracy metric, and a team depth chart.

## Status

This program has become somewhat of an exquisite corpse; it was one of the first major projects I began as a college student in data science classes circa 2022. Over the past five years, I have glommed on more features, revised past implementations, and completely rewrote the full program structure over the course of 2026 to raise the overall quality of the product. That being said, there are still many remnants of my novice programmer decisions, including inefficient edge-case handling with manual brute-force solutions tacked onto massive conditional trees that could be much more modular in the future... but it works. 

My current goals are to continue streamlining the code and removing hyper-specific statistics I have never utilized over many years and only coded in the first place just because I could. The program takes around 10 minutes to run on the complete 2025-2026 season data (28 tournaments) and I am looking to reduce that number.

## Pipeline

Raw Speechwire exports go in; standardized Excel workbooks come out. Each stage writes files that later stages read, so the pipeline runs in order:

1. **Parse results** (`parsing/results.py`): cleans raw round-by-round results into Results by Entry.xlsx
2. **Parse sections** (`parsing/sections.py`): cleans section assignments into Sections by Room.xlsx and Sections by Judge.xlsx
3. **Attach sections** (`parsing/attach_sections.py`): adds section, section-size, and judge data to Results by Entry.xlsx
4. **Compute stats** (`stats/`): competitor, school, tournament, judge, head-to-head, and Elo statistics
5. **Build the depth chart** (`stats/depthchart.py`): combines the statistics into the team depth chart

The entry point is `main.py` (fka `update_forensics.py`), which runs the full pipeline.

## Repository Layout

```text
foren-statistics/
├── main.py                    # runs the full pipeline
├── config.py                  # year, data paths, event and tournament lists
├── standardization.py         # name and event normalization
├── utils.py                   # helpers shared by two or more modules
├── formatting.py              # Excel output formatting
│
├── parsing/                   # raw Speechwire → canonical tables
│   ├── results.py                # Speechwire "Print Results" page → starts Results by Entry.xlsx
│   ├── sections.py               # Speechwire "Print List-style Schematics" page → Sections by Judge.xlsx, Sections by Room.xlsx
│   ├── attach_sections.py        # completes Results by Entry.xlsx (section, section size, and judge data added)
│   └── corrections.py            # one-off manual fixes (semifinal handling, manual corrections)
│
├── stats/                     # canonical tables → statistics, ratings, outputs
│   ├── competitors.py            # Stats by Competitor.xlsx
│   ├── schools.py                # Code/Stats by School.xlsx
│   ├── tournaments.py            # Code/Stats by Tournament.xlsx
│   ├── judges.py                 # Stats by Judge.xlsx
│   ├── h2h.py                    # H2H.xlsx, individual event sheets in Code/H2H
│   ├── elo.py                    # ELO.xlsx
│   └── depthchart.py             # Depth Chart.xlsx
│
├── reports/                   # work in progress; depthchart, formatting, and outputs migrated here?
│   └── timing.py                 # runs profiler, will control progress bar weights
│
├── experiments/               # to be added; for deprecated features or functionality not wired into the main pipeline
│   └── 
│
├── README.md
├── TODO.md
└── .gitignore
```

## Setup

Requires Python [3.x] and the packages in [requirements.txt, which I have not created yet,,,]

The pipeline reads raw exports and write workbooks to a data folder that is **not** part of this repository. Set it in `config.py`:

```python
YEAR = "25-26"
ROOT = rf"C:\path\to\your\data\folder\{YEAR}"
```

Output files are written to `ROOT`, not into the repo, and are excluded by `.gitignore`.

## Usage

```bash
python main.py
```

Run from the repository root so that `parsing` and `stats` resolve as packages.

## Data notes

Student names are not stored in this repository*. Name-correction and standardization uses a `Standardization.xlsx` file stored at `NAME_CORRECTIONS_PATH` in `config.py` that converts a "Raw Text" column into a corresponding "Standardized" column for competitor names (including group events), judge names, and school/team names.

*Well, there is a single instance within manual corrections because student names were used as speaker codes.

## Notes / TODO

- minimize cosmetic changes that don't need to be done at that stage (e.g., the ordering of columns should not be touched constantly, it only needs to be set right before output if that output even really matters)
- create_container is not fully implemented
- continue cleaning comments, line widths, line breaks between functions, and formatting in general
- calculate_recips_for_rounds within parsing.results is an incomplete generalization of calculate_finals_recips and calculate_prelims_recips
- pull_out_div_from_prelims is potentially never used?


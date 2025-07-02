# Nidus Scraper

Async downloaders for robotics hardware reference files. Requires Python 3.11
and [Poetry](https://python-poetry.org/).

## Setup

```bash
poetry install
```

Set a GitHub personal access token:

```bash
export GITHUB_TOKEN=ghp_xxx
```

## Usage

Run all scrapers:

```bash
poetry run crawl-all --workers 32
```

Files are saved under `data_raw/<source>/` and listed in `data_raw/sources.csv`.

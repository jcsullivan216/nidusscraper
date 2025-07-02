# Nidus Scraper

Async downloaders for robotics hardware reference files. Requires Python 3.11
and [Poetry](https://python-poetry.org/).

## Setup

Install dependencies with Poetry:

```bash
poetry install
```

This will create an isolated virtual environment. Use the same Poetry commands
for linting, type checking and tests.

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

Vendor product pages are discovered from domains listed in
`nidus_scraper/vendor_domains.json`. Each matching HTML page is rendered to a
PDF using a headless browser and saved under `data_raw/html_product_pages/`.

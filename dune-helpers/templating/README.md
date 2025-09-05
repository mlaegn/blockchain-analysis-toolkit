# Dune SQL Templating

## Description

Generate standardized **ClickHouse SQL** for **Dune-powered datasets** from a single YAML spec.

Each dataset renders **4 files**:

* `create_table.sql`
* `insert_full.sql` (full history via Dune `query_id_full`)
* `insert_daily.sql` (daily “yesterday” via Dune `query_id_day`)
* `insert_from_execution.sql` (ingest a specific Dune `execution_id`)

## Why

* No duplicate SQL across repos.
* One source of truth for schema & Dune IDs (`config/dune_datasets.yml`).
* Safe: API key and execution id stay as runtime env placeholders.

## Requirements

* **Python 3.10+**
* Install deps:
  ```bash
  pip install Jinja2 PyYAML
  ```

## Setup

* Edit `config/dune_datasets.yml`. Minimal shape:
  ```yaml
  datasets:
    prices:
      dune:
        query_id_full: 5701957
        query_id_day:  5701962
        param_query_id: 5723539
        start_key: start_date
        end_key:   end_date
      clickhouse:
        table: playground_max.gnosis_daily_bluechip_prices
        partition_by: toStartOfMonth(block_date)
        order_by: [symbol, block_date]
      columns:
        - name: block_date   # ClickHouse column name
          source: block_date # CSV column from Dune
          ch_type: Date
          parse: date        # date|datetime|float64|uint64|string
          csv_type: String   # CSV type for ClickHouse url() signature
        - name: symbol
          source: symbol
          ch_type: LowCardinality(String)
          parse: string
          csv_type: String
        - name: price
          source: price
          ch_type: Float64
          parse: float64
          csv_type: Float64
  ```
* (Add more datasets like `labels` the same way.)

## Render

Run the CLI to render one dataset’s SQL from templates:

```bash
# Render "prices" into a target folder (choose where you want the files to live)
python -m dune_helpers.templating.cli \
  --dataset prices \
  --out ../click-runner/queries/dune/prices
```

```bash
# Render "labels"
python -m dune_helpers.templating.cli \
  --dataset labels \
  --out ../click-runner/queries/dune/labels
```

### Where do the files go?

* Wherever you point `--out`. Commonly, render into your ingestion repo (e.g., `click-runner/queries/dune/<dataset>`).

## What Gets Generated

Each dataset produces:

* **`create_table.sql`** – ClickHouse DDL using `partition_by` and `order_by`.
* **`insert_full.sql`** – pulls all rows from `dune.query_id_full`.
* **`insert_daily.sql`** – pulls “yesterday” rows from `dune.query_id_day`.
* **`insert_from_execution.sql`** – pulls the CSV for a specific Dune execution.

_All inserts use `ClickHouse url(...)` with header auth (no API key in the URL)._

## Runtime Environment (used by the rendered SQL)

Set these when executing the SQL (e.g., via click-runner):

* `CH_QUERY_VAR_DUNE_API_KEY` → used as `headers('X-Dune-Api-Key'='{{DUNE_API_KEY}}')`
* `CH_QUERY_VAR_DUNE_QUERY_ID_FULL` → used in `insert_full.sql`
* `CH_QUERY_VAR_DUNE_QUERY_ID_DAY` → used in `insert_daily.sql`
* `CH_QUERY_VAR_DUNE_EXECUTION_ID` → used in `insert_from_execution.sql` (set by your Dune executor)

## Tips

* **Casting:** `parse` controls safe casting (e.g., `date` → `toDate(parseDateTimeBestEffort(...))`).
* **CSV signature:** `csv_type` should match the CSV the Dune API returns.
* **Parameter ranges:** Use `param_query_id` + your executor to run Dune with `start_key`/`end_key`, then ingest via `insert_from_execution.sql`.
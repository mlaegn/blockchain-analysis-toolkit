from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader

# Build a ClickHouse casting expression based on a simple "parse" hint.
def _cast_expr(col: Dict[str, str]) -> str:
    src = col["source"]
    kind = col.get("parse", "string").lower()
    if kind == "date":
        return f"toDate(parseDateTimeBestEffort({src}))"
    if kind == "datetime":
        return f"parseDateTimeBestEffort({src})"
    if kind == "float64":
        return f"toFloat64({src})"
    if kind == "uint64":
        return f"toUInt64({src})"
    # default: string passthrough
    return src

def _csv_signature(cols: List[Dict[str, str]]) -> str:
    # e.g. "block_date String, symbol String, price Float64"
    return ", ".join(f"{c['source']} {c.get('csv_type','String')}" for c in cols)

def build_context(ds: Dict) -> Dict:
    cols = ds["columns"]
    # precompute cast expressions for Jinja
    cols2 = []
    for c in cols:
        c2 = dict(c)
        c2["cast_expr"] = _cast_expr(c)
        cols2.append(c2)
    ctx = {
        "table": ds["clickhouse"]["table"],
        "partition_by": ds["clickhouse"]["partition_by"],
        "order_by": ds["clickhouse"]["order_by"],  # list
        "columns": cols2,                           # with cast_expr
        "column_names": [c["name"] for c in cols2],
        "csv_signature": _csv_signature(cols2),
        "dune": ds["dune"],  # has query_id_full/day/param + keys
    }
    return ctx

def render_dataset(templates_dir: str | Path, out_dir: str | Path, dataset_ctx: Dict) -> List[Path]:
    templates_dir = Path(templates_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=False,
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )

    files = [
        "create_table.sql.j2",
        "insert_full.sql.j2",
        "insert_daily.sql.j2",
        "insert_from_execution.sql.j2",
    ]
    written: List[Path] = []
    for name in files:
        sql = env.get_template(name).render(**dataset_ctx)
        out_path = out_dir / name.replace(".j2", "")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(sql, encoding="utf-8")
        written.append(out_path)
    return written

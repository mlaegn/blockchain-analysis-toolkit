from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader

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
    return src  # string passthrough

def _csv_signature(cols: List[Dict[str, str]]) -> str:
    return ", ".join(f"{c['source']} {c.get('csv_type','String')}" for c in cols)

def build_context(ds: Dict) -> Dict:
    cols = []
    for c in ds["columns"]:
        c2 = dict(c)
        c2["cast_expr"] = _cast_expr(c)
        cols.append(c2)
    return {
        "table": ds["clickhouse"]["table"],
        "partition_by": ds["clickhouse"]["partition_by"],
        "order_by": ds["clickhouse"]["order_by"],  # list
        "columns": cols,
        "column_names": [c["name"] for c in cols],
        "csv_signature": _csv_signature(cols),
        "dune": ds["dune"],  # has query_id_full/day/param + keys
    }

def render_dataset(templates_dir: str | Path, out_dir: str | Path, dataset_ctx: Dict) -> List[Path]:
    templates_dir, out_dir = Path(templates_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=False,
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )
    names = [
        "create_table.sql.j2",
        "insert_full.sql.j2",
        "insert_daily.sql.j2",
        "insert_from_execution.sql.j2",
    ]
    written: List[Path] = []
    for name in names:
        sql = env.get_template(name).render(**dataset_ctx)
        out_path = out_dir / name.replace(".j2", "")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(sql, encoding="utf-8")
        written.append(out_path)
    return written

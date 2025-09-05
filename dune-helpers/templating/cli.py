import argparse, yaml
from pathlib import Path
from .render import build_context, render_dataset

def main():
    ap = argparse.ArgumentParser(description="Render Dune→ClickHouse SQL for a dataset")
    ap.add_argument("--dataset", required=True, help="dataset key in dune_datasets.yml (e.g., prices, labels)")
    ap.add_argument("--config", default="config/dune_datasets.yml", help="path to datasets YAML")
    ap.add_argument("--templates", default="dune_helpers/templating/templates", help="templates dir")
    ap.add_argument("--out", required=True, help="output dir (e.g., queries/dune/prices)")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    ds = cfg["datasets"].get(args.dataset)
    if not ds:
        raise SystemExit(f"Dataset '{args.dataset}' not found in {args.config}")

    ctx = build_context(ds)
    paths = render_dataset(args.templates, args.out, ctx)
    for p in paths:
        print(p)

if __name__ == "__main__":
    main()

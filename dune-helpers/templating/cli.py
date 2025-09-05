import argparse, yaml
from pathlib import Path
from .render import build_context, render_dataset

def main():
    ap = argparse.ArgumentParser(description="Render Dune→ClickHouse SQL for a dataset")
    ap.add_argument("--dataset", required=True, help="Dataset key in config/dune_datasets.yml (e.g., prices, labels)")
    ap.add_argument("--config", default="config/dune_datasets.yml", help="Path to datasets YAML")
    ap.add_argument("--templates", default="dune_helpers/templating/templates", help="Templates directory")
    ap.add_argument("--out", required=True, help="Output dir (e.g., ../click-runner/queries/dune/prices)")
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

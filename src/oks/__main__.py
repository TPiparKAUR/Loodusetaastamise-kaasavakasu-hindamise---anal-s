"""Käsurida: ``python -m oks <käsk>``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import analysis, config, indikaatorid, kaasnev, pipeline, report, sitebuild, stats


def main() -> None:
    ap = argparse.ArgumentParser(prog="oks")
    sub = ap.add_subparsers(dest="cmd", required=True)
    agg = sub.add_parser("aggregate", help="rastrid -> plokitabelid")
    agg.add_argument("--workers", type=int, default=3)
    agg.add_argument("--only", nargs="*", default=None)
    agg.add_argument("--force", action="store_true")
    flds = sub.add_parser("fields", help="põllumassiivid -> plokitabelid")
    flds.add_argument("--force", action="store_true")
    an = sub.add_parser("analyse", help="statistiline analüüs -> data/tulemused")
    an.add_argument("--sensitivity", action="store_true", help="käivita ka tundlikkuse variandid")
    sub.add_parser("kaasnev", help="lähtekasu tulemustabelid (tüüp × seisund, suured ökosüsteemid)")
    sub.add_parser("report", help="genereeri docs/tulemused.md ja docs/andmekataloog.md")
    st = sub.add_parser("site", help="ehita veebileht")
    st.add_argument("--out", default="site")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.cmd == "aggregate":
        pipeline.run(args.workers, set(args.only) if args.only else None, args.force)
    elif args.cmd == "analyse":
        res = analysis.run()
        if args.sensitivity:
            analysis.sensitivity(stats.Params(), res["paarid"]).write_csv(config.RESULTS / "tundlikkus.csv")
    elif args.cmd == "kaasnev":
        kaasnev.build(indikaatorid.all_layers())
    elif args.cmd == "report":
        report.write_catalogue(config.ROOT / "data/teenused.csv", config.DOCS / "andmekataloog.md")
        report.write_results(config.RESULTS, config.DOCS / "tulemused.md")
        report.write_requirements(config.DOCS / "lahteulesanne.md")
    elif args.cmd == "site":
        sitebuild.build(Path(args.out))
    elif args.cmd == "fields":
        pipeline.run_fields(args.force)


if __name__ == "__main__":
    main()

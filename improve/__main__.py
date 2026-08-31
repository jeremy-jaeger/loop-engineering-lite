"""python3 -m improve {prepare|train|eval|promote}"""

import argparse
import sys

from improve.dataset import prepare
from improve.evaluate import run_suite
from improve.promote import promote
from improve.train import train


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verified-trace training flywheel (ADR-005)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--chosen", default=None)
    p.add_argument("--rejected", default=None)
    p.add_argument("--out", default=None)

    t = sub.add_parser("train")
    t.add_argument("--chosen", default=None)
    t.add_argument("--rejected", default=None)
    t.add_argument("--out", default=None)
    t.add_argument("--iters", type=int, default=200)
    t.add_argument("--backend", choices=["mlx", "peft", "plan"], default=None)
    t.add_argument("--plan-only", action="store_true")
    t.add_argument("--base-model", default=None)

    sub.add_parser("eval")
    pr = sub.add_parser("promote")
    pr.add_argument("--allow-baseline", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "prepare":
        prepare(chosen_path=args.chosen, rejected_path=args.rejected, out_dir=args.out)
    elif args.cmd == "train":
        train(
            chosen_path=args.chosen,
            rejected_path=args.rejected,
            out_dir=args.out,
            iters=args.iters,
            backend=args.backend,
            plan_only=args.plan_only,
            base_model=args.base_model,
        )
    elif args.cmd == "eval":
        run_suite()
    elif args.cmd == "promote":
        promote(allow_baseline=args.allow_baseline)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Run the bounded coax example from an exported local Palace bundle."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
import dev
import package_bundle


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    p.add_argument('--profile', choices=['memory', 'reference'], default='memory')
    p.add_argument('--seconds', type=int, default=60)
    args = p.parse_args()
    if not 1 <= args.seconds <= 1800:
        p.error('--seconds must be1..1800')
    manifest = package_bundle.verify(ROOT)
    dev.run('coax-tiny', args.output, args.seconds,
            runtime_image=manifest['runtime_image_id'],
            **package_bundle.example_options(args.profile, ROOT/'reference'))


if __name__ == '__main__':
    dev.install_signal_handlers()
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (ValueError, FileNotFoundError) as error:
        sys.exit(str(error))

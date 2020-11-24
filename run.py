# from mpc2c import nmf
import argparse
from mpc2c import settings as s

# from cylang import cylang
# cylang.compile()
# from Cython.Build import Cythonize

# Cythonize.main(["mpc2c/**.py", "-3", "--inplace"])


def parse_args():
    parser = argparse.ArgumentParser(description="CLI for running experiments")
    parser.add_argument(
        "--template",
        action="store_true",
        help="Create the initial template from `pianoteq_scales.mp3` and `scales.mid`"
    )
    parser.add_argument(
        "--scale",
        action="store_true",
        help="Create the midi file that must be synthesized for creating the template."
    )
    parser.add_argument(
        "--datasets",
        action="store_true",
        help="Create the datasets using NMF."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.template:
        from mpc2c import make_template
        make_template.main()
    if args.scale:
        from mpc2c import create_midi_scale
        create_midi_scale.main()
    if args.datasets:
        from mpc2c import nmf
        import pickle
        nmf_params = pickle.load(open(s.TEMPLATE_PATH, 'rb'))
        nmf.create_datasets(nmf_params, s.MINI_SPEC_PATH, s.DIFF_SPEC_PATH)


if __name__ == "__main__":
    main()

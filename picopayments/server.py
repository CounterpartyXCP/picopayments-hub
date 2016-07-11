from . import cli


def start(args):
    print("start", cli.parse(args))

    # TODO create / migrate datbase if needed

#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argcomplete, argparse
import logging

import thinbox.thinbox as thb

from thinbox.parser import get_parser, USE_ARGCOMPLETE
from thinbox.utils import is_virt_enabled


def main():
    if not is_virt_enabled():
        print("Virtualization not enabled")
        exit(1)
    parser = get_parser()
    if USE_ARGCOMPLETE:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not args.command:
        parser.print_help()
        parser.error("Please specify a command")

    # set not read only
    if args.command == "pull":
        tb = thb.Thinbox()
        if args.pull_parser == "tag":
            tb.pull_tag(args.name, skip=args.skip_check)
        elif args.pull_parser == "url":
            tb.pull_url(args.name, skip=args.skip_check)
    elif args.command == "image":
        tb = thb.Thinbox()
        if args.image_parser in ("list", "ls"):
            tb.image_list()
        elif args.image_parser in ("remove", "rm"):
            if args.all:
                tb.image_remove_all()
            else:
                tb.image_remove(args.name)
        else:
            tb.image_list()
    elif args.command == "create":
        tb = thb.Thinbox(readonly=False)
        if args.image:
            tb.create_from_image(args.image, args.name)
    elif args.command == "copy":
        tb = thb.Thinbox()
        tb.copy(args.file, args.name, args.dir, args.pre, args.comm)
    elif args.command == "enter":
        tb = thb.Thinbox(readonly=False)
        tb.enter(args.name)
    elif args.command == "remove":
        tb = thb.Thinbox(readonly=False)
        tb.remove(args.name)
    elif args.command == "start":
        tb = thb.Thinbox(readonly=False)
        tb.start(args.name)
    elif args.command == "stop":
        tb = thb.Thinbox(readonly=False)
        if args.force:
            tb.stop(args.name, "--mode=acpi")
        tb.stop(args.name)
    elif args.command == "list" or args.command == "ls":
        tb = thb.Thinbox()
        if args.all:
            tb.list()
        elif args.other:
            tb.list(fil="other")
        elif args.paused:
            tb.list(fil="paused")
        elif args.running:
            tb.list(fil="running")
        elif args.stopped:
            tb.list(fil="stopped")
        else:
            tb.list()
    elif args.command == "remove" or args.command == "rm":
        tb = thb.Thinbox(readonly=False)
        if args.all:
            tb.remove_all()
        else:
            tb.remove(args.name)
    elif args.command == "vm":
        tb = thb.Thinbox()
        if args.vm_parser == "list" or args.vm_parser == "ls":
            if args.all:
                tb.list()
            elif args.other:
                tb.list(fil="other")
            elif args.paused:
                tb.list(fil="paused")
            elif args.running:
                tb.list(fil="running")
            elif args.stopped:
                tb.list(fil="stopped")
            else:
                tb.list()
        elif args.vm_parser == "remove" or args.vm_parser == "rm":
            if args.all:
                tb.remove_all()
            else:
                tb.remove(args.name)
        else:
            tb.list()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as ex:
        print("Error:", ex, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

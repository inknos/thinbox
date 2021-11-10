#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK

import argparse

import thinbox.thinbox as thb


from argcomplete.completers import ChoicesCompleter
from thinbox.config import RHEL_TAGS
from thinbox.utils import is_virt_enabled

try:
    import argcomplete
    USE_ARGCOMPLETE = True
except ImportError:
    USE_ARGCOMPLETE = False

def get_parser():
    """
    Returns a parser with this structure
    thinbox create
               |
               +-- -i/--image <image> <vm_name> [autocomplete]
               x-- -t/--tag   <image> <vm_name>
               x-- -u/--url   <url>   <vm_name>

    thinbox pull
             |
             +-- tag <tag> [autocomplete]
             |    |
             +-- url <url>
                  |
                  +-- --skip-check

    thinbox image
              |
              +-- list/ls
              +-- remove/rm <image> [autocomplete]
                        |
                        +-- -a

    thinbox copy <files> <vm_name>
             |
             +-- -c/--command   <command to exec before>
             +-- -d/--dir       <destination dir>
             +-- -p/--pre       <command to exec after>

    thinbox
        |
        +-- list/ls -----------------|
        |       |                    |
        |       +-- -a/--all         |
        |       +-- -o/--other       |
        |       +-- -p/--paused      |
        |       +-- -r/--running     |
        |       +-- -s/--stopped     |
        +-- remove/rm <vm_name> --------| [autocomplete]
                  |                  |  |
                  +-- -a ------------------|
                                     |  |  |
    thinbox vm                       |  |  |
           |                         |  |  |
           +-- list/ls --------------|  |  |
           |    +-- -a/--all            |  |
           |    +-- -o/--other          |  |
           |    +-- -p/--paused         |  |
           |    +-- -r/--running        |  |
           |    +-- -s/--stopped        |  |
           +-- remove/rm <vm_name> -----|  | [autocomplete]
                     |                     |
                     +-- -a ---------------|

    thinbox enter <vm_name> [autocomplete]
    thinbox start <vm_name> [autocomplete]
    thinbox stop  <vm_name> [autocomplete]
    """

    tb = thb.Thinbox()

    parser = argparse.ArgumentParser(  # usage="%(prog)s <command> [opts] [args]",
        description="Thinbox is a tool for..",
        formatter_class=Formatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
    )

    pull_parser = subparsers.add_parser(
        "pull",
        help="pull base image from TAG or URL"
    )
    pull_subparser = pull_parser.add_subparsers(
        dest="pull_parser",
        required=True
    )
    pull_tag_parser = pull_subparser.add_parser(
        "tag",
        help="Pull from TAG"
    )
    pull_tag_parser_gr = pull_tag_parser.add_argument_group()
    pull_tag_parser_gr.add_argument(
        "name",
        choices=list(RHEL_TAGS),
        help="TAG to download"
    )
    pull_tag_parser_gr.add_argument(
        "-s", "--skip-check",
        action="store_const",
        const=True,
        help="skip hash check"
    )
    pull_url_parser = pull_subparser.add_parser(
        "url",
        help="Pull from URL"
    )
    pull_url_parser_gr = pull_url_parser.add_argument_group()
    pull_url_parser_gr.add_argument(
        "name",
        help="URL to download"
    )
    pull_url_parser_gr.add_argument(
        "-s", "--skip-check",
        action="store_const",
        const=True,
        help="skip hash check"
    )

    # create
    create_parser = subparsers.add_parser(
        "create",
        help="create VM from base image",
    )
    create_parser.add_argument(
        "name",
        help="name of the VM"
    )
    create_parser_mg = create_parser.add_mutually_exclusive_group(
        required=True)
    create_parser_mg.add_argument(
        "-i", "--image",
        choices=tb.base_images,
        help="Name of image already downloaded"
    )
    create_parser_mg.add_argument(
        "-p", "--path",
        help="Path of image you want to create a vm from"
    )
    create_parser_mg.add_argument(
        "-t", "--tag",
        help="TAG of the image you want to pull"
    )
    create_parser_mg.add_argument(
        "-u", "--url",
        help="URL of the image you want to pull"
    )
    # copy
    copy_parser = subparsers.add_parser(
        "copy",
        aliases=["cp"],
        help="copy files into specified VM"
    )
    copy_parser.add_argument(
        "file",
        nargs="+",
        help="file or files to copy"
    )
    copy_parser.add_argument(
        "name",
        help="name of the VM"
    )
    copy_parser_mg = copy_parser.add_argument_group()
    copy_parser_mg.add_argument(
        "-c",
        "--comm",
        help="command to execute after the copy"
    )
    copy_parser_mg.add_argument(
        "-d",
        "--dir",
        help="destination dirpath of copy"
    )
    copy_parser_mg.add_argument(
        "-p",
        "--pre",
        help="command to execute before the copy"
    )

    # list
    list_parser = subparsers.add_parser(
        "list",
        aliases=['ls'],
        help="list available VMs"
    )
    list_parser_mg = list_parser.add_mutually_exclusive_group(required=False)
    list_parser_mg.add_argument(
        "-a", "--all",
        action="store_const",
        const=True,
        help="List all VMs"
    )
    list_parser_mg.add_argument(
        "-o", "--other",
        action="store_const",
        const=True,
        help="List all other VMs"
    )
    list_parser_mg.add_argument(
        "-p", "--paused",
        action="store_const",
        const=True,
        help="List all paused VMs"
    )
    list_parser_mg.add_argument(
        "-r", "--running",
        action="store_const",
        const=True,
        help="List all running VMs"
    )
    list_parser_mg.add_argument(
        "-s", "--stopped",
        action="store_const",
        const=True,
        help="List all stopped VMs"
    )
    # remove
    remove_parser = subparsers.add_parser(
        "remove",
        aliases=['rm'],
        help="remove VM"
    )
    remove_parser_mg = remove_parser.add_mutually_exclusive_group(
        required=True)
    remove_parser_mg.add_argument(
        "-a", "--all",
        action='store_const',
        const=True,
        help="Remove all VMs"
    )
    remove_parser_mg.add_argument(
        "name",
        nargs="?",
        help="Remove a VM of name"
    )
    # image
    image_parser = subparsers.add_parser(
        "image",
        aliases=['img'],
        help="manage base images"
    )
    image_subparser = image_parser.add_subparsers(
        dest="image_parser"
    )
    image_list_parser = image_subparser.add_parser(
        "list",
        aliases=["ls"],
        help="Image list"
    )
    image_remove_parser = image_subparser.add_parser(
        "remove",
        aliases=["rm"],
        help="Remove image"
    )
    image_remove_parser_mg = image_remove_parser.add_mutually_exclusive_group(
        required=True)
    image_remove_parser_mg.add_argument(
        "-a", "--all",
        action='store_const',
        const=True,
        help="Remove all VMs"
    )
    image_remove_parser_mg.add_argument(
        "name",
        nargs="?",
        help="Remove a VM of name"
    )
    # vm
    vm_parser = subparsers.add_parser(
        "vm",
        help="manage VMs"
    )
    vm_subparser = vm_parser.add_subparsers(
        dest="vm_parser"
    )
    vm_list_parser = vm_subparser.add_parser(
        "list",
        aliases=["ls"],
        help="VM list "
    )
    vm_list_parser_mg = vm_list_parser.add_mutually_exclusive_group(
        required=False)
    vm_list_parser_mg.add_argument(
        "-a", "--all",
        action="store_const",
        const=True,
        help="List all VMs"
    )
    vm_list_parser_mg.add_argument(
        "-o", "--other",
        action="store_const",
        const=True,
        help="List all other VMs"
    )
    vm_list_parser_mg.add_argument(
        "-p", "--paused",
        action="store_const",
        const=True,
        help="List all paused VMs"
    )
    vm_list_parser_mg.add_argument(
        "-r", "--running",
        action="store_const",
        const=True,
        help="List all running VMs"
    )
    vm_list_parser_mg.add_argument(
        "-s", "--stopped",
        action="store_const",
        const=True,
        help="List all stopped VMs"
    )
    vm_remove_parser = vm_subparser.add_parser(
        "remove",
        aliases=['rm'],
        help="remove VM"
    )
    vm_remove_parser_mg = vm_remove_parser.add_mutually_exclusive_group(
        required=True)
    vm_remove_parser_mg.add_argument(
        "-a", "--all",
        action='store_const',
        const=True,
        help="Remove all VMs"
    )
    vm_remove_parser_mg.add_argument(
        "name",
        nargs="?",
        help="Remove a VM of name"
    )
    # enter
    enter_parser = subparsers.add_parser(
        "enter",
        help="enter VM"
    )
    enter_parser.add_argument(
        "name",
        help="name of the VM to enter",
        choices=[ d.name for d in tb.doms ]
    )
    # start
    start_parser = subparsers.add_parser(
        "start",
        help="start VM"
    )
    start_parser.add_argument(
        "name",
        choices=[ d.name for d in tb.doms ],
        help="name of the VM to start"
    )
    # stop
    stop_parser = subparsers.add_parser(
        "stop",
        help="stop VM"
    )
    stop_parser.add_argument(
        "name",
        choices=[ d.name for d in tb.doms ],
        help="name of the VM to stop"
    )
    stop_parser_mg = stop_parser.add_mutually_exclusive_group(required=False)
    stop_parser_mg.add_argument(
        "-f", "--force",
        help="Force shuotdown of domain with sending ACPI"
    )

    return parser


class Formatter(argparse.HelpFormatter):
    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            parts = []
            for i in action._get_subactions():
                parts.append("%*s%-21s %s" %
                             (self._current_indent, "", i.metavar, i.help))
            return "\n".join(parts)
        return super(Formatter, self)._format_action(action)


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
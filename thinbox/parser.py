import argparse

import thinbox as thb

from thinbox.config import IMAGE_TAGS

try:
    import argcomplete
    USE_ARGCOMPLETE = True
except ImportError:
    USE_ARGCOMPLETE = False


class Formatter(argparse.HelpFormatter):
    """Returns formatter
    """

    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            parts = []
            for i in action._get_subactions():
                parts.append("%*s%-21s %s" %
                             (self._current_indent, "", i.metavar, i.help))
            return "\n".join(parts)
        return super(Formatter, self)._format_action(action)


def get_parser():
    """
    Returns parser
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
    # parser.add_argument(
    #     "-c",
    #     "--config",
    #     help="config file"
    # )

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
        metavar="TAG",
        choices=IMAGE_TAGS,  # _get_rhel_tags(),
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
        "image",
        metavar="IMG_NAME",
        choices=tb.base_images,
        help="Name of image already downloaded"
    )
    create_parser.add_argument(
        "name",
        help="name of the VM"
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
        "dest",
        help="destination"
    )
    # run
    run_parser = subparsers.add_parser(
        "run",
        help="run command into specified VM"
    )
    run_parser.add_argument(
        "cmd",
        help="command to run"
    )
    run_parser.add_argument(
        "name",
        choices=[d.name for d in tb.doms],
        metavar="VM_NAME",
        help="name of VM"
    )
    # env
    env_parser = subparsers.add_parser(
        "env",
        help="print env"
    )
    env_parser.add_argument(
        "var",
        nargs='?',
        help="var"
    )
    env_parser.add_argument(
        "val",
        nargs='?',
        help="value"
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
        choices=[d.name for d in tb.doms],
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
        choices=tb.base_images,
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
        choices=[d.name for d in tb.doms],
        help="Remove a VM of name"
    )
    # enter
    enter_parser = subparsers.add_parser(
        "enter",
        help="enter VM"
    )
    enter_parser.add_argument(
        "name",
        metavar="VM_NAME",
        choices=[d.name for d in tb.doms],
        help="name of the VM to enter"
    )
    # start
    start_parser = subparsers.add_parser(
        "start",
        help="start VM"
    )
    start_parser.add_argument(
        "name",
        metavar="VM_NAME",
        choices=[d.name for d in tb.doms],
        help="name of the VM to start"
    )
    # stop
    stop_parser = subparsers.add_parser(
        "stop",
        help="stop VM"
    )
    stop_parser.add_argument(
        "name",
        metavar="VM_NAME",
        choices=[d.name for d in tb.doms],
        help="name of the VM to stop"
    )
    stop_parser_mg = stop_parser.add_mutually_exclusive_group(required=False)
    stop_parser_mg.add_argument(
        "-f", "--force",
        help="Force shuotdown of domain with sending ACPI"
    )

    return parser

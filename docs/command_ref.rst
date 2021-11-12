.. _command_ref-label:

##########################
 Thinbox Command Reference
##########################

========
Synopsis
========

``thinbox [-hv] [-c CONFIG] command [OPTIONS]``

===========
Description
===========

.. _command_provides-label:

``thinbox`` is a command line tool in ``python3`` to manage virtualmachines build using ``qemu``.

``thinbox`` aims to create a simple environment where store images, create domains and manage them all within one tool.

.. _exit_codes-label:

Return values:

* ``0``  : Operation was successful.
* ``1``  : An error occurred.
* ``2``  : Command line parsong error occurred.

Available commands:

* :ref:`copy <copy_command-label>`
* :ref:`create <create_command-label>`
* :ref:`env <env_command-label>`
* :ref:`enter <enter_command-label>`
* :ref:`image <image_command-label>`
* :ref:`list <list_command-label>`
* :ref:`pull <pull_command-label>`
* :ref:`remove <remove_command-label>`
* :ref:`run <run_command-label>`
* :ref:`start <start_command-label>`
* :ref:`stop <stop_command-label>`
* :ref:`vm <vm_command-label>`

=======
Options
=======

.. _verbose_option-label:

``-v, --verbose``
    Turn on verbose mode. Uses ``python`` moddule ``logging``.

.. _config_option-label:

``-c <file>, --config=<file>``
    Use a different config file than the default one.



========
Commands
========

.. _copy_command-label:

------------
Copy Command
------------

| Command: ``copy``
| Aliases: ``cp``

``thinbox copy FILE [FILES..] DESTINATION``

.. _create_command-label:

--------------
Create Command
--------------

| Command: ``create``

``thinbox create IMAGE VM_NAME``

.. _env_command-label:

-----------
Env Command
-----------

| Command: ``env``

``thinbox env KEY VALUE``

Allows the user to get and set a list of the environment variables that thinbox can use.

.. _env_command_examples-label:

Env Examples
------------

``thinbox env``

.. code-block:: bash

    {
        ...
        "IMAGE_TAGS": [
            "fedora-cloud-34",
            "fedora-cloud-35",
            "rhel8-latest"
        ],
        ...
    }

``thinbox env IMAGE_TAGS``

``thinbox env THINBOX_BASE_DIR ~/Documents/thinbox/mybase``

.. _enter_command-label:

-------------
Enter Command
-------------

| Command: ``enter``

``thinbox enter VM_NAME``

.. _image_command-label:

-------------
Image Command
-------------

| Command: ``image``

``thinbox image [SUBCOMMAND] [OPTIONS]``

.. _list_command-label:

------------
List Command
------------

| Command: ``list``
| Aliases: ``ls``

``thinbox list``

``thinbox ls``

.. _pull_command-label:

------------
Pull Command
------------

| Command: ``pull``


``thinbox pull tag IMAGE_TAG [-s/--skip-check]``

``thinbox pull url IMAGE_URL [-s/--skip-check]``

.. _remove_command-label:

--------------
Remove Command
--------------

| Command: ``remove``
| Aliases: ``rm``

``thinbox remove VM_NAME``

.. _run_command-label:

-----------
Run Command
-----------

| Command: ``run``

.. _start_command-label:

-------------
Start Command
-------------

| Command: ``start``

``thinbox run VM_NAME``

.. _stop_command-label:

------------
Stop Command
------------

| Command: ``stop``

``thinbox stop VM_NAME``

.. _vm_command-label:

----------
VM Command
----------

| Command: ``vm``

``thinbox vm [SUBCOMMAND] [OPTIONS]``

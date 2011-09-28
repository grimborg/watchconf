Watchconf is a simple tool to  quickly audit the configurations of a collection of servers, namely:

* Have a list of all config files that must be present in the servers.
* Check these in all servers, and make sure that they are all equal, and if they are different, see why they are different and whether that's what we want.

This tool displays, for each configuration file:

* Which servers have it and which don't (servers that don't have the file will appear in italics.)
* The servers that do have the file, will be grouped so that servers with identical file contents are together.
* For each group of servers, you'll see a diff of the file against the same file in the previous group of servers.
* Files that are equal in all servers will appear in italics.

The app is in a single file. To get it running either download the ``watchconf.py`` or install it with ``pip install watchconf``.

Here's how to use it::

    watchconf -f FILES -s SERVERS [-p PORT] [-u|--username USERNAME] [-d|--debug]

    Starts an HTTP server that shows the differences between the specified files in the specified servers.

    options:

     -f --files     Files to compare
     -s --servers   Servers to compare
     -p --port      Port to listen to (default: 5000)
     -u --username  ssh username (default: use the current user)
     -d --debug     Debug mode
     -h --help      display help

For example::

    watchconf -s server1,server2 -f file1,file2


Watchconf expects a memcache daemon listening to the default port on localhost.

.. image:: https://github.com/grimborg/watchconf/raw/master/watchconf.png

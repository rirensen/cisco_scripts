======
Condor
======

Condor is a python module providing the connection method to IOS XR based
devices. It supports keyring for password management and multiple jump hosts.

------------
Installation
------------

The module can be installed using::

    python setup.py install

The required packages will be installed automatically.

Required packages
=================

* pexpect
* keyring (optional)


Settings file
=============

If ``keyring`` module is installed instead of providing clear text passwords
in the urls password can be automatically retrieved from the system keyring.
See details:

    https://pypi.python.org/pypi/keyring

The keyring configuration file consists of host group category and username
used for this host or group (see below).

The example accounts.cfg file::

    [DEFAULT]
    username = cisco

    [localhost]
    username = johndoe

Above configuration means that default username is `john` and the password
for this user will be retrieved from keychain if missing in url.
For localhost the username ``johndoe`` can be used.

For the host grouping the wildcards can be used::

    [192.168.1.*]
    username = johndoe1

    [*.cisco.com]
    username = johndoe2



--------
Examples
--------

The example usage in the code::

    urls = ['ssh://user:pass@jumphost', 'telnet://user:pass@terminalserver:2040']

    try:
        with connections.ConnectionAgent(
                connections.Connection(
                        'ASR9K', urls)) as conn:

            try:
                output = conn.send(command)
                print output

            except CommandSyntaxError:
                print "Unknown command error"

    except ConnectionAuthenticationError as e:
        print "Authentication error: %s" % e
    except ConnectionTimeoutError as e:
        print "Connection timeout: %s" % e
    except ConnectionError as e:
        print "Connection error: %s" % e
    except GeneralError as e:
        print "Error: %s" % e


See the details in ``example.py`` file::


    ./example.py -h

    Usage: example.py -H url [-J url] [-d <level>] [-l <filename>] [-h] command
    Copyright (C) 2014 by Klaudiusz Staniek

    Options:
      -h, --help            show this help message and exit
      -H URL, --host_url=URL
                            target host url e.g.: telnet://user:pass@hostname
      -J URL, --jumphost_url=URL
                            jump host url e.g.: ssh://user:pass@jumphostname
      -d LEVEL, --debug=LEVEL
                            prints out debug information about the device
                            connection stage. LEVEL is a string of DEBUG, INFO,
                            WARNING, ERROR, CRITICAL. Default is CRITICAL.
      -l FILE, --log=FILE   file name path for device session log.


    python example.py -H telnet://john@172.28.98.6 -J ssh://johndoe@localhost --debug=DEBUG show running
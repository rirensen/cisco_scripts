#!/usr/bin/env python
# =============================================================================
# driver_test.py
#
# Copyright (c)  2014, Cisco Systems
# All rights reserved.
#
# # Author: Klaudiusz Staniek
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
# =============================================================================

import getpass
import optparse
import sys

import logging

logging.basicConfig(
        format='%(asctime)-15s %(levelname)8s: %(message)s',
        level=logging.CRITICAL)


import condor

from condor.accountmgr import AccountManager
from condor.exceptions import ConnectionAuthenticationError, \
    ConnectionError, ConnectionTimeoutError, CommandSyntaxError, GeneralError


usage  = '%prog -H url [-J url] [-d <level>] [-l <filename>] [-h] command'
usage += '\nCopyright (C) 2014 by Klaudiusz Staniek'
parser = optparse.OptionParser(usage=usage)

parser.add_option(
    '--host_url', '-H', dest='host_url', metavar='URL',
    help='''
target host url e.g.: telnet://user:pass@hostname
'''.strip())

parser.add_option(
    '--jumphost_url', '-J', dest='jumphost_url', default=None, metavar='URL',
    help='''
jump host url e.g.: ssh://user:pass@jumphostname
'''.strip())

parser.add_option(
    '--debug', '-d', dest='debug', type='str', metavar='LEVEL',
    default='CRITICAL', help='''
prints out debug information about the device connection stage.
LEVEL is a string of DEBUG, INFO, WARNING, ERROR, CRITICAL.
Default is CRITICAL.
'''.strip())


parser.add_option(
        '--log', '-l', dest='session_log', default=None, metavar='FILE',
        help='''
file name path for device session log.
'''.strip())


logging_map = {
    0: 60, 1: 50, 2: 40, 3: 30, 4: 20, 5: 10
}

logging.basicConfig(
    format='%(asctime)-15s %(levelname)8s: %(message)s',
    level=60) #log


def prompt_for_password(prompt):
    print("Password not specified in url.\n"
          "Provided password will be stored in system KeyRing\n")
    return getpass.getpass(prompt)


if __name__ == "__main__":
    options, args = parser.parse_args(sys.argv)

    args.pop(0)

    urls = []

    if options.jumphost_url:
        urls.append(options.jumphost_url)

    host_url = None
    if not options.host_url:
        parser.error('Missing host URL')

    urls.append(options.host_url)


    if len(args) > 0:
        command = " ".join(args)
    else:
        parser.error("Missing command")

    numeric_level = getattr(logging, options.debug.upper(), 50)
    logging.getLogger().setLevel(numeric_level)

    try:
        import keyring
        am = AccountManager(config_file='accounts.cfg',
                        password_cb=prompt_for_password)
    except:
        print("No keyring library installed. Password must "
              "be provided in url.")
        am = None


    try:
        with condor.ConnectionAgent(
                condor.Connection(
                        'host', urls,
                        account_manager=am)) as conn:

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


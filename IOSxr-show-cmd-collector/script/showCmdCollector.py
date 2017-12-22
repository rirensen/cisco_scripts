#!/usr/bin/python

__author__ = "Cedric Dessez"
__copyright__ = "Copyright 2015, Cisco"
__credits__ = ["Cedric Dessez"]
__email__ = "cdessez@cisco.com"
__doc__ = '''
Class Collector: tool to automatically collect show commands from IOS-XR devices at a large scale. It uses SSH or telnet
to connect to the devices.
'''

###########################################################################
###########################################################################
##  __  _____      _    ___          _          _ _        _             ##
##  \ \/ / _ \  __| |_ / __|_ __  __| |  __ ___| | |___ __| |_ ___ _ _   ##
##   >  <|   / (_-< ' \ (__| '  \/ _` | / _/ _ \ | / -_) _|  _/ _ \ '_|  ##
##  /_/\_\_|_\ /__/_||_\___|_|_|_\__,_| \__\___/_|_\___\__|\__\___/_|    ##
##                                                                       ##
##   Tool to automatically collect show commands from IOS-XR routers     ##
##             Written by Cedric Dessez (cdessez@cisco.com)              ##
##                                                                       ##
###########################################################################
###########################################################################

import logging
import os
import sys
import argparse
import getpass
import datetime
import condor
import urllib

from condor.accountmgr import AccountManager, make_realm
from condor.exceptions import ConnectionAuthenticationError, ConnectionError, ConnectionTimeoutError, \
    CommandSyntaxError, GeneralError


logger = logging.getLogger(__name__)


DEFAULT_OUTPUT_TEMPLATE = \
"""=============================================================
== Device: {device}
== Command: {command}
== Timestamp: {time}
=============================================================
{output}
"""


def str_sanitize(s, keepcharacters=(' -_')):
    """
    Remove characters that are not alphanumerical or in keepcharacters
    :param s: the string to sanitize
    :keepcharacters: characters to keep
    :return: the resulting string
    """
    return "".join(c for c in s if c.isalnum() or c in keepcharacters).strip().replace(' ','_')



class Collector(object):

    def __init__(self, args):
        """
        Constructor
        """
        self.args = args

        # Set logging
        if self.args.log_level == 'debug':
            logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                        format="[%(levelname)8s][%(asctime)s]:%(name)s:%(funcName)s(){l.%(lineno)d}:  %(message)s")
        else:
            if self.args.log_level == 'info':
                level = logging.INFO
            elif self.args.log_level == 'error':
                level = logging.ERROR
            else:
                level = logging.CRITICAL
            logging.basicConfig(stream=sys.stderr, level=level,
                                format="[%(levelname)8s][%(asctime)s]:  %(message)s")
        logging.getLogger('condor').setLevel(logging.CRITICAL)

        # Parses init commands
        if self.args.init_cmd_files:
            logger.info("Parsing the init command files")
            items = Collector._get_not_empty_lines([self.args.init_cmd_files])
            self.init_commands = [cmd for group, lines in items for cmd in lines]
        else:
            self.init_commands = ['terminal length 0']

        # Parses the commands to collect
        logger.info("Parsing the command files")
        self.commands = Collector._get_not_empty_lines(self.args.command_files)

        logger.info("Reading hostfiles")
        self._parse_hosts(self.args.host_files)

        # Handles credentials
        self.username = self.args.username
        self.accounts_file = self.args.accounts_file
        if not (self.username or self.accounts_file):
            logger.critical("No username or accounts file provided")
            sys.exit(0)
        self.password = self.args.password
        if self.username and not self.password:
            self.password = getpass.getpass()

        # Creates output directory if does not exist
        self.output_dir = self.args.output_dir
        if not os.path.exists(self.output_dir):
            logger.debug("Creating output directory")
            os.makedirs(os.path.realpath(self.output_dir))
        if not os.path.isdir(self.output_dir):
            logger.critical("No such directory: '{0}'".format(self.output_dir))
            raise IOError

        self.filename_format = self.args.filename_format
        self.output_prefix = self.args.output_prefix
        self.output_suffix = self.args.output_suffix

        # Read the output template if specified
        if self.args.output_template:
            if not os.path.exists(self.args.output_template) or not os.path.isfile(self.args.output_template):
                logger.error("Cannot use the specified output template file, the default format will be used")
                self.output_template = DEFAULT_OUTPUT_TEMPLATE
            else:
                with open(self.args.output_template) as f:
                    self.output_template = f.read()
        else:
            self.output_template = DEFAULT_OUTPUT_TEMPLATE


    def execute(self):
        """
        Executes the collection
        """
        try:
            am = AccountManager(config_file=self.accounts_file)
        except:
            am = None
        url_prefix = 'ssh://'
        if self.username:
            url_prefix += urllib.quote(self.username)
            if self.password:
                url_prefix += ':{}'.format(urllib.quote(self.username))
            url_prefix += '@'

        for hostname, display_name in self.hosts:

            # Connection to one device
            try:
                with condor.ConnectionAgent(
                        condor.Connection(
                                display_name, ["{}{}".format(url_prefix, urllib.quote(hostname))],
                                account_manager=am)) as conn:

                    logger.info("Connected to {}".format(display_name))

                    # init commands
                    for command in self.init_commands:
                        try:
                            logger.debug("Executing init command from {}: {}".format(display_name, command))
                            output = conn.send(command)

                        except CommandSyntaxError:
                            logger.error("Unknown command error on {}: {}".format(display_name, command))

                    # commands to collect
                    for command_group, commands in self.commands:
                        for command in commands:
                            try:
                                logger.debug("Collecting command from {}: {}".format(display_name, command))
                                output = conn.send(command)
                                self._save_output_file(command_group, display_name, command, output)

                            except CommandSyntaxError:
                                logger.error("Unknown command error on {}: {}".format(display_name, command))

                    logger.info("Done collecting commands, logging out of {}".format(display_name))

            except ConnectionAuthenticationError as e:
                logger.error("Authentication error on {}: {}".format(display_name, e))
            except ConnectionTimeoutError as e:
                logger.error("Connection timeout on {}: {}".format(display_name, e))
            except ConnectionError as e:
                logger.error("Connection error on {}: {}".format(display_name, e))
            except GeneralError as e:
                logger.error("Error on {}: {}".format(display_name, e))


    def _save_output_file(self, cmd_set, device_name, command, output):
        """
        Saves the output in a file
        :param cmd_set:
        :param device_name:
        :param command:
        :param output:
        """
        cmd_id = str_sanitize(command)
        cmd_id = cmd_id[:min(30,len(cmd_id))]
        file_name = self.filename_format.format(
                            prefix=         self.output_prefix,
                            cmd_file_name=  cmd_set,
                            device_name=    str_sanitize(device_name),
                            command=        cmd_id,
                            suffix=         self.output_suffix)
        path = os.path.join(self.output_dir, file_name)
        content = self.output_template.format(
                            device=         device_name,
                            cmd_file_name=  cmd_set,
                            command=        command,
                            time=           str(datetime.datetime.now()),
                            output=         output)
        with open(path, 'a') as f:
            f.write(content)


    @staticmethod
    def _get_not_empty_lines(files, comment_char='!'):
        """
        Reads files to list all the non-empty lines to run
        :param files: a list of files and directory names
        :return: a list of couples (filename, list of strings)
        """
        # list all the files (unfolds directories)
        all_files = []
        for fname in files:
            if os.path.exists(fname):
                if os.path.isfile(fname):
                    all_files.append(fname)
                else:
                    for f in os.listdir(fname):
                        path = os.path.join(fname,f)
                        if os.path.isfile(path):
                            all_files.append(path)
            else:
                logger.error("Invalid path: {}".format(fname))

        # retrieves the lines
        res = []
        for path in all_files:
            lines = []
            with open(path) as f:
                logger.debug("Reading file {}".format(path))
                for line in f.readlines():
                    line = line.strip()
                    if not line or line[0] == comment_char:
                        continue
                    lines.append(line)
            fname = os.path.basename(path)
            res.append((str_sanitize(fname[:-4] if fname[-4:] == '.txt' else fname),lines))

        return res


    def _parse_hosts(self, files):
        """
        Parse the host files
        :param files: a list of files
        :return:
        """
        self.hosts = []

        hostfiles = Collector._get_not_empty_lines(files, comment_char='#')
        for lines in [f[1] for f in hostfiles]:
            for line in lines:
                if ' ' in line or '\t' in line:
                    hostname, display_name = line.split(None, 1)
                else:
                    hostname = display_name = line
                self.hosts.append((hostname, display_name))


    @staticmethod
    def _get_arg_parser():
        """
        Creates the parser object
        :return: an argparse parser object
        """
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                         description="Tool to automatically collect show commands from IOS-XR devices "
                                                     "\nat a large scale. It uses SSH to connect to the "
                                                     "devices.")
        parser.add_argument('--host-files', required=True, nargs="*", metavar="HOSTFILE",
                            help="List of files where the hosts are stored"
                                 "\nEach line must contain the hostname and an optional display name"
                                 "\nThey must be separated by spaces or tabulations"
                                 "\nEmpty lines or line beginning with the # character will be ignored")
        parser.add_argument('--command-files', required=True, nargs='*', metavar='CMDFILE',
                            help="List of files or directory where the commands to collect are enumerated."
                                 "\nIf a directory is given, all the files it contains will be add to the list."
                                 "\nThe files must contain one command per line. Lines beginning with '!' or "
                                 "\nempty will be ignored")
        parser.add_argument('--output-dir', required=True, metavar='DIRECTORY',
                            help="Path to the directory where the output files should be saved"
                                 "\nWill try to create it if it does not already exist")
        parser.add_argument('--accounts-file', required=False, metavar='ACCOUNTFILE',
                            help="File where the associations hostname to username are defined")
        parser.add_argument('--username', required=False, metavar='USERNAME',
                            help="If given, ignores the account-file and use this username")
        parser.add_argument('--password', required=False, metavar='PASSWD',
                            help="Unique password for the SSH connections"
                                 "\nIf not specified, the password will be prompted on the CLI"
                                 "\nAlthough not recommended, this option can be useful if not in an interactive"
                                 "\nconsole")
        parser.add_argument('--init-cmd-files', required=False, metavar='CMDFILE',
                            help="File that contains initial commands to be issued to prepare the collection"
                                 "\nafter the script gets a prompt."
                                 "\nBy default, the only command is 'terminal length 0' (overridden if a file is"
                                 "\nspecified).")
        parser.add_argument('--filename-format', required=False, metavar='FORMAT',
                            default="{prefix}{cmd_file_name}__{device_name}__{command}{suffix}",
                            help="Format of the name of output files."
                                 "\nDefault value: '{prefix}{cmd_file_name}__{device_name}__{command}{suffix}'"
                                 "\nThis default value entails one file per command."
                                 "\nOther example: '{cmd_file_name}-{device_name}{suffix}' results in one output"
                                 "\nfile per input command file")
        parser.add_argument('--output-template', required=False, metavar='FILE',
                            help="File to specify the template used to print the output of a command"
                                 "\nSee output_template_example.txt for an example"
                                 "\nIf not specified, use a default template with a header that includes the "
                                 "\ndevice name, the command and a timestamp")
        parser.add_argument('--output-prefix', required=False, metavar='PREFIX', default='',
                            help="Prefix to be prepended to the name of output file(s)")
        parser.add_argument('--output-suffix', required=False, metavar='SUFFIX', default='.txt',
                            help="Suffix to be appended to the name of output file(s)"
                                 "\n(can be used to set the extension of output files)"
                                 "\nIf not specified, it defaults to '.txt'")
        parser.add_argument('--log-level', choices=['debug', 'info', 'error', 'critical'], default='error')
        return parser


    @staticmethod
    def cli():
        args = Collector._get_arg_parser().parse_args()
        collector = Collector(args)
        collector.execute()



if __name__ == "__main__":
    Collector.cli()

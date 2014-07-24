#!/usr/bin/python
#
# Wrapper for mspdebug that runs an MSP430 program to a breakpoint, then dumps
# its output to a file or stderr.
#
# TODO: support more than tilib
#

import argparse
import logging
import os, os.path
import select
import signal
import subprocess
import sys
import time

DOTFILE = '.mspdebug'

logger = logging.getLogger(__name__)
logger.propagate = False

def parse_args ():
    parser = argparse.ArgumentParser(description='mspdebug wrapper')
    parser.add_argument('executable', help='msp430 executable')
    parser.add_argument('-s', '--simulator', action='store_true',
            help='use simulator')
    parser.add_argument('-H', '--host-ssh', type=str,
            default='host to connect to via ssh')
    parser.add_argument('-m', '--mspdebug', type=str, default='mspdebug',
            help='how to invoke mspdebug (default \'mspdebug\')')
    parser.add_argument('-c', '--command', type=str, default='tilib',
            help='mspdebug command (default \'tilib\')')
    parser.add_argument('-b', '--breakpoint', default='0xffff',
            help='breakpoint that means program is done (default 0xffff)')
    parser.add_argument('-L', '--library-path',
            help='directory that contains libmsp430.so')
    parser.add_argument('-d', '--debug', action='store_true',
            help='show debugging output')
    parser.add_argument('-o', '--outfile', type=argparse.FileType('w'),
            metavar='FILE', default=sys.stderr,
            help='dump registers on completion')
    parser.add_argument('-T', '--timing-file', type=argparse.FileType('w'),
            metavar='FILE', help='dump runtime on completion')
    return parser.parse_args()

def write_dotfile (args):
    executable = args.executable
    if args.host_ssh:
        executable = os.path.basename(executable)
    cmds = (
            'sym import {}'.format(executable),
            'prog {}'.format(executable),
            'delbreak', # clear all breakpoints
            'setbreak {}'.format(args.breakpoint),
            'run'
           )
    with open(DOTFILE, 'w') as dotfile:
        dotfile.write('\n'.join(cmds))
        dotfile.write('\n')
    if args.host_ssh:
        scpcmd = ['scp', DOTFILE, args.host_ssh + ':']
        logger.debug('Calling {}'.format(' '.join(scpcmd)))
        rc = subprocess.call(scpcmd)
        return (rc == 0)

def run_mspdebug (args):
    outputfile = args.outfile and args.outfile or sys.stderr

    if args.simulator:
        cmd = '{} sim'.format(args.mspdebug)
    else:
        cmd = '{} tilib'.format(args.mspdebug)
    if args.host_ssh:
        cmd = 'ssh {} {}'.format(args.host_ssh, cmd)

        # copy the executable to the remote host
        scpcmd = ['scp', args.executable, args.host_ssh + ':']
        logger.debug('Calling {}'.format(' '.join(scpcmd)))
        rc = subprocess.call(scpcmd)
        assert rc == 0

    logger.debug('Starting {}'.format(cmd))
    proc = subprocess.Popen(cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    try:
        # read until a breakpoint reached.  catch register values
        polite = True
        bail = False
        while not bail:
            reads = [proc.stdout.fileno(), proc.stderr.fileno()]
            ret = select.select(reads, [], [])
            for fd in ret[0]:
                if fd == proc.stdout.fileno():
                    line = proc.stdout.readline()
                    line = line.strip()
                    logger.debug('stdout: [{}]'.format(line))
                    if line.startswith('( '):
                        outputfile.write('{}\n'.format(line))
                    if line == 'Press Ctrl+D to quit.':
                        logger.debug('Got mspdebug prompt')
                        bail = True
                        break
                elif fd == proc.stderr.fileno():
                    stderr = proc.stderr.readline().strip()
                    logger.error('mspdebug: {}'.format(stderr))
                    polite = False
                    bail = True
                    break

            if proc.poll() != None:
                break
        if polite:
            logger.debug('Exiting mspdebug...')
            proc.stdin.write('exit\n')
    except KeyboardInterrupt:
        logger.critical('caught interrupt; sending SIGINT to mspdebug')
        proc.send_signal(signal.SIGINT)
        time.sleep(0.2)
    finally:
        proc.wait()
        logger.debug('mspdebug process exited cleanly.')

def remove_dotfile (args):
    if args.host_ssh:
        sshcmd = ['ssh', args.host_ssh, 'rm', DOTFILE]
        logger.debug('Calling {}'.format(sshcmd))
        rc = subprocess.call(sshcmd)
    os.unlink(DOTFILE)

if __name__ == '__main__':
    args = parse_args()

    logLevel = (args.debug and logging.DEBUG or logging.INFO)
    logHandler = logging.StreamHandler()
    logFormat = '%(levelname)s: %(message)s'
    logHandler.setFormatter(logging.Formatter(logFormat))
    logger.setLevel(logLevel)
    logger.addHandler(logHandler)

    if args.library_path:
        msplib = os.path.join(args.library_path, 'libmsp430.so')
        if not os.path.exists(msplib):
            logger.warn('{} does not exist'.format(msplib))
        try:
            libpath = os.environ['LD_LIBRARY_PATH'].split(os.pathsep)
        except KeyError:
            libpath = []
        libpath.append(args.library_path)
        os.environ['LD_LIBRARY_PATH'] = os.pathsep.join(libpath)

    write_dotfile(args) or sys.exit(1)
    if args.timing_file:
        starttime = time.time()
    run_mspdebug(args)
    if args.timing_file:
        endtime = time.time() - starttime
        args.timing_file.write('{}\n'.format(endtime))
    remove_dotfile(args)

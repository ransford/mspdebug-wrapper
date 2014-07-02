#!/usr/bin/python

import os
import subprocess

BREAKADDR = 'ffff'
DOTFILE = '.mspdebug'
SIMULATOR = True

def write_dotfile (breakaddr=BREAKADDR):
    cmds = (
            'delbreak', # clear all breakpoints
            'setbreak 0x{}'.format(breakaddr),
            'run'
           )
    with open(DOTFILE, 'w') as dotfile:
        dotfile.write('\n'.join(cmds))
        dotfile.write('\n')

def run_mspdebug ():
    print 'Starting mspdebug'
    proc = subprocess.Popen('mspdebug sim',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    try:
        # read until a breakpoint reached.  catch register values
        while True:
            foo = proc.stdout.readline().strip()
            if foo.startswith('( '):
                print foo
            if foo == 'Press Ctrl+D to quit.':
                print 'Got mspdebug prompt'
                break
    except KeyboardInterrupt:
        pass
    finally:
        print 'Exiting...'
        proc.stdin.write('exit\n')
        proc.wait()
        print 'mspdebug process exited cleanly.'

def remove_dotfile ():
    os.unlink(DOTFILE)

if __name__ == '__main__':
    write_dotfile()
    run_mspdebug()
    remove_dotfile()

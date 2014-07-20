This is an mspdebug wrapper for use in scripts.

Use this wrapper to run a program on an MSP430 attached to your PC (via a
hardware debugger such as the [MSP-FET430UIF][fet]) and gather its results.
Given an executable, the wrapper invokes mspdebug, sets a breakpoint at a
location of your choosing, runs the program, and dumps the register values to a
file when that breakpoint is reached.

### Usage

Invoke with `-h` to see options.  Most crucial is the `-b` option that sets the
breakpoint.  If you have defined a function `stop_here()`, for example, that
will be called when the program is done, you can run

    $ python mspdebug-wrapper.py -b stop_here -o regs.txt myfile.elf

Collect the register values from `regs.txt` after the program runs.

Or you can use the MSP430 version of binutils (see "Dependencies" below) to hunt
for a specific instruction that is called after the program completes.  This
instruction will vary from program to program.  Just one example:

    $ msp430-objdump myfile.elf
    ...
        446c:       81 4f 02 00     mov     r15,    2(r1)   ;0x0002(r1)

    $ python mspdebug_wrapper.py -b 0x446c -o regs.txt myfile.elf

### Dependencies
 * [mspdebug][]
 * `msp430-binutils` or `binutils-msp430` from your system's package manager to
   inspect executables as above

[mspdebug]: http://mspdebug.sourceforge.net/

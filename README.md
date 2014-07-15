This is an mspdebug wrapper for use in scripts.

Use this wrapper to run a program on an MSP430 attached to your PC (via a
hardware debugger) and gather its results.

### Usage

    $ msp430-objdump myfile.elf
    ...
        446c:       81 4f 02 00     mov     r15,    2(r1)   ;0x0002(r1)

    $ python mspdebug_wrapper.py -b 0x446c myfile.elf

### Dependencies
Lots, including:
 * mspdebug
 * A hardware debugger such as the MSP-FET430UIF

#!/bin/bash
simulavr --device atmega328 --cpufrequency 1000000 -c vcd:bcd_timer.traces:bcd_timer.vcd -f bcd_timer.elf -m 4000000000

#!/usr/bin/python

import os
import sys
import string
import datetime
from argparse import ArgumentParser
from optparse import OptionParser


### Global variables ###

# Pathname of simulation output file
s_stim_file_path = ''

# Pathname of VCD file
s_vcd_file_path = ''

# Name of simulator
s_version = 'Atmel Studio 6.1'

# List of all VCD variable names
s_vcd_vars = []

# List of all VCD variable objects
vcd_vars = []

# List of all lines to be printed to VCD file
s_vcd_lines = []

# Interconnect System's Wave program does not work
#   with timescales other than '1'
# Need to multiply base time unit to get true scale
s_timescale = '1 us'
n_time_multiplier = 1

# Elapsed simulation time
n_cur_time = 0


class VCD_Var:

    n_printable_indx = 0

    def __init__(
            self,
            s_ref,
            n_width = 8
            ):

        self.s_id = string.printable[ VCD_Var.n_printable_indx ]
        self.s_ref = s_ref
        self.n_width = n_width
        self.sub_vcd_vars = []
        self.n_prev_value = 0

        VCD_Var.n_printable_indx = VCD_Var.n_printable_indx + 1

        if( self.n_width > 1 ):

            for n_bit_indx in range( n_width ):

                self.sub_vcd_vars.append( VCD_Var(
                        s_ref = ( '%s%d' % ( self.s_ref, n_bit_indx ) ),
                        n_width = 1
                        ) )


    def Get_Var_Lines(
            self
            ):

        s_var_lines = []

        s_var_lines

        s_var_lines.append( '$var reg %(n_width)d %(s_id)s %(s_ref)s $end\n' % {
                "n_width":self.n_width,
                "s_id":self.s_id,
                "s_ref":self.s_ref
                } )

        if( self.n_width > 1 ):

            s_var_lines.append( '$scope module %sbits $end\n' % self.s_ref )
            for sub_vcd_var in self.sub_vcd_vars:
                s_var_lines = s_var_lines + sub_vcd_var.Get_Var_Lines()
            s_var_lines.append( '$upscope $end\n' )

        return s_var_lines


    def Get_Scope_Lines(
            self
            ):

        s_scope_lines = []
        s_scope_lines.append( '$scope begin %s $end\n' % self.s_ref )

        if( self.n_width > 1 ):

            for sub_vcd_var in self.sub_vcd_vars:

                s_scope_lines = s_scope_lines + sub_vcd_var.Get_Scope_Lines()

        return s_scope_lines


    def Get_Var_Dump_Lines(
            self
            ):

        s_dump_lines = []
        s_cur_dump_line = ''
        s_sub_dump_lines = []

        if( self.n_width > 1 ):

            s_cur_dump_line = 'b'

            for n_bit_indx in range( self.n_width ):

                s_cur_dump_line = '%s0' % ( s_cur_dump_line )
                s_sub_dump_lines = s_sub_dump_lines + self.sub_vcd_vars[ n_bit_indx ].Get_Var_Dump_Lines()

            s_cur_dump_line = s_cur_dump_line + ' '

        else:

            s_cur_dump_line = '0'

        s_cur_dump_line = s_cur_dump_line + self.s_id + '\n'
        s_dump_lines.append( s_cur_dump_line )
        s_dump_lines = s_dump_lines + s_sub_dump_lines

        return s_dump_lines


    def Get_Value_Dump_Lines(
            self,
            n_new_value
            ):

        if( n_new_value == self.n_prev_value ):
            return []

        self.n_prev_value = n_new_value

        s_dump_lines = []
        s_cur_dump_line = ''
        s_sub_dump_lines = []
        n_cur_value_rot = n_new_value

        if( self.n_width > 1 ):

            for n_bit_indx in range( self.n_width ):

                n_cur_bit = n_cur_value_rot & 1
                n_cur_value_rot = n_cur_value_rot >> 1

                s_cur_dump_line = '%d%s' % (
                        n_cur_bit,
                        s_cur_dump_line
                        )

                s_sub_dump_lines = s_sub_dump_lines + self.sub_vcd_vars[ n_bit_indx ].Get_Value_Dump_Lines( n_cur_bit )

            s_cur_dump_line = 'b' + s_cur_dump_line + ' '

        else:

            s_cur_dump_line = '%d' % n_new_value

        s_cur_dump_line = s_cur_dump_line + self.s_id + '\n'
        s_dump_lines.append( s_cur_dump_line )
        s_dump_lines = s_dump_lines + s_sub_dump_lines

        return s_dump_lines
 

print( 'INFO: Starting program...' )

# Parse command-line arguments
s_usage = 'usage: %prog [options] stimulus-file'
arg_parser = ArgumentParser()
#opt_parser = OptionParser(
#        usage = s_usage
#        )

arg_parser.add_argument(
        'stimulus_file_path',
        help = 'Pathname of stimulus file to read'
        )
#opt_parser.add_option(
#        '-o',
#        '--output',
#        action = 'store',
#        type = str,
#        dest = 's_vcd_file_path',
#        default = '',
#        help = 'Pathname of file to print VCD to',
#        metavar = 'FILE'
#        )

s_args = arg_parser.parse_args()
#( opt_names, opt_values ) = opt_parser.parse_args()

s_stim_file_path = s_args.stimulus_file_path
n_stim_file_base_end_pos = s_stim_file_path.find( '.sim_out' )

if( n_stim_file_base_end_pos == -1 ):
    print 'ERROR: Incorrect file type'
    sys.exit( -1 )

s_vcd_file_path = s_stim_file_path[ : n_stim_file_base_end_pos ]
s_vcd_file_path = s_vcd_file_path + '.vcd'


# Open simulation output file
print( 'INFO: Opening %s...\n' % s_stim_file_path )
stim_file = open(
        s_stim_file_path,
        'r'
        )
s_stim_lines = stim_file.readlines()
stim_file.close()

# Enumerate all listed variables
for s_stim_line in s_stim_lines:

    if( s_stim_line[ 0 ] == '$' ):

        print( 'ERROR: AS directive found in stimulus file.' )
        sys.exit( -1 )

    if( s_stim_line[ 0 ] == '#' ):
        continue

    s_stim_line_tokens = s_stim_line.split()
    s_cur_var = s_stim_line_tokens[ 0 ]
    
    if( s_cur_var not in s_vcd_vars ):
        s_vcd_vars.append( s_cur_var )

print( 'INFO: Found %d logged variables.' % len( s_vcd_vars ) )

# Populate VCD object list
for s_vcd_var in s_vcd_vars:
    vcd_vars.append( VCD_Var( s_vcd_var ) )

# Compose date specifier
t_now = datetime.datetime.now()
s_vcd_lines.append(
        '$date ' +
        t_now.strftime( '%b %d %Y %H:%M:%S' ) +
        ' $end\n'
        )

# Compose simulator version specifier
s_vcd_lines.append(
        '$version ' +
        s_version +
        ' $end\n'
        )

# Compose timescale specifier
s_vcd_lines.append(
        '$timescale ' +
        s_timescale +
        ' $end\n'
        )

# Compose variable declarations
s_vcd_lines.append( '$scope module top $end\n' )

for vcd_var in vcd_vars:
    s_vcd_lines = s_vcd_lines + vcd_var.Get_Var_Lines()

s_vcd_lines.append( '$upscope $end\n' )
s_vcd_lines.append( '$enddefinitions $end\n' )

# Compose scope declarations
#for vcd_var in vcd_vars:
#    s_vcd_lines = s_vcd_lines + vcd_var.Get_Scope_Lines()

# Compose variable dump lines
s_vcd_lines.append( '#0\n' )
s_vcd_lines.append( '$dumpvars\n' )

for vcd_var in vcd_vars:
    s_vcd_lines = s_vcd_lines + vcd_var.Get_Var_Dump_Lines()

s_vcd_lines.append( '$end\n' )

for vcd_var in vcd_vars:
    s_vcd_lines = s_vcd_lines + vcd_var.Get_Value_Dump_Lines( 0 )

# Compose value dump lines
print( 'INFO: Parsing value dump...' )
for s_stim_line in s_stim_lines:

    if( s_stim_line[ 0 ] == '#' ):

        s_time_delay = s_stim_line[ 1 :].strip()
        n_time_delay = int( s_time_delay ) * n_time_multiplier
        n_cur_time = n_cur_time + n_time_delay

        s_vcd_lines.append( '#%d\n' % n_cur_time )
        continue

    s_stim_line_tokens = s_stim_line.split()

    for vcd_var in vcd_vars:

        if( s_stim_line_tokens[ 0 ] == vcd_var.s_ref ):

            s_new_value = s_stim_line_tokens[ 2 ]
            s_new_value = s_new_value.replace( '0x', '' )

            s_vcd_lines = s_vcd_lines + vcd_var.Get_Value_Dump_Lines( int( s_new_value, 16 ) )


# Write all lines to VCD file
print( 'INFO: Writing VCD to %s' % s_vcd_file_path )
vcd_file = open(
        s_vcd_file_path,
        'wb'
        )
vcd_file.writelines( s_vcd_lines )
vcd_file.close()

# Delete simulation output file to avoid concatenation
#   with next simulation's output
print( 'INFO: Deleting %s' % s_stim_file_path )
os.remove( s_stim_file_path )

print( 'INFO: End of program' )

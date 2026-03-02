#! /usr/bin/env python3
#
# -----------------------------------------------------------------------------
# Copyright (c) 2020-2022, Arm Limited. All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# -----------------------------------------------------------------------------

import re
import os
import sys
import click

# Add the cwd to the path so that if there is a version of imgtool in there then
# it gets used over the system imgtool. Used so that imgtool from upstream
# mcuboot is preferred over system imgtool
cwd = os.getcwd()
sys.path = [cwd] + sys.path
import imgtool
import imgtool.main

parser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(parser_path)
import macro_parser
import subprocess

sign_bin_size_re = re.compile(r"^\s*RE_SIGN_BIN_SIZE\s*=\s*(.*)")
load_addr_re = re.compile(r"^\s*RE_IMAGE_LOAD_ADDRESS\s*=\s*(.*)")
rom_fixed_re = re.compile(r"^\s*RE_IMAGE_ROM_FIXED\s*=\s*(.*)")

#This works around Python 2 and Python 3 handling character encodings
#differently. More information about this issue at
#https://click.palletsprojects.com/en/5.x/python3
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

@click.argument('outfile')
@click.argument('infile')
@click.option('--measured-boot-record', default=False, is_flag=True, help='Add '
              'CBOR encoded measured boot record to the image manifest.')
@click.option('-l', '--layout', help='The file containing the macros of the '
                                     'slot sizes')
@click.option('-v', '--version', callback=imgtool.main.validate_version,
              required=True)
@click.option('--align', type=click.Choice(['1', '2', '4', '8', '16', '32']),
              required=True)
@click.option('-H', '--header-size',
              callback=imgtool.main.validate_header_size,
              type=imgtool.main.BasedIntParamType(), required=True)
@click.option('-t', '--sign-tool', metavar='filename')
@click.option('-s', '--sign-alg', type=click.Choice(['qghppkds1', 'qghppkds3', 'qghppkds5', 'mldsa44', 'mldsa65', 'mldsa87']), default='qghppkds1',
              help='Sign image with one of the MASQ PQC algorithms.')
@click.option('-e', '--encrypt', type=click.Choice(['qeep', 'aes']), default='qeep',
              help='Encrypt image with qeep or aes algorithm. The key will be randomly generated and encaped with KEM.')
@click.command(help='''Create a signed or unsigned image\n
               INFILE and OUTFILE are parsed as Intel HEX if the params have
               .hex extension, otherwise binary format is used''')
def wrap(sign_tool, align, version, header_size, layout, infile, outfile, measured_boot_record, encrypt, sign_alg):

    slot_size = macro_parser.evaluate_macro(layout, sign_bin_size_re, 0, 1)
    load_addr = macro_parser.evaluate_macro(layout, load_addr_re, 0, 1)
    rom_fixed = macro_parser.evaluate_macro(layout, rom_fixed_re, 0, 1)

    print("args:", sign_tool, align, version, header_size, layout, encrypt, infile, outfile, measured_boot_record, encrypt, sign_alg)
    
    if measured_boot_record:
        if "_s.o" in layout:
            record_sw_type = "SPE"
        elif "_ns.o" in layout:
            record_sw_type = "NSPE"
        else:
            record_sw_type = "NSPE_SPE"
    else:
        record_sw_type = None

    if int(align) <= 8 :
        #default behaviour for max_align
        max_align=8
    else:
        #max_align must be set to align
        max_align=align

    if record_sw_type is not None:
        cmd = "{}/qtpsign -v {} -t b_u585i_iot02a -s {} -h {} -a {} -k {}/sbl_certs/{}/customer.key -c {}/sbl_certs/{}/customer.crt -i {} -o {} -b {}".format(sign_tool, version, slot_size, header_size, align, sign_tool, sign_alg, sign_tool, sign_alg, infile, outfile, record_sw_type)
    else:
        cmd = "{}/qtpsign -v {} -t b_u585i_iot02a -s {} -h {} -a {} -k {}/sbl_certs/{}/customer.key -c {}/sbl_certs/{}/customer.crt -i {} -o {}".format(sign_tool, version, slot_size, header_size, align, sign_tool, sign_alg, sign_tool, sign_alg, infile, outfile)
  
    if encrypt is not None:
        cmd = cmd + " -e{}".format(encrypt)

    print("cmd", cmd)
    os.system(cmd)



if __name__ == '__main__':
    wrap()

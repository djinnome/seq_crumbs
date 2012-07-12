# Copyright 2012 Jose Blanca, Peio Ziarsolo, COMAV-Univ. Politecnica Valencia
# This file is part of seq_crumbs.
# seq_crumbs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# seq_crumbs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR  PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with seq_crumbs. If not, see <http://www.gnu.org/licenses/>.


from crumbs.utils import (get_inputs_from_args, get_output_from_args,
                          io_setup_argparse)
from crumbs.seqio import read_seqrecords, count_seqs_in_files


def sample_setup_argparse():
    'It prepares the command line argument parsing.'
    description = 'Get first seqs from file[s]'
    parser = io_setup_argparse()
    parser.description = description
    parser.add_argument('-n', '--num_seqs', default=10, type=int,
                        dest='num_seqs', help='Number of sequendes to print')
    return parser


def sample_parse_args(parser):
    '''It parses the command line and it returns a dict with the arguments.'''
    parsed_args = parser.parse_args()
    num_seqs = parsed_args.num_seqs
    in_fhands = get_inputs_from_args(parsed_args)
    out_fhand = get_output_from_args(parsed_args)

    return {'out_fhand': out_fhand, 'in_fhands': in_fhands,
            'num_seqs': num_seqs}




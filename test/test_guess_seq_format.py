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

'''
Created on 21/06/2012

@author: jose
'''

import unittest
import os.path
from subprocess import check_output, CalledProcessError
from tempfile import NamedTemporaryFile

from crumbs.utils.bin_utils import BIN_DIR

# pylint: disable=R0201
# pylint: disable=R0904


class GuessFormat(unittest.TestCase):
    'It tests the guess_seq_format binary'

    def test_guess_format(self):
        'It tests guess_seq_format'

        guess_bin = os.path.join(BIN_DIR, 'guess_seq_format')

        assert 'usage' in check_output([guess_bin, '-h'])

        # a fasta file
        fasta_fhand = NamedTemporaryFile()
        fasta_fhand.write('>seq\nACTA\n')
        fasta_fhand.flush()
        assert check_output([guess_bin, fasta_fhand.name]) == 'fasta\n'

        # Unknown_format
        bad_fhand = NamedTemporaryFile()
        bad_fhand.write('bad file')
        bad_fhand.flush()
        stderr = NamedTemporaryFile()
        try:
            check_output([guess_bin, bad_fhand.name], stderr=stderr)
            self.fail('Error expected')
        except CalledProcessError:
            assert open(stderr.name).read().startswith('Sequence file of unkn')

    def test_stdin(self):
        'It works with stdin'
        guess_bin = os.path.join(BIN_DIR, 'guess_seq_format')
        fasta_fhand = NamedTemporaryFile()
        fasta_fhand.write('>seq\nACTA\n')
        fasta_fhand.flush()
        fmt = check_output([guess_bin], stdin=open(fasta_fhand.name))
        assert fmt == 'fasta\n'

    def test_version(self):
        'It can return its version number'
        guess_bin = os.path.join(BIN_DIR, 'guess_seq_format')

        stderr = NamedTemporaryFile()
        check_output([guess_bin, '--version'], stderr=stderr)
        assert 'from seq_crumbs version:' in open(stderr.name).read()

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'SffExtractTest.test_items_in_gff']
    unittest.main()

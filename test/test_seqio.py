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

# pylint: disable=R0201
# pylint: disable=R0904

import os
import unittest
from cStringIO import StringIO

from crumbs.utils.test_utils import TEST_DATA_DIR
from crumbs.utils.tags import SEQITEM, SEQRECORD
from crumbs.utils.seq_utils import get_seq_class
from crumbs.seqio import (guess_seq_type, _itemize_fasta, _itemize_fastq,
                          read_seqs, write_seqs)


class SeqioTest(unittest.TestCase):
    'It test seqIO functions'

    def test_guess_seq_type(self):
        'It guesses if the sequence is nucleotide or protein'
        fpath = os.path.join(TEST_DATA_DIR, 'arabidopsis_genes')
        assert guess_seq_type(open(fpath)) == 'nucl'

        fpath = os.path.join(TEST_DATA_DIR, 'pairend2.sfastq')
        assert guess_seq_type(open(fpath)) == 'nucl'


class SimpleIOTest(unittest.TestCase):
    'It tests the simple input and output read'
    def test_fasta_itemizer(self):
        'It tests the fasta itemizer'
        fhand = StringIO('>s1\nACTG\n>s2 desc\nACTG\n')
        seqs = list(_itemize_fasta(fhand))
        assert seqs == [('s1', ['>s1\n', 'ACTG\n']),
                        ('s2', ['>s2 desc\n', 'ACTG\n'])]

    def test_fastq_itemizer(self):
        'It tests the fasta itemizer'
        fhand = StringIO('@s1\nACTG\n+\n1234\n@s2 desc\nACTG\n+\n4321\n')
        seqs = list(_itemize_fastq(fhand))
        assert seqs == [('s1', ['@s1\n', 'ACTG\n', '+\n', '1234\n']),
                        ('s2', ['@s2 desc\n', 'ACTG\n', '+\n', '4321\n'])]

    def test_seqitems_io(self):
        'It checks the different seq class streams IO'
        fhand = StringIO('>s1\nACTG\n>s2 desc\nACTG\n')
        seqs = list(read_seqs([fhand], 'fasta',
                              prefered_seq_classes=[SEQITEM]))
        assert get_seq_class(seqs[0]) == SEQITEM
        fhand = StringIO()
        write_seqs(seqs, fhand)
        assert fhand.getvalue() == '>s1\nACTG\n>s2 desc\nACTG\n'

        # SeqRecord
        fhand = StringIO('>s1\nACTG\n>s2 desc\nACTG\n')
        seqs = list(read_seqs([fhand], 'fasta',
                              prefered_seq_classes=[SEQRECORD]))
        assert get_seq_class(seqs[0]) == SEQRECORD
        fhand = StringIO()
        write_seqs(seqs, fhand, 'fasta')
        assert fhand.getvalue() == '>s1\nACTG\n>s2 desc\nACTG\n'

        # seqitem not possible with different input and output formats
        fhand = StringIO('>s1\nACTG\n>s2 desc\nACTG\n')
        try:
            seqs = list(read_seqs([fhand], 'fasta', out_format='fastq',
                        prefered_seq_classes=[SEQITEM]))
            self.fail('ValueError expected')
        except ValueError:
            pass

        fhand = StringIO('>s1\nACTG\n>s2 desc\nACTG\n')
        seqs = list(read_seqs([fhand], 'fasta', out_format='fasta',
                        prefered_seq_classes=[SEQITEM]))
        fhand = StringIO()
        write_seqs(seqs, fhand)
        assert fhand.getvalue() == '>s1\nACTG\n>s2 desc\nACTG\n'

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'SffExtractTest.test_items_in_gff']
    unittest.main()

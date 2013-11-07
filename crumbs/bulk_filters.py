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

# pylint: disable=C0111

from crumbs.seq import get_str_seq
from crumbs.pairs import group_seqs_in_pairs
from crumbs.seqio import read_seqs, write_seqs
from crumbs.utils.tags import SEQITEM
from crumbs.iterutils import sorted_unique_items


def _tabbed_pairs_equal(pair1, pair2):
    pair1 = pair1.split('\t')
    pair2 = pair2.split('\t')
    if len(pair1) != len(pair2):
        return False
    seqs_in_pair1 = pair1[1::3]
    seqs_in_pair2 = pair2[1::3]
    for read1, read2 in zip(seqs_in_pair1, seqs_in_pair2):
        if read1 != read2:
            return False
    return True


def _seqitem_pairs_equal(pair1, pair2):
    if len(pair1) != len(pair2):
        return False
    else:
        for read1, read2 in zip(pair1, pair2):
            if not get_str_seq(read1) == get_str_seq(read2):
                return False
        return True


def _read_pairs(in_fhands, paired_reads):
    seqs = read_seqs(in_fhands, prefered_seq_classes=[SEQITEM])
    if paired_reads:
        pairs = group_seqs_in_pairs(seqs)
    else:
        pairs = ([seq] for seq in seqs)
    return pairs


def _key(pair):
    key = []
    for read in pair:
        key.append(get_str_seq(read))
    return key


def filter_duplicates(in_fhands, out_fhand, paired_reads, n_seqs_packet=None,
                      directory=None):
    if not in_fhands:
        raise ValueError('At least one input fhand is required')
    pairs = _read_pairs(in_fhands, paired_reads)
    for pair in sorted_unique_items(pairs, key=_key,
                                    max_items_in_memory=n_seqs_packet,
                                    temp_dir=directory):
        write_seqs(pair, out_fhand)
    out_fhand.flush()

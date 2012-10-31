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

import subprocess
from tempfile import NamedTemporaryFile
from collections import Counter
from random import randint

from Bio.SeqFeature import SeqFeature, FeatureLocation

from crumbs.utils.bin_utils import (get_binary_path, popen,
                                    check_process_finishes)
from crumbs.utils.tags import (PROCESSED_PACKETS, PROCESSED_SEQS, YIELDED_SEQS,
                               FIVE_PRIME, THREE_PRIME)
from crumbs.seqio import write_seqrecords, read_seqrecords
from crumbs.blast import BlastMatcher2
from crumbs.settings import POLYA_ANNOTATOR_MIN_LEN, POLYA_ANNOTATOR_MISMATCHES

# pylint: disable=R0903


def _run_estscan(seqrecords, pep_out_fpath, dna_out_fpath, matrix_fpath):
    'It runs estscan in the input seqs'
    seq_fhand = write_seqrecords(seqrecords, file_format='fasta')
    seq_fhand.flush()
    binary = get_binary_path('estscan')

    cmd = [binary, '-t', pep_out_fpath, '-o', dna_out_fpath, '-M',
           matrix_fpath, seq_fhand.name]
    process = popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check_process_finishes(process, binary=cmd[0])
    seq_fhand.close()


def _read_estcan_result(fhand, result, file_type):
    'It reads a dna or pep ESTscan result file'
    for seq in read_seqrecords([fhand], file_format='fasta'):
        items = [i.strip() for i in seq.description.split(';')]
        strand = -1 if 'minus strand' in items else 1
        start, end = items[0].split(' ', 3)[1:3]
        seqid = seq.id
        try:
            seq_orfs = result[seqid]
        except KeyError:
            seq_orfs = {}
            result[seqid] = seq_orfs
        orf_key = (int(start), int(end), strand)
        if orf_key in seq_orfs:
            orf = seq_orfs[orf_key]
        else:
            orf = {}
            seq_orfs[orf_key] = orf
        orf[file_type] = seq.seq


def _read_estcan_results(pep_fhand, dna_fhand):
    'It reads the fhand result files'
    result = {}
    _read_estcan_result(pep_fhand, result, 'pep')
    _read_estcan_result(dna_fhand, result, 'dna')
    return result


class EstscanOrfAnnotator(object):
    'It annotates the given seqrecords'
    def __init__(self, usage_matrix):
        'Initiator'
        self._usage_matrix = usage_matrix
        self._stats = Counter()

    @property
    def stats(self):
        'The process stats'
        return self._stats

    def __call__(self, seqrecords):
        'It runs the actual annotations'
        stats = self._stats
        stats[PROCESSED_PACKETS] += 1
        pep_fhand = NamedTemporaryFile()
        dna_fhand = NamedTemporaryFile()
        _run_estscan(seqrecords, pep_fhand.name, dna_fhand.name,
                     self._usage_matrix)
        # now we read the result files
        estscan_result = _read_estcan_results(open(pep_fhand.name),
                                              open(dna_fhand.name))

        for seq in seqrecords:
            stats[PROCESSED_SEQS] += 1
            seq_name = seq.id
            orfs = estscan_result.get(seq_name, {})
            feats = []
            for (start, end, strand), seqs in orfs.viewitems():
                start -= 1
                # end is fine  -- end[
                feat = SeqFeature(location=FeatureLocation(start, end, strand),
                                  type='ORF', qualifiers=seqs)
                feats.append(feat)
            if feats:
                seq.features.extend(feats)
            stats[YIELDED_SEQS] += 1

        dna_fhand.close()
        pep_fhand.close()
        return seqrecords


def _detect_polya_tail(seq, location, min_len, max_cont_mismatches):
    '''It detects 3' poylA or 5' polyT tails.

    This function is a re-implementation of the EMBOSS's trimest code.
    It will return the position of a poly-A in 3' or a poly-T in 5'.
    It returns the start and end of the tail. The nucleotide in the end
    position won't be included in the poly-A.
    '''
    if location == FIVE_PRIME:
        tail_nucl = 'T'
        inc = 1
        start = 0
        end = len(seq)
    elif location == THREE_PRIME:
        tail_nucl = 'A'
        inc = -1
        start = -1
        end = -len(seq) - 1
    else:
        msg = 'location should be five or three prime'
        raise ValueError(msg)

    mismatch_count = 0
    poly_count = 0
    tail_len = 0
    result = 0

    for index in range(start, end, inc):
        nucl = seq[index].upper()
        if nucl == tail_nucl:
            poly_count += 1
            mismatch_count = 0
        elif nucl == 'N':
            pass
        else:
            poly_count = 0
            mismatch_count += 1
        if poly_count >= min_len:
            result = tail_len + 1
        if mismatch_count > max_cont_mismatches:
            break
        tail_len += 1
    if result and location == FIVE_PRIME:
        start = 0
        end = result
        result = start, end
    elif result and location == THREE_PRIME:
        end = len(seq)
        start = end - result
        result = start, end
    else:
        result = None
    return result


def _annotate_polya(seqrecord, min_len, max_cont_mismatches):
    'It annotates the polyA with the EMBOSS trimest method'
    str_seq = str(seqrecord.seq)
    polya = _detect_polya_tail(str_seq, THREE_PRIME, min_len,
                               max_cont_mismatches)
    polyt = _detect_polya_tail(str_seq, FIVE_PRIME, min_len,
                               max_cont_mismatches)
    a_len = polya[1] - polya[0] if polya else 0
    t_len = polyt[1] - polyt[0] if polyt else 0
    chosen_tail = None
    if a_len > t_len:
        chosen_tail = 'A'
    elif t_len > a_len:
        chosen_tail = 'T'
    elif a_len and a_len == t_len:
        if randint(0, 1):
            chosen_tail = 'A'
        else:
            chosen_tail = 'T'
    if chosen_tail:
        strand = 1 if chosen_tail == 'A' else -1
        start, end = polya if chosen_tail == 'A' else polyt
        feat = SeqFeature(location=FeatureLocation(start, end, strand),
                          type='polyA_sequence')
        seqrecord.features.append(feat)


class PolyaAnnotator(object):
    'It annotates the given seqrecords with poly-A or poly-T regions'
    def __init__(self, min_len=POLYA_ANNOTATOR_MIN_LEN,
                 max_cont_mismatches=POLYA_ANNOTATOR_MISMATCHES):
        '''It inits the class.

        min_len - minimum number of consecutive As (or Ts) to extend the tail
        max_cont_mismatches - maximum number of consecutive no A (or Ts) to
                              break a tail.
        '''
        self._min_len = min_len
        self._max_cont_mismatches = max_cont_mismatches
        self._stats = Counter()

    @property
    def stats(self):
        'The process stats'
        return self._stats

    def __call__(self, seqrecords):
        'It runs the actual annotations'
        stats = self._stats
        stats[PROCESSED_PACKETS] += 1
        max_cont_mismatches = self._max_cont_mismatches
        min_len = self._min_len

        for seq in seqrecords:
            stats[PROCESSED_SEQS] += 1
            stats[YIELDED_SEQS] += 1
            _annotate_polya(seq, min_len, max_cont_mismatches)
        return seqrecords

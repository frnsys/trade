import re
import json
import terms
import Levenshtein
import pandas as pd
from tqdm import tqdm
from functools import partial
from multiprocessing import Pool
from collections import defaultdict

SIM_THRESHOLD = 0.94
WHITESPACE_RE = re.compile('\s+')
PARENS_RE = re.compile('\([^)]+\)')
ENDPARENS_RE = re.compile('\([^)]+$')

# How legal entity names are actually rendered
# can vary widely, so trying to generate all variations here
exts = sum(terms.terms_by_type.values(), []) + sum(terms.terms_by_country.values(), [])
exts = [e.replace('.', '') for e in exts]
exts = exts + [e.replace(' ', '') for e in exts]
exts = exts + [e.replace('/', '') for e in exts]
exts = [e.upper() for e in exts]
exts = set(exts)
entities = [re.compile(' {}$'.format(l.strip())) for l in exts]


def strip_entities(name):
    """Strip out legal entities
    names from the end of a name"""
    found = True
    while found:
        for e in entities:
            res = e.search(name)
            if res is not None:
                name = e.sub('', name)
                break
        else:
            found = False
    return name


def clean(name):
    """Attempt to clean up a name"""
    orig = name

    # These occasionally show up
    name = name.replace('UNTO THE ORDER OF', '')
    name = name.replace('TO THE ORDER OF', '')

    name = name.strip('(').strip(')')
    name = PARENS_RE.sub('', name)
    name = ENDPARENS_RE.sub('', name)
    name = name.strip('/')\
        .replace('.', '')\
        .replace(',', ' ')\
        .replace(' AND ', ' & ')\
        .strip('-')\
        .strip()
    name = WHITESPACE_RE.sub(' ', name)
    name = name.upper()
    name = strip_entities(name)
    if not name:
        print('Cleaning obliterated name for "{}", preserving original'.format(orig))
        return orig
    return name


def find_candidate(names, name):
    """Find matches above threshold"""
    # Include self
    cands = [(name, 1.0)]
    for name_ in names:
        if name == name_: continue

        # To vastly reduce searching, only compare
        # if first characters match
        if name[0] != name_[0]: continue

        sim = Levenshtein.ratio(name, name_)
        if sim >= SIM_THRESHOLD:
            cands.append((name_, sim))
    return name, cands


if __name__ == '__main__':
    print('Loading csv...')
    df = pd.read_csv('data/src/ams_bill_of_lading_summary__2018.csv')

    freqs = defaultdict(int)

    skipped = 0
    for r in tqdm(df.itertuples()):
        # One of the parties is NaN, skip
        # TODO investigate further
        if not isinstance(r.shipper_party_name, str) or not isinstance(r.consignee_name, str):
            skipped += 1
            continue

        fm_name = r.shipper_party_name
        to_name = r.consignee_name

        freqs[fm_name] += 1
        freqs[to_name] += 1

    print('Skipped: {:,}'.format(skipped))

    print('Cleaning names...')
    cleaned = {name: clean(name) for name in tqdm(freqs.keys())}

    # Merge cleaned name frequencies
    freqs_ = {}
    for name, freq in tqdm(freqs.items()):
        name = cleaned[name]
        freqs_[name] = freqs_.get(name, 0) + freq
    freqs = freqs_

    cands = {}
    names = set(cleaned.values())
    fn = partial(find_candidate, names)
    with Pool() as p:
        for name, cnds in tqdm(p.imap(fn, names), total=len(names)):
            if not cnds: continue
            cands[name] = cnds

    # Get frequencies for candidates
    cands_ = {}
    for name, cnds in cands.items():
        cnds = [(n, sim, freqs[n]) for n, sim in cnds]
        total = sum(c[2] for c in cnds)
        cands_[name] = [(n, sim, freq, freq/total) for n, sim, freq in cnds]
    cands = cands_

    normalized = {}
    for name, cs in cands.items():
        norm = max(cs, key=lambda c: c[3])
        normalized[name] = norm[0]

    with open('data/names/candidates.json', 'w') as f:
        json.dump(cands, f)

    with open('data/names/freqs.json', 'w') as f:
        json.dump(freqs, f)

    with open('data/names/normalized.json', 'w') as f:
        json.dump(normalized, f)
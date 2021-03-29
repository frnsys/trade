import re
import json
import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm
from fa2 import ForceAtlas2
from collections import defaultdict, Counter

print('Loading csv...')
df = pd.read_csv('data/src/ams_bill_of_lading_summary__2018.csv')

print('Loading normalized names...')
normalized_names = json.load(open('data/names/normalized.json'))

lookup = {}
inv_lookup = {}
graph = defaultdict(lambda: defaultdict(int))

STACKABLE_RE = re.compile('(NOT)? STACKABLES?')

def clean_desc(desc):
    desc = desc.replace('-', '')
    desc = STACKABLE_RE.sub('', desc)
    return desc

def get_id(name):
    if name not in inv_lookup:
        id = len(lookup)
        lookup[id] = name
        inv_lookup[name] = id
    return inv_lookup[name]

descs_ship = defaultdict(list)
descs_recv = defaultdict(list)

skipped = 0
for r in tqdm(df.itertuples(), desc='Building graph data'):
    # One of the parties is NaN, skip
    # TODO investigate further
    if not isinstance(r.shipper_party_name, str) or not isinstance(r.consignee_name, str):
        # print('Skipped:')
        # print(r.shipper_party_name)
        # print(r.consignee_name)
        # print('-'*12)
        skipped += 1
        continue

    text = r.description_text

    fm_name = normalized_names.get(r.shipper_party_name, r.shipper_party_name)
    to_name = normalized_names.get(r.consignee_name, r.consignee_name)

    r_id = get_id(fm_name)
    c_id = get_id(to_name)

    if isinstance(text, str):
        descs_ship[r_id].append(clean_desc(text))
        descs_recv[c_id].append(clean_desc(text))
    graph[r_id][c_id] += 1

print('Skipped: {:,}'.format(skipped))

with open('data/graph.json', 'w') as f:
    json.dump({
        'graph': graph,
        'index': lookup
    }, f)

weights = []
G = nx.Graph()
for f, ts in tqdm(graph.items(), total=len(graph), desc='Creating graph'):
    for t, weight in ts.items():
        weights.append(weight)
        G.add_edge(f, t, w=weight)

df_data = []
for f, ts in tqdm(graph.items(), total=len(graph), desc='Creating dataframe'):
    name = lookup[f]

    # Simple tokenization
    recv_terms = []
    for desc in descs_recv[f]:
        recv_terms += desc.split(' ')
    ship_terms = []
    for desc in descs_ship[f]:
        ship_terms += desc.split(' ')

    partners = [(lookup[p], w) for p, w in ts.items()]
    partners = sorted(partners, key=lambda p: p[1], reverse=True)

    df_data.append({
        'name': name,
        'degree': G.degree(f),
        'mean_weight': np.mean(list(ts.values())),
        'top_recv_terms': ', '.join([t for t, _ in Counter(recv_terms).most_common(10)]),
        'top_ship_terms': ', '.join([t for t, _ in Counter(ship_terms).most_common(10)]),
        'top_partners': '; '.join(['{} ({})'.format(name, w) for name, w in partners[:5]])
    })
graph_df = pd.DataFrame(df_data)
graph_df.to_csv('data/graph.csv', index=False)

print('Mean weights:', np.mean(weights))
print('Max weights:', max(weights))
print('1-weights:', sum(1 for w in weights if w == 1))

# Drop edges with weights
# less than min_weights
# to vastly reduce edges
# for visualization purposes
G = nx.Graph()
min_weights = 3
for f, ts in tqdm(graph.items(), total=len(graph), desc='Creating pruned graph'):
    for t, weight in ts.items():
        if weight >= min_weights:
            G.add_edge(f, t, w=weight)

print('Nodes:', len(G.nodes()))
print('Edges:', len(G.edges()))
components = list(nx.connected_components(G))
print('Connected components:', len(components))
print('Isolated nodes:', sum(1 for c in components if len(c) <= 1))
print('Mean component nodes:', np.mean([len(c) for c in components]))

layouts = []

print('Generating layouts...')
subgraphs = [c for c in nx.connected_component_subgraphs(G) if len(c.nodes()) > 1]
subgraphs = sorted(subgraphs, key=lambda c: len(c.nodes()))
for c in tqdm(subgraphs):
    # https://networkx.github.io/documentation/stable/reference/drawing.html#module-networkx.drawing.layout
    # layout = nx.drawing.layout.spectral_layout(c, weight='w')
    # layout = nx.drawing.layout.spring_layout(c, weight='w')

    forceatlas2 = ForceAtlas2(
        # Behavior alternatives
        outboundAttractionDistribution=True,  # Dissuade hubs
        linLogMode=False,  # NOT IMPLEMENTED
        adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
        edgeWeightInfluence=1.0,

        # Performance
        jitterTolerance=1.0,  # Tolerance
        barnesHutOptimize=True,
        barnesHutTheta=1.2,
        multiThreaded=False,  # NOT IMPLEMENTED

        # Tuning
        scalingRatio=2.0,
        strongGravityMode=False,
        gravity=1.0,

        # Log
        verbose=False)
    try:
        layout = forceatlas2.forceatlas2_networkx_layout(c, pos=None, iterations=200)
    except ZeroDivisionError:
        layout = nx.drawing.layout.spectral_layout(c, weight='w')
    layouts.append({k: tuple(v) for k, v in layout.items()})

import ipdb; ipdb.set_trace()
with open('data/layouts.json', 'w') as f:
    json.dump(layouts, f)
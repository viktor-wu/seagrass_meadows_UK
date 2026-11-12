#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 09:44:11 2026

@author: viktorwu
"""
#%%
%matplotlib widget

import geopandas as gpd
import pandas as pd
import numpy as np
import os
import pyogrio
import matplotlib.pyplot as plt

#Input datasets
inputs = [
    {
        'path': "C:\\Users\\3158557W\\Desktop\\SEAGRASS LAYERS\\National_Seagrass_Layer_England_2024_All_Years_9171382247343351990.gpkg",
        'source': 'Natural England',
        'year_field': 'year',
        'layer': None
    },
    {
        'path': "C:\\Users\\3158557W\\Desktop\\SEAGRASS LAYERS\\GeMS___Scottish_Priority_Marine_Features_5486385292911346861.gpkg",
        'source': 'NatureScot',
        'year_field': 'year',
        'layer': None
    },
    {
        'path': "C:\\Users\\3158557W\\Desktop\\SEAGRASS LAYERS\\Seagrass loch_craignish.kml",
        'source': 'Seawilding',
        'year_field': 'year',
        'layer': None
    }
]

output_path = "C:\\Users\\3158557W\\Desktop\\SEAGRASS LAYERS\\all_seagrass_meadows.gpkg"

#%%

for item in inputs:

    print('\n' + '='*60)
    print(item['source'])
    print('='*60)

    layers = pyogrio.list_layers(item['path'])

    print('Available layers:')
    print(layers)
    
#%% Layer 1
kml_path = inputs[2]['path']

layers = pyogrio.list_layers(kml_path)
sw = gpd.read_file(
    kml_path,
    layer='Seagrass Meadows'
)

print(
    sw.drop(columns='geometry').to_string(index=False)
)

print('CRS:', sw.crs)

sw_metric = sw.to_crs('EPSG:27700')

sw_metric['calculated_area_ha'] = (
    sw_metric.geometry.area / 10000
)

print(
    sw_metric[
        ['Name', 'Area', 'Area2', 'area3',
         'area_ha', 'aream2', 'calculated_area_ha']
    ].to_string(index=False)
)

sw_metric = sw.to_crs('EPSG:27700')

sw_metric['area_calculated_ha'] = (
    sw_metric.geometry.area / 10000
)

sw_metric['source'] = 'Seawilding'
sw_metric['survey_year'] = 2023

sw_metric['species'] = 'unknown'

sw_metric.loc[
    sw_metric['Name'].str.contains('noltei', case=False, na=False),
    'species'
] = 'Zostera noltei'


#Exclude Zostera noltei polygons
sw_zostera = sw[
    ~sw['Name'].str.contains('noltei', case=False, na=False)
].copy()

#Reproject to British National Grid
sw_zostera = sw_zostera.to_crs('EPSG:27700')

#Calculate area in hectares
sw_zostera['area_ha_calculated'] = (
    sw_zostera.geometry.area / 10000
)

#Add standardised attributes
sw_zostera['source'] = 'Seawilding'
sw_zostera['species'] = 'Zostera marina'
sw_zostera['survey_year'] = 2023

print('Zostera marina polygons:', len(sw_zostera))
print(sw_zostera[['Name', 'area_ha_calculated']].to_string(index=False))

#%% Layer 2
ne = gpd.read_file(inputs[0]['path'])

print('\nNATURAL ENGLAND')
for col in ['Habitat', 'HAB_TYPE', 'ORIG_HAB',
            'ORIG_CLASS', 'Year_', 'DET_DATE']:

    print('\n', col)
    print(ne[col].value_counts(dropna=False).head(30))

#Convert Year_ to numeric
ne['Year_'] = pd.to_numeric(ne['Year_'], errors='coerce')

#Keep records from selected year onwards
ne_recent = ne[ne['Year_'] >= 2017].copy()

print('Features retained:', len(ne_recent))
print(ne_recent['Year_'].value_counts().sort_index())

ne_recent['area_ha_calculated'] = (
    ne_recent.geometry.area / 10000
)

#%% Layer 3
ns = gpd.read_file(inputs[1]['path'])

print('\nNATURESCOT')
for col in ['PMF', 'PMF_COMPONENT', 'EUNIS_CODE',
            'CURRENT_BIOTOPE_NAME', 'ORIG_CLASSIFICATION',
            'YEAR', 'DATE_', 'DATE_RANGE']:

    print('\n', col)
    print(ns[col].value_counts(dropna=False).head(30))
    
    
#Filter seagrass
ns_seagrass = ns.loc[
    ns['PMF'] == 'Seagrass beds'
].copy()

print('Number of seagrass features:', len(ns_seagrass))

#Inspect components
print('\nPMF_COMPONENT:')
print(
    ns_seagrass['PMF_COMPONENT']
    .value_counts(dropna=False)
)

print('\nEUNIS_CODE:')
print(
    ns_seagrass['EUNIS_CODE']
    .value_counts(dropna=False)
)

print('\nCURRENT_BIOTOPE_NAME:')
print(
    ns_seagrass['CURRENT_BIOTOPE_NAME']
    .value_counts(dropna=False)
)

ns_zmarina = ns_seagrass[
    ns_seagrass['PMF_COMPONENT'].isin([
        'Zostera marina/angustifolia beds on infralittoral clean or muddy sand',
        'Zostera marina/angustifolia beds on lower shore clean or muddy sand'
    ])
].copy()

print('Features:', len(ns_zmarina))
print(ns_zmarina['PMF_COMPONENT'].value_counts())


ns_zmarina = ns_zmarina[
    ns_zmarina['YEAR'] >= 2017
].copy()

print('Features:', len(ns_zmarina))
print(ns_zmarina['YEAR'].value_counts().sort_index())

ns_zmarina['area_ha_calculated'] = (
    ns_zmarina.geometry.area / 10000
)
    
#%% Sort by size

#Keep polygons of chosen area

ne_recent_1ha = ne_recent[
    ne_recent['area_ha_calculated'] >= 1
].copy()

ns_zmarina_1ha = ns_zmarina[
    ns_zmarina['area_ha_calculated'] >= 1
].copy()

sw_zostera_1ha = sw_zostera[
    sw_zostera['area_ha_calculated'] >= 1
].copy()

#%% Prep for visual inspection

ne_review = ne_recent
ns_review = ns_zmarina
sw_review = sw_zostera

ne_review['source'] = 'Natural England'
ns_review['source'] = 'NatureScot'
sw_review['source'] = 'Seawilding'

all_meadows = gpd.GeoDataFrame(
    pd.concat(
        [ne_review, ns_review, sw_review],
        ignore_index=True
    ),
    crs='EPSG:27700'
)

all_meadows['feature_id'] = [
    f'MEADOW_{i:04d}'
    for i in range(1, len(all_meadows) + 1)
]

#Flag the polygons that meet area threshold
all_meadows['over_1ha'] = (
    all_meadows['area_ha_calculated'] >= 1
)

print('Total polygons:', len(all_meadows))
print('Polygons >= 1 ha:', all_meadows['over_1ha'].sum())
print(all_meadows['source'].value_counts())

#%% Group meadows

#Join by NE BED_Name
#Examine bed names
ne_group_summary = (
    ne_review
    .groupby(['Bed_Name', 'Year_'], dropna=False)
    .agg(
        record_count=('Bed_Name', 'size'),
        geometry_count=(
            'geometry',
            lambda x: sum(
                len(g.geoms) if g.geom_type == 'MultiPolygon' else 1
                for g in x
            )
        ),
        total_area_ha=('area_ha_calculated', 'sum'),
        wb_names=('WB_Name', lambda x: x.dropna().unique().tolist())
    )
    .sort_values('record_count', ascending=False)
)

print(ne_group_summary.head(25))

#Group NE by bed name and survey year
from shapely.ops import unary_union

ne_units = []

for (bed_name, year), group in ne_review.groupby(
    ['Bed_Name', 'Year_'],
    dropna=False
):

    #Leave records with missing names as individual units
    if pd.isna(bed_name):

        for idx, row in group.iterrows():

            ne_units.append({
                'meadow_id': f'NE_{idx}',
                'source': 'Natural England',
                'Bed_Name': bed_name,
                'WB_Name': row['WB_Name'],
                'Year_': year,
                'original_record_count': 1,
                'original_geometry_count': (
                    len(row.geometry.geoms)
                    if row.geometry.geom_type == 'MultiPolygon'
                    else 1
                ),
                'geometry': row.geometry
            })

        continue

    #Combine all geometries belonging to this group
    merged_geometry = unary_union(group.geometry.tolist())

    #Count original geometry parts
    geometry_count = sum(
        len(g.geoms) if g.geom_type == 'MultiPolygon' else 1
        for g in group.geometry
    )

    ne_units.append({
        'meadow_id': f'NE_{len(ne_units) + 1:04d}',
        'source': 'Natural England',
        'Bed_Name': bed_name,
        'WB_Name': ', '.join(
            group['WB_Name'].dropna().unique().astype(str)
        ),
        'Year_': year,
        'original_record_count': len(group),
        'original_geometry_count': geometry_count,
        'area_ha_calculated': merged_geometry.area / 10000,
        'geometry': merged_geometry
    })

ne_units = gpd.GeoDataFrame(
    ne_units,
    crs=ne_review.crs
)

print('Original records:', len(ne_review))
print('Unified meadow units:', len(ne_units))

fig, ax = plt.subplots(figsize=(10, 10))

bedname = 'Carlyon Bay'
#Original polygons
joinedbed = ne_review[
    ne_review['Bed_Name'] == bedname
    ]

joinedbed.plot(
    ax=ax,
    color='lightblue',
    edgecolor='steelblue',
    linewidth=0.4
)

#Merged geometry
joinedbed.plot(
    ax=ax,
    facecolor='none',
    edgecolor='red',
    linewidth=1.5
)

ax.set_title(bedname + '– Original records vs unified meadow')
ax.set_aspect('equal')

plt.show()

#%%
#Join by proximity (NS)

print('Original records:', len(ns_review))
print('\nCRS:', ns_review.crs)

print('\nRecords by year:')
print(ns_review['YEAR'].value_counts(dropna=False).sort_index())

print('\nGeometry types:')
print(ns_review.geometry.geom_type.value_counts())

#Keep a reference to the original record
ns_parts = ns_review.copy()
ns_parts['source_record_id'] = ns_parts.index

#Split MultiPolygons into individual Polygon features
ns_parts = ns_parts.explode(index_parts=True).reset_index(drop=True)

print('Original records:', len(ns_review))
print('Individual polygon parts:', len(ns_parts))

def spatial_clusters(gdf):

    n = len(gdf)

    #Each polygon initially belongs to its own group
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a

    #Find intersecting polygon pairs
    pairs = gdf.sindex.query(
        gdf.geometry,
        predicate='intersects'
    )

    for a, b in zip(pairs[0], pairs[1]):

        if a != b:
            union(a, b)

    #Assign a cluster ID to each connected component
    roots = [find(i) for i in range(n)]

    cluster_lookup = {
        root: cluster_id
        for cluster_id, root in enumerate(sorted(set(roots)), start=1)
    }

    return [cluster_lookup[root] for root in roots]

ns_parts['cluster_id'] = pd.NA

for year, group in ns_parts.groupby('YEAR', dropna=False):

    clusters = spatial_clusters(group)

    ns_parts.loc[group.index, 'cluster_id'] = clusters

print('Polygon parts:', len(ns_parts))
print('Spatial clusters:', ns_parts.groupby(
    ['YEAR', 'cluster_id'], dropna=False
).ngroups)

ns_cluster_summary = (
    ns_parts
    .groupby(['YEAR', 'cluster_id'], dropna=False)
    .agg(
        polygon_part_count=('geometry', 'size'),
        source_record_count=('source_record_id', 'nunique'),
        total_area_ha=('geometry',
                       lambda x: sum(g.area for g in x) / 10000),
        locations=('LOCATION_NAME',
                   lambda x: x.dropna().unique().tolist())
    )
    .sort_values('polygon_part_count', ascending=False)
)

print(ns_cluster_summary.head(25))

#%% land outline (low-res alternative)

import cartopy.io.shapereader as shpreader
import geopandas as gpd

#Get Natural Earth land polygons
land_path = shpreader.natural_earth(
    resolution='10m',
    category='physical',
    name='land'
)

land = gpd.read_file(land_path)
land = land.to_crs('EPSG:27700')

print(land.crs)
print(len(land))

#%% Plot clusters to examine visually
def plot_ns_cluster(year, cluster_id):

    cluster = ns_parts[
        (ns_parts['YEAR'] == year) &
        (ns_parts['cluster_id'] == cluster_id)
    ].copy()

    # Map extent with 2 km margin
    xmin, ymin, xmax, ymax = cluster.total_bounds
    buffer = 2000

    xmin -= buffer
    xmax += buffer
    ymin -= buffer
    ymax += buffer

    nearby_land = land.cx[xmin:xmax, ymin:ymax]

    fig, ax = plt.subplots(figsize=(10, 10))

    nearby_land.plot(
        ax=ax,
        color='lightgrey',
        edgecolor='grey',
        linewidth=0.5
    )

    cluster.plot(
        ax=ax,
        color='orange',
        edgecolor='black',
        linewidth=0.6
    )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect('equal')

    location = cluster['LOCATION_NAME'].dropna().unique()

    ax.set_title(
        f"NatureScot | {location} | {year} | "
        f"{len(cluster)} polygon parts"
    )

    plt.show()

    print('Polygon parts:', len(cluster))
    print('Original records:', cluster['source_record_id'].nunique())
    print('Total area (ha):', cluster.geometry.area.sum() / 10000)
    print('Location:', location)
    
#Example
plot_ns_cluster(2022, 603)  # Mallow Bank
plot_ns_cluster(2022, 217)  # St Peters Pool

#Check if polygons in cluster come from same survey
cluster = ns_parts[
    (ns_parts['YEAR'] == 2022) &
    (ns_parts['cluster_id'] == 603)
]
print(
    cluster.groupby(['SURVEY_NAME', 'EVENT_NAME'], dropna=False)
    .agg(
        record_count=('source_record_id', 'nunique'),
        polygon_parts=('geometry', 'size'),
        locations=('LOCATION_NAME', lambda x: x.dropna().unique().tolist())
    )
    .sort_values('record_count', ascending=False)
)

#%% Merge cluster contents 

from shapely.ops import unary_union

ns_units = []

for (year, cluster_id), group in ns_parts.groupby(
    ['YEAR', 'cluster_id']
):
    merged_geometry = unary_union(group.geometry.tolist())

    ns_units.append({
        'meadow_id': f'NS_{int(year)}_{int(cluster_id):04d}',
        'source': 'NatureScot',
        'YEAR': year,
        'LOCATION_NAME': ', '.join(
            group['LOCATION_NAME'].dropna().unique().astype(str)
        ),
        'SURVEY_NAME': ', '.join(
            group['SURVEY_NAME'].dropna().unique().astype(str)
        ),
        'PMF_COMPONENT': ', '.join(
            group['PMF_COMPONENT'].dropna().unique().astype(str)
        ),
        'original_record_count': group['source_record_id'].nunique(),
        'polygon_part_count': len(group),
        'area_ha_calculated': merged_geometry.area / 10000,
        'geometry': merged_geometry
    })

ns_units = gpd.GeoDataFrame(ns_units, crs=ns_parts.crs) #Final variable

print('Meadow units:', len(ns_units))
print(ns_units.nlargest(10, 'area_ha_calculated')[
    ['meadow_id', 'LOCATION_NAME', 'YEAR',
     'original_record_count', 'area_ha_calculated']
])


#%% Units ready for review

#Natural England
ne_combined = ne_units.copy()

ne_combined['year'] = ne_combined['Year_']
ne_combined['location'] = ne_combined['Bed_Name']

#Recalculate area for all units, including those with missing Bed_Name
ne_combined['area_ha_calculated'] = (
    ne_combined.geometry.area / 10000
)


#NatureScot
ns_combined = ns_units.copy()

ns_combined['year'] = ns_combined['YEAR']
ns_combined['location'] = ns_combined['LOCATION_NAME']


#Seawilding
sw_combined = sw_review.copy()

sw_combined['meadow_id'] = [
    f'SW_{i:04d}' for i in range(1, len(sw_combined) + 1)
]

sw_combined['location'] = sw_combined['Name']
sw_combined['year'] = np.nan
sw_combined['original_record_count'] = 1

#Make sure the area is calculated in the same CRS
sw_combined['area_ha_calculated'] = (
    sw_combined.geometry.area / 10000
)


#Keep a common set of fields
common_columns = [
    'meadow_id',
    'source',
    'year',
    'location',
    'original_record_count',
    'area_ha_calculated',
    'geometry'
]

all_meadow_units = gpd.GeoDataFrame(
    pd.concat(
        [
            ne_combined[common_columns],
            ns_combined[common_columns],
            sw_combined[common_columns]
        ],
        ignore_index=True
    ),
    crs='EPSG:27700'
)

#Unique identifier across all sources
all_meadow_units['feature_id'] = [
    f'MEADOW_{i:04d}'
    for i in range(1, len(all_meadow_units) + 1)
]

#Flag larger meadows for initial review
all_meadow_units['over_1ha'] = (
    all_meadow_units['area_ha_calculated'] >= 1
)

#%% Add attributes to show in interactive window

#Natural England attributes
ne_extra = ne_units[[
    'meadow_id',
    'Bed_Name',
    'WB_Name',
    'Year_'
]].copy()

#Aggregate Density and Data_confidence from original records
ne_attributes = (
    ne_review.groupby(
        ['Bed_Name', 'WB_Name', 'Year_'],
        dropna=False
    )
    .agg(
        Density=('Density', lambda x: ', '.join(
            x.dropna().astype(str).unique()
        )),
        Data_confidence=('Data_confidence', lambda x: ', '.join(
            x.dropna().astype(str).unique()
        ))
    )
    .reset_index()
)

#Attach attributes to meadow units
ne_extra = ne_extra.merge(
    ne_attributes,
    on=['Bed_Name', 'WB_Name', 'Year_'],
    how='left'
)

print(ne_extra[[
    'meadow_id', 'Bed_Name', 'Year_', 'Density', 'Data_confidence'
]].head(10))


#NatureScot attributes
ns_extra = ns_units[[
    'meadow_id',
    'SURVEY_NAME',
    'PMF_COMPONENT'
]].copy()

#Seawilding attributes
sw_extra = sw_review.copy()
sw_extra['meadow_id'] = [
    f'SW_{i:04d}' for i in range(1, len(sw_extra) + 1)
]

sw_extra = sw_extra[[
    'meadow_id',
    'Name',
    'type',
    'Area'
]].copy()

all_meadow_units = all_meadow_units.merge(
    ne_extra, on='meadow_id', how='left'
)

all_meadow_units = all_meadow_units.merge(
    ns_extra, on='meadow_id', how='left'
)

all_meadow_units = all_meadow_units.merge(
    sw_extra, on='meadow_id', how='left'
)


#%%
#https://osdatahub.os.uk/data/downloads/open/VectorMapDistrict?_gl=1*1vdp4ge*_gcl_au*MTUwNzkwMzE5MC4xNzk0MDYwNjE1*_ga*MTQ0NTkxMjM3OS4xNzk0MDYwNjE1*_ga_59ZBN7DVBG*czE3OTQwNjA2MTUkbzEkZzAkdDE3OTQwNjA2MjMkajUyJGwwJGgw
import geopandas as gpd

os_path = "C:\\Users\\3158557W\\Desktop\\SEAGRASS LAYERS\\vmdvec_gb.gpkg"

# See which layers are available
print(gpd.list_layers(os_path))

coast = gpd.read_file(
    os_path,
    layer='tidal_boundary'
)

coast = coast.to_crs('EPSG:27700')
land = coast

print(coast.crs)
print(coast.geom_type.value_counts())
print(coast.columns.tolist())


#%% Plot meadow and surrounding

import matplotlib.pyplot as plt

#Choose candidate
candidate_idx = all_meadow_units.index[
    all_meadow_units['over_1ha']
][0]

candidate = all_meadow_units.loc[[candidate_idx]]

#Get its bounds
xmin, ymin, xmax, ymax = candidate.total_bounds

#Add a 3 km margin around it
buffer = 3000

xmin -= buffer
xmax += buffer
ymin -= buffer
ymax += buffer

#Select all meadows within this map extent
nearby_meadows = all_meadow_units.cx[xmin:xmax, ymin:ymax]

#Select land within the same extent
nearby_land = land.cx[xmin:xmax, ymin:ymax]

#Plot
fig, ax = plt.subplots(figsize=(10, 10))

nearby_land.plot(
    ax=ax,
    color='lightgrey',
    edgecolor='grey',
    linewidth=0.5
)

nearby_meadows.plot(
    ax=ax,
    color='lightblue',
    edgecolor='steelblue',
    linewidth=0.6,
    alpha=0.7
)

candidate.plot(
    ax=ax,
    color='orange',
    edgecolor='black',
    linewidth=1.5
)

ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_aspect('equal')
ax.set_title(candidate['feature_id'].iloc[0])

plt.show()

print(candidate.drop(columns='geometry').T)


#%% Review columns

if 'review_status' not in all_meadow_units.columns:
    all_meadow_units['review_status'] = 'unreviewed'

if 'review_reason' not in all_meadow_units.columns:
    all_meadow_units['review_reason'] = ''

candidate_indices = all_meadow_units.index[
    all_meadow_units['over_1ha']
].tolist()

print('Candidates to review:', len(candidate_indices))

#%% Interactive reviewer

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np
import pandas as pd
import os

#Settings

map_buffer = 3000  #3 km around each candidate

#Attributes to display for each source
source_fields = {
    'Natural England': [
        'Name'
        'source',
        'WB_Name',
        'Bed_Name',
        'Density',
        'year',
        'area_ha_calculated',
        'Data_confidence',
        'DET_MTHD',
        'DET_DATE',
        'ORIG_HAB',
        'SURVEY_NAME'
    ],

    'NatureScot': [
        'Name'
        'source',
        'location',
        'CURRENT_BIOTOPE_NAME',
        'PMF_COMPONENT',
        'year',
        'area_ha_calculated',
        'ACCURACY',
        'DETERMINATION',
        'SURVEY_NAME'
    ],

    'Seawilding': [
        'Name',
        'Area',
        'Area2',
        'area_ha',
        'aream2'
    ]
}

#Figure layout
fig = plt.figure(figsize=(15, 9))

ax_map = fig.add_axes([0.04, 0.15, 0.59, 0.78])
ax_info = fig.add_axes([0.67, 0.15, 0.29, 0.78])

ax_info.axis('off')

#Navigation and decision buttons
ax_previous = fig.add_axes([0.12, 0.04, 0.12, 0.06])
ax_next = fig.add_axes([0.27, 0.04, 0.12, 0.06])
ax_keep = fig.add_axes([0.47, 0.04, 0.12, 0.06])
ax_exclude = fig.add_axes([0.62, 0.04, 0.12, 0.06])
ax_save = fig.add_axes([0.82, 0.04, 0.12, 0.06])

btn_previous = Button(ax_previous, 'Previous')
btn_next = Button(ax_next, 'Next')
btn_keep = Button(ax_keep, 'Keep')
btn_exclude = Button(ax_exclude, 'Exclude')
btn_save = Button(ax_save, 'Save')

#Current position in candidate list
position = 0

#Display one candidate
def show_candidate():

    global position

    idx = candidate_indices[position]
    candidate = all_meadow_units.loc[[idx]]

    #Map extent
    xmin, ymin, xmax, ymax = candidate.total_bounds

    xmin -= map_buffer
    xmax += map_buffer
    ymin -= map_buffer
    ymax += map_buffer

    #Nearby polygons and land
    nearby_meadows = all_meadow_units.cx[xmin:xmax, ymin:ymax]
    nearby_land = land.cx[xmin:xmax, ymin:ymax]

    #Clear previous map
    ax_map.clear()
    ax_info.clear()
    ax_info.axis('off')

    #Plot land
    nearby_land.plot(
        ax=ax_map,
        color='lightgrey',
        edgecolor='grey',
        linewidth=0.5
    )

    #Plot surrounding meadows
    nearby_meadows.plot(
        ax=ax_map,
        color='lightblue',
        edgecolor='steelblue',
        linewidth=0.6,
        alpha=0.7
    )

    #Highlight selected meadow
    candidate.plot(
        ax=ax_map,
        color='orange',
        edgecolor='black',
        linewidth=1.5
    )

    ax_map.set_xlim(xmin, xmax)
    ax_map.set_ylim(ymin, ymax)
    ax_map.set_aspect('equal')

    #Candidate information
    feature_id = candidate['feature_id'].iloc[0]
    source = candidate['source'].iloc[0]
    area = candidate['area_ha_calculated'].iloc[0]
    status = candidate['review_status'].iloc[0]
    reason = candidate['review_reason'].iloc[0]

    ax_map.set_title(
        f'{feature_id} | {source} | {area:.2f} ha',
        fontsize=12
    )

    #Source-specific attributes
    fields = source_fields.get(source, [])

    info_lines = [
        f'Candidate {position + 1} of {len(candidate_indices)}',
        '',
        f'ID: {feature_id}',
        f'Source: {source}',
        f'Area: {area:.2f} ha',
        f'Status: {status}',
        f'Reason: {reason}',
        '',
        'ATTRIBUTES',
        '--------------------------'
    ]

    for field in fields:

        if field in candidate.columns:

            value = candidate[field].iloc[0]

            if pd.notna(value):
                info_lines.append(f'{field}: {value}')

    info_lines.extend([
        '',
        '--------------------------',
        f'Reviewed: {sum(all_meadow_units.loc[candidate_indices, "review_status"] != "unreviewed")} / {len(candidate_indices)}'
    ])

    ax_info.text(
        0,
        1,
        '\n'.join(info_lines),
        va='top',
        fontsize=9,
        wrap=True
    )

    fig.canvas.draw_idle()

    #Also print the full attributes in Spyder's console
    print('\n' + '=' * 60)
    print(feature_id, '|', source)
    print(candidate.drop(columns='geometry').T)


#Navigation

def next_candidate(event):

    global position

    if position < len(candidate_indices) - 1:
        position += 1

    show_candidate()


def previous_candidate(event):

    global position

    if position > 0:
        position -= 1

    show_candidate()

#Record decisions

def mark_keep(event):

    idx = candidate_indices[position]

    all_meadow_units.loc[idx, 'review_status'] = 'keep'
    all_meadow_units.loc[idx, 'review_reason'] = ''

    next_candidate(None)


def mark_exclude(event):

    idx = candidate_indices[position]

    all_meadow_units.loc[idx, 'review_status'] = 'exclude'
    all_meadow_units.loc[idx, 'review_reason'] = ''

    next_candidate(None)



def save_progress(event):

    output_path = os.path.join(
        os.path.dirname(inputs[0]['path']),
        'seagrass_meadow_review.gpkg'
    )

    #Remove previous version so it can be replaced
    if os.path.exists(output_path):
        os.remove(output_path)

    all_meadow_units.to_file(
        output_path,
        driver='GPKG'
    )

    print('\nReview saved to:')
    print(output_path)


#Connect buttons

btn_previous.on_clicked(previous_candidate)
btn_next.on_clicked(next_candidate)
btn_keep.on_clicked(mark_keep)
btn_exclude.on_clicked(mark_exclude)
btn_save.on_clicked(save_progress)

#Show first candidate
show_candidate()

plt.show()
#%% See reviewed

reviewed = gpd.read_file("C:\\Users\\3158557W\\Desktop\\SEAGRASS LAYERS\\seagrass_meadow_review.gpkg")

print(reviewed.columns.tolist())
print(reviewed['review_status'].value_counts())

kept = reviewed[reviewed['review_status'] == 'keep'].copy()

print('Kept meadows:', len(kept))

#Centroid of meadow
centroids = gpd.GeoSeries(kept.geometry.centroid, crs=kept.crs)
centroids_wgs84 = centroids.to_crs('EPSG:4326')
kept['centre_lon'] = centroids_wgs84.x
kept['centre_lat'] = centroids_wgs84.y

kept_wgs84 = kept.to_crs('EPSG:4326')

kept_wgs84['centre_lon'] = centroids_wgs84.x
kept_wgs84['centre_lat'] = centroids_wgs84.y

#%% Exterior coordinates
def get_coordinates(geometry):

    if geometry.geom_type == 'Polygon':

        return [
            [round(lon, 7), round(lat, 7)]
            for lon, lat in geometry.exterior.coords
        ]

    elif geometry.geom_type == 'MultiPolygon':

        return [
            [
                [round(lon, 7), round(lat, 7)]
                for lon, lat in polygon.exterior.coords
            ]
            for polygon in geometry.geoms
        ]

    else:
        return None

kept_wgs84['coordinates'] = (
    kept_wgs84.geometry.apply(get_coordinates)
)
#%% Save first geopackage + final csv
import json

kept.to_file('final_seagrass_meadows.gpkg', driver='GPKG')
final_table = kept_wgs84.drop(columns='geometry').copy()
final_table['coordinates'] = (final_table['coordinates'].apply(json.dumps))
final_table.to_csv('final_seagrass_meadows.csv', index=False)

# %%

#Manually add datelist to table


dates = [
  "2017-01-02",
  "2017-04-02",
  "2017-05-02",
  "2017-06-01",
  "2017-07-31",
  "2017-11-08",
  "2017-11-23",
  "2017-11-28",
  "2017-12-18",
  "2017-12-28",
  "2018-01-17",
  "2018-02-16",
  "2018-04-22",
  "2018-05-07",
  "2018-05-17",
  "2018-05-22",
  "2018-06-06",
  "2018-06-11",
  "2018-06-21",
  "2018-06-26",
  "2018-07-01",
  "2018-07-06",
  "2018-07-11",
  "2018-07-21",
  "2018-07-31",
  "2018-09-29",
  "2018-10-09",
  "2018-10-19",
  "2018-10-24",
  "2018-10-29",
  "2018-11-18",
  "2019-01-17",
  "2019-01-27",
  "2019-02-26",
  "2019-04-12",
  "2019-04-22",
  "2019-05-12",
  "2019-07-16",
  "2019-08-05",
  "2019-09-04",
  "2019-09-14",
  "2019-09-19",
  "2019-09-24",
  "2019-10-19",
  "2019-11-13",
  "2019-12-23",
  "2020-03-27",
  "2020-04-01",
  "2020-04-06",
  "2020-04-11",
  "2020-04-21",
  "2020-04-26",
  "2020-05-06",
  "2020-05-21",
  "2020-05-26",
  "2020-05-31",
  "2020-06-25",
  "2020-07-05",
  "2020-07-30",
  "2020-08-09",
  "2020-09-08",
  "2020-09-18",
  "2020-11-02",
  "2020-12-17",
  "2021-03-22",
  "2021-04-26",
  "2021-05-31",
  "2021-06-05",
  "2021-06-15",
  "2021-07-20",
  "2021-08-09",
  "2021-08-14",
  "2021-09-03",
  "2021-09-08",
  "2021-11-12",
  "2021-11-22",
  "2021-12-02",
  "2022-02-25",
  "2022-03-17",
  "2022-03-22",
  "2022-03-27",
  "2022-04-16",
  "2022-04-26",
  "2022-06-10",
  "2022-06-15",
  "2022-06-20",
  "2022-07-10",
  "2022-07-15",
  "2022-08-09",
  "2022-08-24",
  "2022-10-08",
  "2022-10-13",
  "2022-11-12",
  "2023-01-11",
  "2023-01-21",
  "2023-02-10",
  "2023-02-15",
  "2023-03-02",
  "2023-05-21",
  "2023-05-26",
  "2023-05-31",
  "2023-06-05",
  "2023-06-15",
  "2023-06-25",
  "2023-08-19",
  "2023-08-19",
  "2023-09-03",
  "2023-09-23",
  "2023-11-07",
  "2023-11-17",
  "2023-11-27"
]

final_table.at[final_table.index[9], 'date_list'] = dates

#Note where we stopped
# %%
final_table.to_csv('final_seagrass_meadows.csv', index=False)

# %%

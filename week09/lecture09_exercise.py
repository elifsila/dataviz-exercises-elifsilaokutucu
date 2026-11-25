#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 19:33:35 2026

@author: dina.deifallah
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# Page configuration, title and data source
st.set_page_config(page_title="World Happiness Report", page_icon="🌐", layout='wide')
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# Data Ingestion
DATA = Path(__file__).parent.parent / "data" / "world_happiness_2023.csv"
df = pd.read_csv(DATA)

df.columns = ['Country','Region','Score','GDP','Social_Support',
              'Life_Expectancy','Freedom','Generosity','Corruption']

# Side bar filters
with st.sidebar:
    st.header("Filters")
    regions = ['All Regions'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N", 5, 25, 15)
    

# filter data by region and top_n
filtered = df if selected_region == 'All Regions' else df[df['Region'] == selected_region]
top = filtered.nlargest(top_n, 'Score').sort_values('Score')

# KPI row 
col1, col2, col3 = st.columns(3)
col1.metric("Countries", len(filtered))
col2.metric("Avg Score", f"{filtered['Score'].mean():.2f}",
            f"{filtered['Score'].mean()-df['Score'].mean():+.2f} vs global")
col3.metric("Happiest", filtered.nlargest(1,'Score')['Country'].values[0])

st.divider()

# create top bar chart
fig = px.bar(top, x='Score', y='Country', orientation='h',
             labels={'Score': 'Happiness Score (0–10)', 'Country': ''},
             template='plotly_white', title=f'Happiest {top_n} Countries in 2023 - {selected_region}')

fig.update_layout(title_font=dict(family='Arial', size=13, color='slategrey'),
                  xaxis=dict(range=[0, 8.0]))


st.plotly_chart(fig, width='stretch', height=600) 

# ── NEW: Diverging chart — happiness relative to the global average ─────────────────
# Midpoint = global average score, so the colour shows above (blue) vs below (red) average.
global_avg = df['Score'].mean()

if selected_region == 'All Regions':
    # Overview level: one bar per region
    div = df.groupby('Region', as_index=False)['Score'].mean().rename(columns={'Region': 'Label'})
    level = 'region'
else:
    # Drill-down level: one bar per country in the selected region
    div = filtered[['Country', 'Score']].rename(columns={'Country': 'Label'})
    level = 'country'

div['Gap'] = div['Score'] - global_avg                 # + above average, - below average
div = div.sort_values('Gap')                           # ascending -> largest gap on top
limit = div['Gap'].abs().max()                         # symmetric scale around 0

best, worst = div.iloc[-1], div.iloc[0]
title = (f"{best['Label']} is {best['Gap']:+.2f} points from the global average, "
         f"{worst['Label']} {worst['Gap']:+.2f}") if len(div) > 1 else \
        f"{best['Label']} is {best['Gap']:+.2f} points from the global average"

fig2 = px.bar(div, x='Gap', y='Label', orientation='h',
              color='Gap',
              color_continuous_scale='RdBu',           # diverging: red = below, blue = above average
              color_continuous_midpoint=0,             # white = global average
              range_color=[-limit, limit],
              text=div['Gap'].map('{:+.2f}'.format),
              hover_data={'Score': ':.2f', 'Gap': ':+.2f'},
              labels={'Gap': 'Gap to global average', 'Label': ''},
              template='plotly_white', title=title)

fig2.update_traces(textposition='outside', cliponaxis=False)

# Midpoint reference line + annotation
fig2.add_vline(x=0, line_color='slategrey', line_width=1.5)
fig2.add_annotation(x=0, y=1.02, xref='x', yref='paper', showarrow=False,
                    text=f"Global average = {global_avg:.2f}", yanchor='bottom',
                    font=dict(color='slategrey', size=12))

fig2.update_layout(title_font=dict(family='Arial', size=13, color='slategrey'),
                   xaxis=dict(title=f'Happiness score minus global average ({global_avg:.2f})',
                              range=[-limit * 1.25, limit * 1.25], zeroline=False, showgrid=False),
                   coloraxis_showscale=False,          # bar labels + midpoint annotation replace the colour bar
                   margin=dict(t=80))

st.subheader("How far above or below the global average?")
st.caption(f"One bar per {level}. Pick a region in the sidebar to see its countries.")
st.plotly_chart(fig2, width='stretch', height=max(400, 28 * len(div) + 150))

st.divider()
st.caption("Built with Streamlit + Plotly")
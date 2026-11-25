"""
Uses:
    -Results by Entry.xlsx     [fka: Results.xlsx]
    
Creates:
    -Stats by School.xlsx      [fka: School Ranks.xlsx]
"""

import pandas as pd
import numpy as np
from utils import add_header_row
from config import ROOT, EVENT_LIST
from formatting import write_sheet


def get_event_group_stats(data, school_name):
    data[school_name]['LP'] = (
        data[school_name]['EXT'] + 
        data[school_name]['IMP']
        )/2
    
    data[school_name]['Group'] = (
        data[school_name]['DUO'] + 
        data[school_name]['OID']
        )/2
    
    data[school_name]['PA'] = (
        data[school_name]['OO'] + 
        data[school_name]['INF'] +
        data[school_name]['ENT']
        )/3
    
    data[school_name]['Interp'] = (
        data[school_name]['HI'] + 
        data[school_name]['DI'] + 
        data[school_name]['POI'] + 
        data[school_name]['POE']
        )/4
    
    return data


def _pooled_ranks(frame, cols):  #CLAUDE
    """Flatten the rank columns into one float array with NaNs dropped."""
    ranks = frame[cols].to_numpy(dtype=float).ravel()  # dtype=float fixes the object-dtype issue
    return ranks[~np.isnan(ranks)]


def get_school_stats(df, champs=False):  #CLAUDE
    EVENTS = EVENT_LIST + ['Group', 'PA', 'Interp']

    if champs:
        df = df[df['Break'] == 1]   # filter BEFORE grouping (see note below)
        rank_cols = ['F1', 'F2', 'F3', 'F4', 'F5']
    else:
        rank_cols = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']

    data = {}
    for school_name, df_school in df.groupby('Tm'):
        row = {}
        if not champs:
            row['Class'] = df_school['Class'].iloc[0]
            row['District'] = df_school['District'].iloc[0]
            row['Size'] = len(df_school)
        row['AvgRk'] = 7
        row['SDRk'] = 0
        row.update({event: 7 for event in EVENTS})

        ranks = _pooled_ranks(df_school, rank_cols)
        if len(ranks) > 0:
            row['AvgRk'] = round(np.mean(ranks), 4)
            row['SDRk'] = round(np.std(ranks), 4)

        for event_name, df_event in df_school.groupby('Event'):
            ranks = _pooled_ranks(df_event, rank_cols)
            if len(ranks) > 0:
                row[event_name] = round(np.mean(ranks), 4)

        data[school_name] = row
        data = get_event_group_stats(data, school_name)

    df_schools = pd.DataFrame(data).transpose().reset_index()
    df_schools.rename({'index': 'Team'}, axis=1, inplace=True)
    return df_schools

def save_school_ranks_sheet(df_schools, df_schools_champs):
    df_schools = add_header_row(df_schools)
    df_schools_champs = add_header_row(df_schools_champs)
    
    
    writer = pd.ExcelWriter(ROOT + r'\Code\Stats by School.xlsx', engine='xlsxwriter')
    write_sheet(writer, df=df_schools, sheet_name="Prelims", layout="school_stats", index=False, header=None)
    write_sheet(writer, df=df_schools_champs, sheet_name="Champs", layout="school_stats", index=False, header=None)

    writer.close()
    

def create_school_ranks_sheets(df):
    df_schools = get_school_stats(df)
    df_schools_champs = get_school_stats(df, champs=True)
    save_school_ranks_sheet(df_schools, df_schools_champs)

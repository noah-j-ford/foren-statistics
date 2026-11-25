import pandas as pd
from standardization import Standardizer
from config import YEAR, TOURNAMENTS, MOST_RECENT_TOURNAMENT, NO_JUDGE_SHEETS
std = Standardizer()

def get_tournament_list(judges=False):
    tournament_list = list(TOURNAMENTS[YEAR])  # get list of keys, not dict
    index = tournament_list.index(MOST_RECENT_TOURNAMENT)
    tournament_list = tournament_list[:index]
    if judges:
        for t in NO_JUDGE_SHEETS:
            try:
                tournament_list.remove(t)
            except ValueError:
                pass
    return tournament_list

def safe_to_numeric(col):
    """errors='ignore' is deprecated in pandas 3.0, i guess, so this is the equivalent"""
    try:
        return pd.to_numeric(col)
    except (ValueError, TypeError):
        return col

def create_container(columns):
    data = {}
    for c in columns:
        data[c] = []
    return data

def move_column(df, label, index):  # parse_results and parse_sections
    column = df.pop(f'{label}')
    df.insert(index, f'{label}', column)
    return df

def drop_speechwire_rows(df):  # parse_results and parse_sections
    df = df[df[0].str.contains("© 2004-")==False]
    df = df[df[0] != "This tournament is being run using SpeechWire Tournament Services software - www.SpeechWire.com."]
    df.reset_index(drop=True, inplace=True)
    return df


def create_event_column_list(df, tournament_name):  # parse_results and parse_sections
    event_column_list, event_name = [[],""]
    for i, row in df.iterrows():
        cell = row[0]
        if cell == tournament_name:
            event_name = std.standardize_event_name(df[0][i+1], keep_novice=True)
        event_column_list.append(event_name)
    return event_column_list


def drop_novice_sections(df):
    return df[~df['Event'].astype(str).str.startswith('N-')]

def drop_unified_speech(df):
    return df[df['Event'] != 'Unified Speech']

def drop_headers(df, first_column_text):
    return df[df.iloc[:, 0] != first_column_text]

def drop_nan_rows(df, column):
    return df[df.iloc[:, column].notna()]

def drop_event_header(df):
    return df[~df.iloc[:, 0].map(std.is_event_name)]

def drop_unneeded_rows(df, tournament_name, mode):  # parse_results and parse_sections
    first_table_header = 'Code' if mode == 'results' else 'Sect.'

    df = drop_novice_sections(df)
    df = drop_unified_speech(df)
    df = drop_headers(df, tournament_name)
    df = drop_headers(df, first_table_header)  #"Code" results, "Sect." sections
    if mode == 'results':
        df = drop_nan_rows(df, 0)
        # don't drop nan's in first column for sections because that would drop 2 finals judges 
        # (first column has "FINAL"-nan-nan)
    df = drop_nan_rows(df, 1)
    df = drop_event_header(df)
    df.reset_index(drop=True, inplace=True)
    return df


def add_header_row(df):
    df.loc[-1] = df.columns.to_list() # adding a row
    df.index = df.index + 1  # shifting index
    df.sort_index(inplace=True)  # sorting by index
    return df

def evaluate_tournament_toc_score(x):
    if x == 0:
        return 0
    if x < 20:
        return 1
    if 35 > x >= 20:
        return 2
    if 50 > x >= 35:
        return 3
    if 70 > x >= 50:
        return 4
    if 100 > x >= 70:
        return 5
    if x>=100:
        return 6
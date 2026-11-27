"""
Uses:
    Competitor Stats.xlsx
    
Creates:
    Depth Chart.xlsx
    Depth Chart (Statewide).xlsx
"""
import warnings
import pandas as pd
from standardization import Standardizer
from config import ROOT, YEAR
from formatting import write_sheet
warnings.filterwarnings('ignore')
std = Standardizer()

def calculate_depth_points(df):
    """
    Depth Points:
        (6-Avg Prelim Rank+1) * Prelim Rounds + 
        (6-Avg Champs Rank+1) * Champs Breaks +
        2(Champs Breaks) + (Honors Breaks)
    """
    
    for col in ['1s', '2s', '3s', '4s', '5s', '6s', 'AvgChampsPlacement', 'ChampsTotal']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Depth Points'] = (
        df['1s']*6 + 
        df['2s']*5 + 
        df['3s']*4 +
        df['4s']*3 + 
        df['5s']*2 + 
        df['6s']*1
    )
    df['Champs Points'] = round((6-df['AvgChampsPlacement']+1)*df['ChampsTotal']).fillna(0)
    df['Depth Points'] = df['Depth Points'] + df['Champs Points']

    df['HonorsTotal'] = df['BreakTotal'] - df['ChampsTotal']
    df['Depth Points'] = df['Depth Points'] + df['ChampsTotal']*2 + df['HonorsTotal']

    df['Depth Points'] = pd.to_numeric(df['Depth Points'], errors='coerce')
    return df

def drop_dropped_students(df):
    df = df[~df['Competitor'].astype(str).isin(std.dropped[YEAR].dropna())]
    df.reset_index(drop=True, inplace=True)
    return df

def save_depthchart(df, only_mn=True):
    if only_mn:
        df = drop_dropped_students(df)
    
    statewide = "" if only_mn else " (Statewide)"
    writer = pd.ExcelWriter(ROOT + rf'\Depth Chart{statewide}.xlsx', engine='xlsxwriter')
    
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        df['Competitor'] = df['Competitor'].apply(std.standardize_name)
        df_event.rename({'Competitor': event_name}, axis=1, inplace=True)
        df_event.drop(['Event'], axis=1, inplace=True)
        df_event.sort_values(['Depth Points','Average Rank'],
                             ascending=[False, True],
                             inplace=True)
        write_sheet(writer, df_event, event_name, layout="depth_chart", index=False)
    writer.close()

def attach_elo_scores(df, df_elo, only_mn):
    if only_mn:
        df_elo = df_elo[df_elo['Tm'] == 'MN'].reset_index(drop=True)
        
    df_elo['ID'] = df_elo['Competitor']+df_elo['Event']
    df_elo.index = df_elo['ID']
    data = df_elo[['ELO']].to_dict()['ELO']
    
    df['ID'] = df['Competitor']+df['Event']
    df['ELO'] = df['ID'].map(data)
    df.drop(['ID'], axis=1, inplace=True)
    return df

def clean_for_display(df):
    """
    Rounds = "Ballots" (my number is prelim ballots. it is correct.)
    Total Rank = AvgRk * Ballots
    Average Rank = AvgRk
    Finals = "ChampsTotal"
    Total Rank = ChampsTotal * (AvgChampsRk*3)
    Average Rank = "AvgChampsRk"
    Total Entries = "TournamentTotal"
    Break% = "Champs%"
    """
    df.drop(['HonorsTotal','BreakTotal','1s','2s','3s','4s','5s','6s','Break%'],
            axis=1, inplace=True)
    df = df.reindex(
        ['Event', 'Competitor', 'Depth Points', 'Ballots', 'Total Rank', 'AvgRk', 'ChampsTotal',
         'Total Champs Rank', 'AvgChampsPlacement', 'TournamentTotal', 'Champs%'],
        axis=1)
    df.rename(
        {'Ballots':'Rounds',
        'AvgRk':'Average Rank',
        'AvgChampsPlacement': 'Average Rank (F)',
        'ChampsTotal':'Finals',
        'Total Champs Rank':'Total Rank (F)',
        'TournamentTotal':'Total Entries',
        'Champs%':'Break %'},
        axis=1, inplace=True)
    return df

def make_depth_chart(df, df_elo, only_mn=True):
    if only_mn:
        df = df[df['Tm'] == 'MN'].reset_index(drop=True)
    df = df[['Event', 'Competitor','Champs%','Break%','AvgRk','AvgChampsPlacement',
             'TournamentTotal','BreakTotal','ChampsTotal','Ballots',
             '1s','2s','3s','4s','5s','6s']]
    df['Total Rank'] = round(df['AvgRk'] * df['Ballots'])
    df['Total Champs Rank'] = round(df['ChampsTotal'] * df['AvgChampsPlacement'])
    df = calculate_depth_points(df)
    df = clean_for_display(df)    
    df = attach_elo_scores(df, df_elo, only_mn)
    save_depthchart(df, only_mn)

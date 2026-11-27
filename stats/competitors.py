"""
Uses:
    -Results by Entry.xlsx     [fka: Results.xlsx]
        11/12/26 I believe this is not saved yet at this point in execution?
    
Creates:
    -Stats by Competitor.xlsx  [fka: Competitor Stats.xlsx]
"""
import re
import warnings
import pandas as pd
import numpy as np
from standardization import Standardizer
import stats.depthchart as dpt
from config import ROOT
from utils import evaluate_tournament_toc_score
from formatting import write_sheet
warnings.filterwarnings('ignore')
std = Standardizer()


#### So much processing.
def group_events_by_tournament(df):
    df_tournaments = pd.DataFrame()
    tournament_groups = df.groupby('Tournament')
    for tournament_name, df_tournament in tournament_groups:
        event_groups = df_tournament.groupby('Event')
        for event_name, df_event in event_groups:
            df_event['EntrySize'] = len(df_event)
            df_event['Outperformed'] = df_event['EntrySize']-df_event['FinalResult']
            df_event['Percentile'] = round(df_event['FinalResult']/df_event['EntrySize']*100, 2)
            df_tournaments = pd.concat([df_tournaments, df_event],axis=0)
    return df_tournaments

def group_competitors_by_tournament(df):  # Claude
    df = df.sort_values(['Tournament', 'Competitor'], kind='stable')
    df['IEs'] = df.groupby(['Tournament', 'Competitor'])['Tournament'].transform('size')
    return df

def get_competitor_stats_by_event(df):
    df_competitors = pd.DataFrame()
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        data = {}
        df_event.sort_values(['INDEX'], ascending=False, inplace=True)
        columns = {'TournamentTotal':[], 'BreakTotal':[], 'ChampsTotal':[], 'Break%':[],
                   'Champs%':[], 'AvgRk':[], 'AvgChampsRk':[], 'AvgPercentile':[], 
                   'AvgOutperformed':[], 'AvgChampsPlacement':[], '1s':[], '2s':[],
                   '3s':[], '4s':[], '5s':[], '6s':[], '1%':[], '2%':[], '3%':[], '4%':[],
                   '5%':[], '6%':[], 'Up%':[], 'Ballots':[], 'AvgFinalResult':[],
                   'AvgEntrySize':[], 'TOCPtsTotal':[], 'AvgTOCPts':[]} # !!!
        # for i in df_event.index.to_list():
        for i, row in df_event.iterrows():
            competitor_name = row['Competitor']
            if competitor_name not in data:
                data.update({competitor_name:
                {'TournamentTotal':0, 'BreakTotal':0, 'ChampsTotal':0, 'TOCPtsTotal':0,
                 'AvgTOCPts':0, 'AvgRk':0, 'AvgChampsRk':0,'AvgPercentile':0,
                 'AvgOutperformed':0, 'AvgFinalResult':0, 'AvgEntrySize':0,
                 'AvgChampsPlacement':0,
                 'Break%':0,'Champs%':0,
                 '1s':0,'2s':0,'3s':0,'4s':0,'5s':0,'6s':0,
                 '1%':0,'2%':0,'3%':0,'4%':0,'5%':0,'6%':0,'Up%':0,'Ballots':0,
                 'RankList':[],'BreakList':[],'ChampsRkList':[],'PercentileList':[],
                 'OutperformedList':[],'FinalResultList':[],'EntrySizeList':[],
                 'TOCPtsList':[],'ChampsPlacementList':[]}})  # !!!
        #### RANKS
            data[competitor_name]['TournamentTotal'] += 1
            for rd in ['P1','P2','P3','P4','P5','P6']:
                # print(rd, event_name, competitor_name, row[rd])
                try:
                    rk = row[rd]
                    if pd.notna(rk):
                        data[competitor_name]['RankList'].append(int(rk))
                except KeyError:
                    pass
            data[competitor_name]['AvgRk'] = round(np.mean(
                data[competitor_name]['RankList']),3)
        #### BREAKS
            if row['Break'] >= 1:
                data[competitor_name]['BreakTotal'] += 1
            data[competitor_name]['BreakList'].append(row['Break'])
            data[competitor_name]['Break%'] = round(
                data[competitor_name]['BreakTotal']/data[competitor_name]['TournamentTotal']*100,2)
        #### CHAMPS
            if row['Break'] == 1:
                data[competitor_name]['ChampsTotal'] += 1
                for judge in ['F1','F2','F3','F4','F5']:
                    try:
                        rk = int(row[judge])
                        data[competitor_name]['ChampsRkList'].append(rk)
                    except (ValueError, TypeError):
                        pass
            data[competitor_name]['AvgChampsRk'] = round(np.mean(data[competitor_name]['ChampsRkList']),3) 
            data[competitor_name]['Champs%'] = round(data[competitor_name]['ChampsTotal']/data[competitor_name]['TournamentTotal']*100,2)
        #### 1/2/3/4/5/6s
            #Counts
            
            for j in range(1,6):
                data[competitor_name][f'{j}s'] = data[competitor_name]['RankList'].count(j)
            data[competitor_name]['6s'] = data[competitor_name]['RankList'].count(6) + data[competitor_name]['RankList'].count(7) + data[competitor_name]['RankList'].count(8)
            data[competitor_name]['Ballots'] = data[competitor_name]['1s'] + data[competitor_name]['2s'] + data[competitor_name]['3s'] + data[competitor_name]['4s'] + data[competitor_name]['5s'] + data[competitor_name]['6s']
            #Percents
            for num in ['1','2','3','4','5','6']:
                try:
                    data[competitor_name][f'{num}%'] = round(data[competitor_name][f'{num}s']/len(data[competitor_name]['RankList'])*100,2)
                except ZeroDivisionError:
                    data[competitor_name][f'{num}%'] = 0
            data[competitor_name]['Up%'] = data[competitor_name]['1%']+ data[competitor_name]['2%'] + data[competitor_name]['3%']
        #### Strength
            for var in ['FinalResult', 'Percentile', 'Outperformed', 'EntrySize']:
                data[competitor_name][f'{var}List'].append(row[var])
                data[competitor_name][f'Avg{var}'] = round(np.mean(data[competitor_name][f'{var}List']),3)
            #ChampsPlacement
            if pd.notna(row['Champs_Rd_Rk']):
                data[competitor_name]['ChampsPlacementList'].append(row['Champs_Rd_Rk'])
            data[competitor_name]['AvgChampsPlacement'] = round(np.mean(data[competitor_name]['ChampsPlacementList']),3)
            
        #### Tournament SOS
            if event_name == 'DUO':
                multiplier=2
            elif event_name == 'OID':
                multiplier=4
            else:
                multiplier=1
            entry_size_toc = df_event['EntrySize'][i]*multiplier
            toc_pt = evaluate_tournament_toc_score(entry_size_toc)
            data[competitor_name]['TOCPtsList'].append(toc_pt)
            data[competitor_name]['TOCPtsTotal'] = sum(data[competitor_name]['TOCPtsList'])
            data[competitor_name]['AvgTOCPts'] = round(np.mean(data[competitor_name]['TOCPtsList']),3)
            
            for stat in data[competitor_name]:
                if stat not in ['RankList', 'BreakList', 'ChampsRkList',
                                'PercentileList', 'OutperformedList', 'FinalResultList', 
                                'EntrySizeList', 'TOCPtsList', 'ChampsPlacementList']:
                    columns[stat].append(data[competitor_name][stat])           
        for column, data in columns.items():
            df_event[column] = data
        df_competitors = pd.concat([df_competitors,df_event],axis=0)
    return df_competitors

def calculate_average_champs_placement(df):
    data = []
    for i, row in df.iterrows():
        if row['Break'] == 1:
            data.append(row['Final_Rd_Rk'])
        else:
            data.append(np.nan)
    df['Champs_Rd_Rk'] = data
    return df

def save_results_by_entry(df):
    #### Need to adjust column widths for F4, F5 (maybe?)
    writer = pd.ExcelWriter(ROOT + r'\Results by Entry.xlsx', engine='xlsxwriter')
    write_sheet(writer, df, 'Results', layout="results_by_entry", index=False)
    writer.close()

def get_expanded_stats(df):
    #Takes DUO/OID and sorts members alphabetically, reduces into comma-separated lists
    df['Competitor'] = df.Competitor.apply(
        lambda x: ', ' .join(
            sorted(re.split(' and |, ',x))
            )
        ).replace(' , ',', ')
    #Standardize capitalization
    df['Competitor'] = df['Competitor'].str.title()  # !!! This kills Mc names!
    #Standardize Competitor Names  (including OIDs)
    df['Competitor'] = df['Competitor'].apply(std.standardize_name)
    
    #Clean school names, Districts, Class
    df['Tm'] = df['Tm'].apply(std.standardize_school_name)
    df['Class'] = df['Tm'].map(std.classes)
    df['District'] = df['Tm'].map(std.districts)
    
    #For depth chart purposes
    df = calculate_average_champs_placement(df)
    
    df = group_events_by_tournament(df)
    df = group_competitors_by_tournament(df)
    df = get_competitor_stats_by_event(df)

    stat_order = [
        'INDEX', 'Tournament', 'Event', 'Code', 'Tm', 'District', 'Class', 'Competitor', 'P1', 'P2', 
        'P3', 'Cume_P', 'OppAvgRk', 'Recips_P', 'PrelimResult', 'F1', 'F2', 'F3', 'Cume_F', 
        'Recips_F', 'Final_Rd_Rk', 'Champs_Rd_Rk', 'FinalResult', 'Break', 'Outperformed', 
        'Percentile', 'EntrySize', 'OppBeat', 'Ballots', 'AvgRk', 'AvgChampsRk', 'Break%',
        'Champs%', 'Up%', '1%', '2%', '3%', '4%', '5%', '6%', '1s', '2s', '3s', '4s', '5s', '6s',
        'TournamentTotal', 'BreakTotal', 'ChampsTotal', 'TOCPtsTotal', 'AvgTOCPts', 'AvgPercentile',
        'AvgOutperformed', 'AvgFinalResult', 'AvgChampsPlacement', 'AvgEntrySize', 'P4', 'P5', 'P6',
        'F4', 'F5', 'S1', 'S2', 'S3', 'Cume_S', 'Recips_S', 'Semi_Rd_Rk', 'Cume_ST', 'Recips_ST',
        'Semi_Result', 'Semi_Sec', 'Cume_TOTAL', 'Recips_TOTAL', 'IEs', 'Div',
        ]
    df = df.reindex(columns=stat_order)
    return df

def get_competitor_stats_and_scores(df):
    #Drop single tournament stats
    df.drop(['Tournament','EntrySize','Break','Percentile','P1','P2','P3','P4',
             'P5','P6','Cume_P','Recips_P','PrelimResult','F1','F2','F3',
             'F4','F5','Cume_F','Recips_F', 'Final_Rd_Rk', 'Champs_Rd_Rk',
             'FinalResult','OppBeat','OppAvgRk',
             'S1','S2','S3','Cume_S','Semi_Rd_Rk','Recips_S','Cume_ST','Recips_ST',
             'Semi_Result','Semi_Sec','Cume_TOTAL','Recips_TOTAL','Code'],
            axis=1, inplace=True)
    columns = df.columns.to_list()
    columns.append('TotalOutperformed')
    df_competitors = pd.DataFrame()
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        competitor_groups = df_event.groupby('Competitor')
        for competitor_name, df_competitor in competitor_groups:
            df_competitor.sort_values(by=['INDEX'], inplace=True)
            df_competitor['IEs'] = max(df_competitor['IEs'].to_list())
            df_competitor['TotalOutperformed'] = sum(
                df_competitor['Outperformed'].to_list())
            division = df_competitor['Div'].to_list()
            if 'Novice' in division:
                df_competitor['Div'] = 'Novice'
            elif 'Varsity' in division:
                df_competitor['Div'] = 'Varsity'
            else:
                df_competitor['Div'] = ''   
            df_temp = pd.DataFrame(df_competitor.iloc[0].values.reshape(1, len(
                df_competitor.columns)))
            df_competitors = pd.concat([df_competitors, df_temp], axis=0)
    df_competitors.columns = columns
    df_competitors.reset_index(drop=True,inplace=True)
    
    df_competitors = dpt.calculate_depth_points(df_competitors)
    df_competitors['Depth Points'] = round(df_competitors['Depth Points'])
    df_competitors.rename({'Depth Points':'DepthPts'}, axis=1, inplace=True)
    
    df_competitors.drop(['INDEX','Outperformed','Champs Points', 'HonorsTotal'],
                        axis=1, inplace=True)
    return df_competitors

def create_stats_by_competitor(df):
    df = get_expanded_stats(df)
    save_results_by_entry(df)
    df = get_competitor_stats_and_scores(df)
    df.to_excel(ROOT + r'\Stats by Competitor.xlsx', index=False) 
    return df

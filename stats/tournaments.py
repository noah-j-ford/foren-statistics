"""
Uses:
    -Results by Entry.xlsx     [fka: Results.xlsx]
    
Creates:
    -Stats by Tournament.xlsx  [fka: Tournament Sizes.xlsx]
"""

import pandas as pd
from config import YEAR, ROOT, EVENT_LIST, TOURNAMENTS
from utils import evaluate_tournament_toc_score

def count_unique_values(df, col):
    return len(set(df[col]))


def get_nietoc_scores(df):
    for event_name in EVENT_LIST:
        data = []
        for i, row in df.iterrows():
            x = row[event_name]
            if event_name == 'OID':
                x = x*4
            elif event_name == 'DUO':
                x = x*2
            x = evaluate_tournament_toc_score(x)
            data.append(x)
        df[event_name+'Pt'] = data    
    return df


def get_tournament_stats(df):
    tournament_groups = df.groupby('Tournament')
    data = {}
    for tournament_name, df_tournament in tournament_groups:
        data.update(
                {tournament_name: {
                    'Order':0, 'Schools':0, 'Competitors':0, 'Entries':0, 
                    'EXT':0, 'IMP':0, 'OO':0, 'INF':0, 'ENT':0, 'HI':0, 
                    'DI':0, 'POE':0, 'POI':0, 'DUO':0, 'OID':0,
                    }
                }
            )
        
        data[tournament_name]['Order'] = TOURNAMENTS[YEAR].get(tournament_name)                                                                        
        data[tournament_name]['Schools'] = count_unique_values(df_tournament, 'Tm')
        data[tournament_name]['Competitors'] = count_unique_values(df_tournament, 'Competitor')
        data[tournament_name]['Entries'] = len(df_tournament['Competitor'])
        
        event_groups = df_tournament.groupby('Event')
        for event_name in EVENT_LIST:
            try:
                df_event = event_groups.get_group(event_name)
                entry_size = df_event['EntrySize'].to_list()[0]
                data[tournament_name][event_name] = entry_size
            except KeyError:
                pass
    df_tournaments = pd.DataFrame(data).transpose()
    df_tournaments.sort_values(['Order'], inplace=True)
    df_tournaments = get_nietoc_scores(df_tournaments)
    return df_tournaments

def create_stats_by_tournament(df):
    df_tournaments = get_tournament_stats(df)
    df_tournaments.to_excel(ROOT + r'\Code\Stats by Tournament.xlsx')
"""
Uses:
    Competitor Stats.xlsx
    Sections (ELO).xlsx
    Results.xlsx
    Sections (Master).xlsx
    *Competitor Stats ({most_recent_tournament}).xlsx
    *Sections (ELO) ({most_recent_tournament}).xlsx
    
Updates:
    Sections by Room.xlsx             [fka: Sections (ELO).xlsx]

Creates:
    ELO.xlsx
    ELO ({most_recent_tournament}).xlsx
    
"""

import os
import pandas as pd
from multielo import MultiElo, Player
from config import EVENT_LIST, ROOT, YEAR, TOURNAMENTS, BASE_RATING, K_VALUE, D_VALUE, EXP
from formatting import write_sheet
import utils as util

def map_tournament_order_onto_spreadsheet(df):
    df['Tournament_ID'] = df['Tournament'].map(TOURNAMENTS[YEAR])
    df.sort_values(by=['Tournament_ID', 'Event', 'Round', 'Sect.'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def create_elo_sections_sheet(df_results, df_sections):
    df_results['Code'] = df_results['Code'].astype(str)
    # after changing the pipeline to minimize excel read/writes, Unique_ID broke because Tournament
    # was changed to `category` dtype somewhere earlier
    df_results['Tournament'] = df_results['Tournament'].astype(str)
    df_results['Unique_ID'] = df_results['Tournament']+df_results['Event']+df_results['Code']
    id_dict = pd.Series(df_results.Competitor.values, index=df_results.Unique_ID).to_dict()

    df_sections = map_tournament_order_onto_spreadsheet(df_sections)    
    for num in [f'{i+1}' for i in range(8)]:
        df_sections[f'Sp{num}'] = df_sections[f'Sp{num}'].fillna('').astype(str)
        df_sections[f'ID{num}'] = df_sections['Tournament'] + df_sections['Event'] + df_sections[f'Sp{num}']
    for num in [f'{i+1}' for i in range(8)]:  
        df_sections[f'Name{num}'] = df_sections[f'ID{num}'].map(id_dict)
    
    cols = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'F1', 'F2', 'F3', 'F4', 'F5', 'S1', 'S2', 'S3']
    data = df_results.set_index('Unique_ID')[cols].to_dict()
    
    ranks = {
        'RkA': util.create_container('12345678'),
        'RkB': util.create_container('12345678'),
        'RkC': util.create_container('12345678'),
        }

    for i, row in df_sections.iterrows():
        rd, sect, tournament_name, judge_count = [row['Round'], row['Sect.'], row['Tournament'], row['JudgeCount']]
        ########### FINALS ###################3
        if rd == 'Final':
            for num in ranks['RkA']: #1, 2, 3, 4, 5, 6, 7, 8
                try:
                    ranks['RkA'][num].append(data['F1'][row[f'ID{num}']])
                except KeyError: #Finals section is smaller than 8
                    ranks['RkA'][num].append('')
            if sect == 'Champs':
                for num in ranks['RkA']:
                    try:
                        ranks['RkB'][num].append(data['F2'][row[f'ID{num}']])                           
                    except KeyError:
                        ranks['RkB'][num].append('')
                    try:
                        ranks['RkC'][num].append(data['F3'][row[f'ID{num}']])
                    except KeyError:
                        ranks['RkC'][num].append('')
            else:
                for num in ranks['RkA']: #Blank out B and C ranks, the round only has one ballot
                    ranks['RkB'][num].append('')
                    ranks['RkC'][num].append('')  
        elif rd == 'Semifinal':
            for num in [f'{i+1}' for i in range(8)]:
                try:
                    ranks['RkA'][num].append(data['S1'][row[f'ID{num}']])
                    ranks['RkB'][num].append(data['S2'][row[f'ID{num}']])
                    ranks['RkC'][num].append(data['S3'][row[f'ID{num}']])
                except KeyError:
                    ranks['RkA'][num].append('')
                    ranks['RkB'][num].append('')
                    ranks['RkC'][num].append('')

        ###################
        elif judge_count == 1:
            if tournament_name not in ['LSW', 'Millard South']:#Flighted tournaments which had 2 judges in the first round of at least 1 event
                for num in ranks['RkA']:
                    ranks['RkB'][num].append('')
                    ranks['RkC'][num].append('')
                    try:
                        ranks['RkA'][num].append(data[f'P{rd}'][row[f'ID{num}']])
                    except KeyError:
                        ranks['RkA'][num].append('') 
            elif str(rd) == '1': #If round == 1 and judge_count == 1, that is always P1.
                for num in ranks['RkA']:
                    ranks['RkB'][num].append('')
                    ranks['RkC'][num].append('')
                    try:
                        ranks['RkA'][num].append(data['P1'][row[f'ID{num}']])
                    except KeyError:
                        ranks['RkA'][num].append('') 
            else: #It's not round 1 at a double-judge-round tournament and judge_count is 1.
                #if there is one judge in round __ at tournament ___, then I can assume P3.
                #I'm still manually assisting with what tournament is flighted or not, but...
                for num in ranks['RkA']:
                    ranks['RkB'][num].append('')
                    ranks['RkC'][num].append('')
                    try:
                        ranks['RkA'][num].append(data['P3'][row[f'ID{num}']])
                    except KeyError:
                        ranks['RkA'][num].append('') 
        elif tournament_name in ['NQ_N','NQ_S', 'NQ_N DX', 'NQ_S DX']:
            data_keys = {'1': ('P1', 'P2'), '2': ('P3', 'P4'), '3': ('P5', 'P6')}
            for num in ranks['RkA']:
                ranks['RkC'][num].append('')
                if rd in data_keys:
                    try:
                        ranks['RkA'][num].append(data[data_keys[rd][0]][row[f'ID{num}']])
                        ranks['RkB'][num].append(data[data_keys[rd][1]][row[f'ID{num}']])
                    except KeyError:
                        ranks['RkA'][num].append('')
                        ranks['RkB'][num].append('')
                
        elif judge_count == 2: #There are two judges in this round. It is not a final.
            data_keys = {'1': ('P1', 'P2'), '2': ('P2', 'P3')}
            for num in ranks['RkA']:
                ranks['RkC'][num].append('')
                if str(rd) in data_keys:
                    try:
                        ranks['RkA'][num].append(data[data_keys[str(rd)][0]][row[f'ID{num}']])
                        ranks['RkB'][num].append(data[data_keys[str(rd)][1]][row[f'ID{num}']])
                    except KeyError:
                        ranks['RkA'][num].append('')
                        ranks['RkB'][num].append('')
        else:
            print("ERROR?: ", tournament_name, rd, sect, judge_count)

    rank_a = pd.DataFrame(ranks['RkA'])   
    rank_a.columns = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8']             
    rank_b = pd.DataFrame(ranks['RkB'])   
    rank_b.columns = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8'] 
    rank_c = pd.DataFrame(ranks['RkC']).fillna('')
    rank_c.columns = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8']  
    df = pd.concat([df_sections, rank_a, rank_b, rank_c],axis=1)    
    df = map_tournament_order_onto_spreadsheet(df)
    df.to_excel(ROOT + r'\Code\Sections by Room.xlsx', index=False)
    return df


def create_full_competitor_dict(df):
    elo_data = {e: {} for e in EVENT_LIST}
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        for i, row in df_event.iterrows():
            player_temp = Player(row['Competitor'], rating=BASE_RATING)
            elo_data[event_name].update({row['Competitor']:player_temp})
    return elo_data    

def initialize_elo():
    Elos = {}
    Elos['Elo'] = MultiElo(k_value=K_VALUE,
                   d_value=D_VALUE, 
                   score_function_base=EXP)
    
    Elos['StableElo'] = MultiElo(k_value=(K_VALUE*.75), 
                         d_value=D_VALUE, 
                         score_function_base=EXP)
    
    Elos['ChampsElo'] = MultiElo(k_value=K_VALUE/3,
                         d_value=D_VALUE,
                         score_function_base=EXP)
    
    Elos['StableChampsElo'] = MultiElo(k_value=(K_VALUE*.75)/3,
                               d_value=D_VALUE,
                               score_function_base=EXP)
    
    return Elos

def calculate_elo_scores(df, elo_data, Elos):
    # Yeah so the issue here is that you fill all the blanks when creating the sheet with
    # blank strings ('') instead of np.nan so the columns are strings, but before when you saved
    # and then reloaded that pandas just reads in the blank cells assuming as nan and its fine
    # TL;DR - fix the ''s
    df = pd.read_excel(ROOT + r'\Code\Sections by Room.xlsx')
    largest_section_size = len(df.filter(regex='Sp').columns)
    for i, row in df.iterrows():
        event_name, tournament_id = [row['Event'], row['Tournament_ID']]
        if tournament_id: #in [...]: #This was the "Select Tournaments" portion
            data = util.create_container(['Name', 'A', 'B', 'C'])
            for j in [f'{k+1}' for k in range(largest_section_size)]:
                for column in ['Name','A','B','C']:
                    if row[f'{column}{j}'] == row[f'{column}{j}']:
                        data[column].append(row[f'{column}{j}'])
            for ballot in [data['A'],data['B'],data['C']]:
                if len(ballot) > 0:
                    current_elo = {}
                    for j in range(0,len(data['Name'])):
                        Player = elo_data[event_name][data['Name'][j]]
                        current_elo.update({data['Name'][j]:Player.rating})
                    competitor_rank_order = [x for _, x in sorted(zip(ballot, data['Name']))]
                    
                    ordered_elo = [x for _, x in sorted(zip(ballot, current_elo.values()))]
                    if row['Sect.'] == 'Champs':
                        new_elo = Elos['ChampsElo'].get_new_ratings(ordered_elo)
                        new_stable_elo = Elos['StableChampsElo'].get_new_ratings(ordered_elo)
                    else:
                        new_elo = Elos['Elo'].get_new_ratings(ordered_elo)
                        new_stable_elo = Elos['StableElo'].get_new_ratings(ordered_elo)
                        
                    for j in range(0,len(competitor_rank_order)):
                        Player = elo_data[event_name][competitor_rank_order[j]]
                        selected_new_elo = new_stable_elo[j] if Player.count_games() >= 20 else new_elo[j]
                        if row['Sect.'] in ['Champs', 'Honors', 'Merit', 'Consi', 'Semis']:
                            if selected_new_elo > Player.rating: # ONLY if the ELO was boosted by the round
                                Player.update_rating(selected_new_elo, date=tournament_id)
                            else:  
                                Player.update_rating(Player.rating, date=tournament_id)
                        else:
                            Player.update_rating(selected_new_elo, date=tournament_id)
    return elo_data

def create_elo_spreadsheet(elo_data):
    data = util.create_container(['Event', 'Competitor', 'ELO', 'Ballots'])
    for event_name, competitor_dict in elo_data.items():
        for competitor_name, competitor in competitor_dict.items():
            data['Event'].append(event_name)
            data['Competitor'].append(competitor_name)
            data['ELO'].append(competitor.rating)
            data['Ballots'].append(competitor.count_games())
    df_elo = pd.DataFrame(data)
    df_elo.sort_values(by=['Event', 'ELO', 'Ballots'],
                       ascending=[True, False, False], inplace=True)
    return df_elo

def expand_elo_stats(df_elo, df_competitors):
    df_elo['ID'] = df_elo['Competitor'] + df_elo['Event']
    df_team = df_competitors.loc[:, ['Competitor','Tm','Class','District']]
    df_team.index = df_team['Competitor']
    df_team.drop(['Competitor'],axis=1,inplace=True)
    for column in df_team.columns:
        data = df_team[[column]].to_dict()[column]
        df_elo[column] = df_elo['Competitor'].map(data)
        
    df_stats = df_competitors.loc[:, ['Competitor', 'Event', 'AvgRk', 'AvgChampsRk', 'Up%', 'Break%', 'DepthPts']]
    df_stats['ID'] = df_stats['Competitor']+df_stats['Event']
    df_stats.index = df_stats['ID']
    df_stats.drop(['ID','Competitor','Event'], axis=1, inplace=True)
    for column in df_stats.columns:
        data = df_stats[[column]].to_dict()[column]
        df_elo[column] = df_elo['ID'].map(data)
    df_elo.drop(['ID'],axis=1,inplace=True)
    
    df_elo = df_elo[['Event', 'Competitor', 'Tm', 'ELO', 'Ballots', 'AvgRk', 'AvgChampsRk', 'Up%', 'Break%', 'DepthPts', 'Class', 'District']]
    return df_elo


def convert_table_to_integers(df):
    df.columns = df.iloc[0]
    df.set_index(df[0], inplace=True)
    df.drop([0], axis=1, inplace=True)
    df.drop([0], axis=0, inplace=True)
    df = df.astype('float64')
    return df

def calculate_winpct(prelims=False):
    df = pd.DataFrame()
    if prelims:
        directory = ROOT + r'\Code\H2H\All Classes (Prelims)'
    else:
        directory = ROOT + r'\Code\H2H\All Classes'
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            # 2/23/26: I'm contemplating reworking this to just calculate exclusively from 
            # the "Wins" sheet? Somebody's row total = wins, column total = losses, so
            # row + column = total and row / total = win%? I feel like that looks simpler.
            event_name = file.replace('.xlsx','')
            path = os.path.join(subdir,file)
             
            df_percent = convert_table_to_integers(pd.read_excel(
                path, sheet_name='WinPct', header=None))
            df_meetings = convert_table_to_integers(pd.read_excel(
                path, sheet_name='Meetings', header=None))
            df_winpct = pd.DataFrame()
            df_winpct['Competitor'] = df_percent.index
            df_winpct['Event'] = event_name
            weights = []     
            
            for i in df_meetings.index:
                win_percents, meetings = [df_percent.loc[i,:], df_meetings.loc[i,:]]
                if meetings.sum() != 0:
                    weight = ((win_percents*meetings).sum()/meetings.sum()).round(2)
                else:
                    weight = 0
                weights.append(weight)

            df_winpct['Win%'] = weights                
            df_winpct = df_winpct[['Event', 'Competitor', 'Win%']]
            df = pd.concat([df, df_winpct],axis=0)
    df.sort_values(by=['Event', 'Competitor'], ascending=[True, True], inplace=True)
    df.reset_index(drop=True,inplace=True)
    return df

def add_winpct(df_elo):
    # Calculate win percentage values (in dataframes)
    df_winpct = calculate_winpct()   
    df_prelim_winpct = calculate_winpct(prelims=True)
    
    # Sort df_elo to be alpha by competitor within each event (so it matches winpct dfs),
    df_elo.sort_values(by=['Event', 'Competitor'], ascending=[True, True], inplace=True)
    # Add Win% and Prelim Win% columns into df_elo
    for variable, df in {'Win%':df_winpct, 'Pre%':df_prelim_winpct}.items():
        df_elo[variable] = df['Win%']
    # Revert df_elo's sorting to be by ELO again rather than alpha
    df_elo.sort_values(by=['Event', 'ELO', 'Ballots'], 
                       ascending=[True, False, False], inplace=True)
    return df_elo
    
def create_elo_tiers(df):
    tiers = {"F":  517,          # 0-517
             "D-": 610,          # 518-610
             "D":  750,          # 611-750
             "D+": 850,          # 751-850   manual break added
             "C-": 956,          # 851-956
             "C":  1023,         # 957-1023 
             "C+": 1132,         # 1024-1132
             "B-": 1229,         # 1133-1229
             "B":  1271,         # 1230-1271
             "B+": 1347,         # 1272-1347
             "A-": 1413,         # 1348-1413
             "A":  1488,         # 1414-1488
             "A+": 1600,         # 1489-1600
             "S":  1742,         # 1601-1742
             "S+": float("inf"), # 1742+
             } 
    tiers = [
        'F', 'D-', 'D', 'D+', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+', 'S', 'S+',
        ]
    cutoffs = [-float("inf"), 
        517, 610, 750, 850, 956, 1023, 1132, 1229, 1271, 1347, 1413, 1488, 1600, 1742,
        float('inf'),
        ]
    df['Tier'] = pd.cut(  # pd.cut is made for converting continuous -> ordinal data
        df['ELO'],                        # continuous variable to cut into discrete bins
        bins = cutoffs,                   # tier names (letter grades)            
        labels = tiers,                   # cutoff values (local minima values for tiers)
        right = True,                     # cutoff values are inclusive as a maximum; 
        include_lowest = True,            # lowest boundary (0) is included in bottom
        )
    
    return df

def save_elo_formatting(df, most_recent_tournament=False):
    for column in ['ELO','Up%','Break%']:
        df[column] = round(df[column])
    for column in ['AvgRk','AvgChampsRk']:
        df[column] = round(df[column],2)
    df = create_elo_tiers(df)
    df = df[['Event', 'Competitor', 'Tm', 'ELO', 'Ballots', 'AvgRk', 'AvgChampsRk', 'Up%', 'Break%',
             'Win%', 'Pre%', 'Class', 'District', 'Tier','DepthPts']]
    
    if not most_recent_tournament:
        writer = pd.ExcelWriter(ROOT + r'\ELO.xlsx', engine='xlsxwriter')
    else:
        writer = pd.ExcelWriter(ROOT + rf'\Code\ELO\ELO ({most_recent_tournament}).xlsx',
                                engine='xlsxwriter')
    write_sheet(writer, df, "ELO", layout="elo", index=False)
    return writer


def save_h2h_formatting(writer, df, event):
    df = df.T.reset_index().T  # turns column names into row
    df = df.reset_index()
    write_sheet(writer, df, event, layout="h2h_master", index=False, header=None)

def attach_h2h_data(writer):
    # Hi Noah. I'm choosing to store all dfs in this dictionary instead of replacing all
    # master[event_name]'s to a simple `df` for the sake of debugging. 
    # You can access everything in `master` at once; `df` would store one frame at a time.
    master = {}  
    for subdir, dirs, files in os.walk(ROOT + r'\Code\H2H\All Classes'):
        for file in files:
            event_name = file.replace('.xlsx','')
            path = os.path.join(subdir, file)
            data = {}
            for sheet in ['WinPct', 'Net', 'Meetings', 'Wins']:
                data[sheet] = pd.read_excel(path, sheet_name=sheet)
                data[sheet] = data[sheet].astype(str)
                data[sheet].index = data[sheet].columns[1:]
            master[event_name] = data['WinPct'] + ' / ' + data['Net'] + ' / ' + data['Meetings'] + ' / ' + data['Wins']
            master[event_name].drop([0], axis=1, inplace=True)
            master[event_name].replace('nan / 0 / 0 / 0', '-', inplace=True)
            
            save_h2h_formatting(writer, master[event_name], event_name)
            
    writer.close()

def run_elo(stats_by_competitor, sections_by_room, most_recent_tournament=False):
    Elos = initialize_elo()
    elo_data = create_full_competitor_dict(stats_by_competitor)
    elo_data = calculate_elo_scores(sections_by_room, elo_data, Elos)
    df_elo = create_elo_spreadsheet(elo_data)

    df_elo = expand_elo_stats(df_elo, stats_by_competitor)
    df_elo = add_winpct(df_elo)
    writer = save_elo_formatting(df_elo, most_recent_tournament=most_recent_tournament)
    attach_h2h_data(writer)
    return df_elo
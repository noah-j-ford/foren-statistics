"""
Uses:
    Results by Entry.xlsx         [fka: Master by Rounds.xlsx]
    ELO.xlsx
    H2H/All Classes/{event_name}.xlsx

Creates:
    H2H/All Classes/{event_name}.xlsx
    H2H/All Classes (Prelims)/{event_name}.xlsx
    H2H/Class A/{event_name}.xlsx
"""
import os
import copy
import pandas as pd
import numpy as np
from config import EVENT_LIST, ROOT, NE_NORTH_SCHOOLS
from formatting import write_sheet


def create_base_data(df_event):
    base_data = pd.DataFrame(set(df_event['Competitor']))  # gets unique competitors
    base_data.index = base_data[0]  # Set names as index
    base_data[0] = 0  # Set value for each name to 0
    base_data = base_data.to_dict()[0]  # convert back to dict
    return base_data
    
def collect_data():
    data = {e: {} for e in EVENT_LIST}
    df = pd.read_excel(ROOT + r'\Results by Entry.xlsx')
    df = df[['Competitor','Tournament','Event','Code','P1','P2','P3','F1','F2','F3','F4','F5','Sc1','Sc2','Sc3','ScF']]
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        base_data = create_base_data(df_event)
        event_data = base_data.copy()
        for i, row in df_event.iterrows():
            event_data[row['Competitor']] = base_data.copy()
        data[str(event_name)] = event_data
    # `data` is a blank dictionary of 11 dictionaries that are full of blank dictionaries for
    # every competitor with key/value pairs of `opponent:0`; 
    # ex {'OO':{'Noah Ford':{'Zoe Keese':0, 'Rahul Guda':0,}}} etc.
    return data

def run_pairwise_comparisons(df, data):
    prelim_data = copy.deepcopy(data) # data.copy() only copied the outer layer of the dict; .deepcopy() makes a copy of all nested dicts.
                                      # this was an issue because any time the inner competitor dicts of `data` were accessed, it updated
                                      # `prelim_data` anyways. This should solve that split... for this first time. Lol. You're welcome. ~2/22/26
    ballot_data = {'Sc1':['P1'], 'Sc2':['P2'], 'Sc3':['P3'],
                   'ScF':['F1','F2','F3','F4','F5'], 'ScS':['S1','S2','S3']}
    
    tournament_groups = df.groupby('Tournament')
    for tournament_name, df_tournament in tournament_groups:
        event_groups = df_tournament.groupby('Event')
        for event_name, df_event in event_groups:
            for section_name in ['Sc1','Sc2','Sc3','ScF','ScS']:
                section_groups = df_event.groupby(section_name)
                for section, df_section in section_groups:
                    df_section.reset_index(drop=True,inplace=True)
                    n_competitors = df_section.shape[0]
                    pairwise_matrix = np.zeros((n_competitors, n_competitors))
                    # iterate over every combination of candidates
                    for i in range(n_competitors):
                        for j in range(i+1, n_competitors):
                            # calculate the number of times candidate i was ranked higher than candidate j
                            i_better_count = 0
                            for k in range(len(ballot_data[section_name])): #1 should be number of judges
                                if df_section.loc[i,ballot_data[section_name][k]] < df_section.loc[j,ballot_data[section_name][k]]:
                                    i_better_count += 1
                            # add the result to the matrix
                            pairwise_matrix[i,j] = i_better_count
                            pairwise_matrix[j,i] = len(ballot_data[section_name]) - i_better_count
                    pairwise_df = pd.DataFrame(pairwise_matrix, index=df_section['Competitor'].values, columns=df_section['Competitor'].values)
                    for attacker in pairwise_df.index:
                        for defender in pairwise_df.columns:
                            data[event_name][attacker][defender] += int(pairwise_df.loc[attacker,defender])
                            if section_name in ['Sc1', 'Sc2', 'Sc3']:
                                prelim_data[event_name][attacker][defender] += int(pairwise_df.loc[attacker,defender])
    return data, prelim_data

def calculate_meetings(wins, wins_inv):
    return wins + wins_inv

def calculate_net_wins(wins, wins_inv):
    return wins - wins_inv
 
def calculate_win_pct(wins, meetings):
    return round((wins / meetings)*100)

def calculate_h2h_data_sheets(event_name, section_choice, data, prelim_data):
    data_sheets = {'WinPct':'', 'Net':'', 'Meetings':'', 'Wins':''}
    if section_choice == 'All':
        data_sheets['Wins'] = pd.DataFrame(
            data[event_name]).transpose().sort_index().sort_index(axis=1)
    else:
        data_sheets['Wins'] = pd.DataFrame(
            prelim_data[event_name]).transpose().sort_index().sort_index(axis=1)
                    
    wins_inv = data_sheets['Wins'].transpose()
    data_sheets['Meetings'] = calculate_meetings(data_sheets['Wins'], wins_inv)
    data_sheets['Net'] = calculate_net_wins(data_sheets['Wins'], wins_inv)
    data_sheets['WinPct'] = calculate_win_pct(data_sheets['Wins'], data_sheets['Meetings'])
    return data_sheets

def add_headers(data_sheets):
    header = pd.DataFrame(data_sheets['Wins'].columns).T
    header.columns = data_sheets['Wins'].columns
    for sheet in ['WinPct','Net','Meetings','Wins']:
        data_sheets[sheet] = pd.concat([header, data_sheets[sheet]], axis=0)
    return data_sheets

def save_h2h_excel(writer, data):
    for sheet in ['WinPct','Net','Meetings','Wins']:
        df = data[sheet].reset_index()
        if sheet == 'WinPct':
            write_sheet(writer, df, sheet, layout="h2h_winpct", index=False, header=None)
        else:
            write_sheet(writer, df, sheet, layout="h2h_counts", index=False, header=None)
    writer.close()

def h2h_event_sheets(data, prelim_data, NO_OID_FLAG=0):
    for event_name in data:
        if event_name == 'OID' and NO_OID_FLAG != 0:
            pass
        else:
            for section_choice in ['Prelims', 'All']:
                data_sheets = calculate_h2h_data_sheets(event_name, section_choice, data, prelim_data)
                data_sheets = add_headers(data_sheets)
                
                if section_choice == 'All':
                    writer = pd.ExcelWriter(ROOT + rf'\Code\H2H\All Classes\{event_name}.xlsx',
                                            engine='xlsxwriter')
                else:
                    writer = pd.ExcelWriter(ROOT + rf'\Code\H2H\All Classes (Prelims)\{event_name}.xlsx',
                                            engine='xlsxwriter')
                save_h2h_excel(writer, data_sheets)  
        
def make_h2hs(NO_OID_FLAG=0):
    data = collect_data()
    df = pd.read_excel(ROOT + r'\Results by Entry.xlsx')
    df = df[['Competitor','Tournament','Event','Code','P1','P2','P3','F1','F2','F3','F4','F5','S1','S2','S3','Sc1','Sc2','Sc3','ScF','ScS']]
    data, prelim_data = run_pairwise_comparisons(df, data)
    h2h_event_sheets(data, prelim_data, NO_OID_FLAG)

def create_class_a_list():
    df = pd.read_excel(ROOT + r'\Results by Entry.xlsx')
    
    df = df[['Competitor','Tm','Class','District']]
    df = df.drop_duplicates(subset='Competitor', keep="first")
    
    class_a = df[df['Class'] == 'A']
    class_a_list = class_a['Competitor'].to_list() 
    class_a_list.append(0)
    return class_a_list

def create_specifier_list():
    df = pd.read_excel(ROOT + r'\ELO.xlsx')
    df = df[df['Tm'].isin(NE_NORTH_SCHOOLS)]
    df.reset_index(drop=True, inplace=True)
    df = df.drop_duplicates(subset='Competitor', keep="first")
    
    specifier_list = df['Competitor'].to_list() 
    specifier_list.append(0)
    return specifier_list

def trim_h2hs_to_specification(folder = "Class A"):
    if folder == 'Class A':
        specifier_list = create_class_a_list()
    else:
        specifier_list = create_specifier_list()
    
    for subdir, dirs, files in os.walk(ROOT + r'\Code\H2H\All Classes'):
        for file in files:
            event_name = file.replace('.xlsx','')
            path = os.path.join(subdir, file)
            
            data = {}
            for sheet in ['WinPct', 'Net', 'Meetings', 'Wins']:
                data[sheet] = pd.read_excel(path, sheet_name=sheet, header=None)
                for i in range(2):  # Runs twice bc does one axis, transposes, does other
                    data[sheet] = data[sheet][data[sheet][0].isin(specifier_list)].T
            
            writer = pd.ExcelWriter(ROOT + rf'\Code\H2H\{folder}\{event_name}.xlsx',
                                    engine='xlsxwriter')
            save_h2h_excel(writer, data)

def save_master_formatting(writer, df, event):
    df = df.T.reset_index().T  # turns column names into row
    df = df.reset_index()
    write_sheet(writer, df, event, layout="h2h_master", index=False, header=None)
    

def create_master_h2h_sheet():
    writer = pd.ExcelWriter(ROOT + r'\H2Hs.xlsx', engine='xlsxwriter')
    master = {}  
    # Hi Noah. I'm choosing to store all dfs in this dictionary instead of replacing all
    # master[event_name]'s to a simple `df` for the sake of debugging. 
    # You can access everything in `master` at once; `df` would store one frame at a time.
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
            
            save_master_formatting(writer, master[event_name], event_name)
            
    writer.close()

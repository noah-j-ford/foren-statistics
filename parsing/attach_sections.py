"""
Takes the clean Sections (Master).xlsx sheet and produces per-competitor, per-round views
that feed into H2H and ELO.

Uses:
    -Sections by Room.xlsx          [fka: Sections (Master).xlsx]

Updates:
    -Results by Entry.xlsx          [fka: Master by Rounds.xlsx]

"""

import pandas as pd
import numpy as np
from config import ROOT, ROUND_NAMES
import utils as util
from reports.timing import progress

def create_identifier_column(df):
    df['Code'] = df['Code'].astype(str)
    df['IndexString'] = (df['Code'] + df['Tournament'] + df['Event'])
    return df


def create_sections_by_entry_sheet(df_results, df_sections):
    # from Claude; we'll see if this fixes the bottleneck?
    OUT_COLS = ['Tournament', 'Event', 'Code', 'Round', 'Sect.', 'JudgeCount', 
                'Judge', 'J2', 'J3', 'J4', 'J5', 'RoundSize', 'SpkOrder',
                'Sp1', 'Sp2', 'Sp3', 'Sp4', 'Sp5', 'Sp6', 'Sp7', 'Sp8']
    
    STAT_COLS = ['Sect.', 'JudgeCount', 'Judge', 'J2', 'J3', 'J4', 'J5',
                 'Sp1', 'Sp2', 'Sp3', 'Sp4', 'Sp5', 'Sp6', 'Sp7', 'Sp8']
    
    sec = df_sections.reset_index(drop=True)
    code_cols = list(sec.columns[11:])            # identical slice to original iloc[j, 11:]

    # one row per section, with the per-section fields the original computed
    core = sec[['Tournament', 'Event'] + STAT_COLS].copy()
    core['Round'] = sec['Round'].astype(str)
    core['RoundSize'] = 7 - sec[code_cols].isna().sum(axis=1)   # same formula as original
    core['_sec_ord'] = np.arange(len(sec))

    # one row per (section, slot) holding a code; SpkOrder = slot position (1-based)
    slots = []
    for k, c in enumerate(code_cols):
        s = core.copy()
        s['Code'] = sec[c].values
        s['SpkOrder'] = k + 1
        slots.append(s[s['Code'].notna()])
    long = pd.concat(slots, ignore_index=True)

    # original `break`s at the first section (file order) in the round containing the code,
    # and code_list.index() takes the first slot within it
    long = (long.sort_values(['_sec_ord', 'SpkOrder'], kind='stable')
                .drop_duplicates(['Tournament', 'Event', 'Round', 'Code'], keep='first'))

    res = df_results[['Code', 'Tournament', 'Event']].reset_index(drop=True)
    res['_res_ord'] = np.arange(len(res))

    # original raised KeyError (get_group) when a results Tournament/Event had no sections
    have = pd.MultiIndex.from_frame(sec[['Tournament', 'Event']].drop_duplicates())
    missing = ~pd.MultiIndex.from_frame(res[['Tournament', 'Event']]).isin(have)
    if missing.any():
        raise KeyError(res.loc[missing, ['Tournament', 'Event']].drop_duplicates().values.tolist())

    df = res.merge(long.drop(columns='_sec_ord'), on=['Code', 'Tournament', 'Event'], how='inner')

    # original emitted rounds in ROUND_NAMES order and raised KeyError for any other round
    rank = {r: i for i, r in enumerate(ROUND_NAMES)}
    df['_rr'] = df['Round'].map(rank)
    if df['_rr'].isna().any():
        raise KeyError(df.loc[df['_rr'].isna(), 'Round'].unique().tolist())

    df = df.sort_values(['_res_ord', '_rr'], kind='stable')[OUT_COLS]
    df.index = np.zeros(len(df), dtype=np.int64)   # original concat never reset index: every row is 0
    df = create_identifier_column(df)               # appends IndexString as the last column
    return df

#### Section Alignment
def create_judge_round_data(df_results, df_sections):
    # merged get_sections_and_sizes here
    data = util.create_container(['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 
                                  'F1', 'F2', 'F3', 'F4', 'F5',
                                  'S1', 'S2', 'S3'])
    sections = util.create_container(ROUND_NAMES)
    sizes = util.create_container(ROUND_NAMES)
    for i, row in progress(df_results.iterrows(), total=len(df_results)):      
        index_string = str(row['Code'])+row['Tournament']+row['Event']
        df_competitor = df_sections[df_sections['IndexString'] == index_string]
        if len(df_competitor) < 1:
            print(index_string)
        for rd in ROUND_NAMES:
            # formerly get_sections_and_sizes
            try:
                j = df_competitor['Round'].to_list().index(rd)
                sections[rd].append(df_competitor['Sect.'].to_list()[j])
                sizes[rd].append(df_competitor['RoundSize'].to_list()[j])
            except ValueError:
                sections[rd].append('')
                sizes[rd].append('')
            #
            if row['Tournament'] in ['NQ_N','NQ_S', 'NQ_N DX', 'NQ_S DX']:
                try:
                    j = df_competitor['Round'].to_list().index(rd)
                    judge_count = df_competitor['JudgeCount'].to_list()[j]
                    if rd == '1':
                        data['J1'].append(df_competitor['Judge'].to_list()[j])
                        data['J2'].append(df_competitor['J2'].to_list()[j])
                    elif rd == '2':
                        data['J3'].append(df_competitor['Judge'].to_list()[j])
                        data['J4'].append(df_competitor['J2'].to_list()[j])
                    elif rd == '3':
                        data['J5'].append(df_competitor['Judge'].to_list()[j])
                        data['J6'].append(df_competitor['J2'].to_list()[j])
                    elif rd == 'Final':
                        data['F1'].append(df_competitor['Judge'].to_list()[j])
                        data['F2'].append(df_competitor['J2'].to_list()[j])
                        data['F3'].append(df_competitor['J3'].to_list()[j])
                        for column in ['F4','F5']:
                            data[column].append('')
                    elif rd == 'Semifinal':
                        data['S1'].append(df_competitor['Judge'].to_list()[j])
                        data['S2'].append(df_competitor['J2'].to_list()[j])
                        data['S3'].append(df_competitor['J3'].to_list()[j])
                        
                except ValueError:
                    if rd == 'Final':
                        for column in ['F1','F2','F3','F4','F5']:
                            data[column].append('')
                    elif rd == 'Semifinal':
                        for column in ['S1','S2','S3']:
                            data[column].append('')
                    elif rd == '3':
                        for column in ['J5','J6']:
                            data[column].append('')
                    else:
                        print(rd, row['Code'], row['Event'])
            else:                
                if rd == '1':
                    # only add a blank once, hence why rd == 1. Every tournament has Rd1,
                    # but that is otherwise arbitrary
                    for column in ['J4','J5','J6']:
                        data[column].append('')  
            #### Mid-Tournament drops 
            #(if they competed round 1 but nothing else; 
            #code handles post-round 2 drops already)
                if len(df_competitor) == 1 and rd=='1' and df_competitor['JudgeCount'].to_list()[0] == 1: #You need to have JudgeCount! 
                    data['J2'].append('')
                    
                try:
                    j = df_competitor['Round'].astype(str).to_list().index(rd)
                    judge_count = df_competitor['JudgeCount'].to_list()[j]
                    
                    if rd == '2' and judge_count == 2:
                        data['J2'].append(df_competitor['Judge'].to_list()[j])
                        data['J3'].append(df_competitor['J2'].to_list()[j])
                        
                    elif rd == '2' and judge_count == 1 and df_competitor['JudgeCount'].to_list()[j-1] == 2:
                        #If there's 1 judge in Rd2 but the previous Rd had 2 judges
                        data['J3'].append(df_competitor['Judge'].to_list()[j])
                        
                    elif rd == '1' and judge_count == 2:
                        data['J1'].append(df_competitor['Judge'].to_list()[j])
                        data['J2'].append(df_competitor['J2'].to_list()[j])
                        
                    elif rd in ['1','2','3'] and judge_count == 1:
                        data[f'J{rd}'].append(df_competitor['Judge'].to_list()[j])
                        
                    elif rd == 'Final' and row['Tournament'] == 'Doane' and row['Event'] == 'OID':
                        data['J1'].append(df_competitor['Judge'].to_list()[j])
                        data['J2'].append(df_competitor['J2'].to_list()[j])
                        data['J3'].append(df_competitor['J3'].to_list()[j])
                        for column in ['F1','F2','F3','F4','F5']:
                            data[column].append('')
                    
                    # Hi noah. There's totally a
                        # elif rd == 'Final': , data['F1'] append Judge no matter what,
                        # then determine how J2-J# should be handled based on judge count
                        # Also. JUST CHANGE `JUDGE` TO `J1`, IT'LL MAKE YOUR LIFE SO MUCH
                        # EASIER!!!!
                    
                    elif rd == 'Final' and judge_count == 5: #5-judge LSW Champs
                        data['F1'].append(df_competitor['Judge'].to_list()[j])
                        
                        for k in range(2,6):
                            data[f'F{k}'].append(df_competitor[f'J{k}'].to_list()[j])
                            
                    elif rd == 'Final' and judge_count == 3: #Champs Finals Rds
                        data['F1'].append(df_competitor['Judge'].to_list()[j])
                        data['F2'].append(df_competitor['J2'].to_list()[j])
                        data['F3'].append(df_competitor['J3'].to_list()[j])
                        for column in ['F4','F5']:
                            data[column].append('')
                    elif rd == 'Final' and judge_count == 1: #Honors/Merit/Consolation Finals Rds
                        data['F1'].append(df_competitor['Judge'].to_list()[j])
                        for column in ['F2','F3','F4','F5']:
                            data[column].append('')
                    
                    elif rd == 'Final' and judge_count == 2:  # Districts Finals
                        data['F1'].append(df_competitor['Judge'].to_list()[j])
                        data['F2'].append(df_competitor['J2'].to_list()[j])
                        for column in ['F3','F4','F5']:
                            data[column].append('')
                    
                    elif rd == 'Semifinal':
                        data['S1'].append(df_competitor['Judge'].to_list()[j])
                        data['S2'].append(df_competitor['J2'].to_list()[j])
                        data['S3'].append(df_competitor['J3'].to_list()[j])
                        
                except ValueError:
                    if rd == 'Final':
                        for column in ['F1','F2','F3','F4','F5']:
                            data[column].append('')
                    elif rd == 'Semifinal':
                        for column in ['S1','S2','S3']:
                            data[column].append('')
                    elif rd == '3' and sum(df_competitor['JudgeCount'].to_list()[0:2]) < 3:
                        data['J3'].append('')
                        
    df_judges = pd.DataFrame(data)
    sections = pd.DataFrame(sections)
    sizes = pd.DataFrame(sizes)
    return df_judges, sections, sizes


def append_section_data_to_results(df_results, df_sections):
    df_section_names, df_section_sizes, df_judges = create_judge_round_data(df_results, df_sections)
    df_add = pd.concat([df_section_names, df_section_sizes, df_judges], axis=1)
    df = pd.concat([df_results, df_add], axis=1)
    return df


def update_columns(df_results, df):
    columns = df_results.columns
    columns = columns.to_list() + ['Sc1','Sc2','Sc3','ScF','ScS',
                                   'Sz1','Sz2','Sz3','SzF','SzS',
                                   'J1','J2','J3','J4','J5','J6',
                                   'JF1','JF2','JF3','JF4','JF5','JS1','JS2','JS3']
    df.columns = columns
    return df    

def to_entries(df_results, df_sections):
    df_sections = create_sections_by_entry_sheet(df_results, df_sections)
    df = append_section_data_to_results(df_results, df_sections)
    df = update_columns(df_results, df)
    df.to_excel(ROOT + r'\Results by Entry.xlsx', index=False)
    return df

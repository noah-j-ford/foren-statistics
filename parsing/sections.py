"""
Uses:
    -Sections (Raw Format).xlsx
    
Creates:
    -Sections by Judge.xlsx      [fka: Sections (Base).xlsx]
    -Sections by Room.xlsx       [fka: Sections (Master).xlsx]
"""

import pandas as pd
import numpy as np
from standardization import Standardizer
from config import ROOT
import utils as util
from reports.timing import progress
std = Standardizer()

#### Base Section Sheets
def create_rd_column_list(df, tournament_name):
    rd_column_list, rd = [[],""]
    for i, row in df.iterrows():
        cell = row[0]
        if pd.notna(cell) and ' - ' in cell:
            # Round 1 - 9:00 AM
            # Final round - 1:45 PM
            rd = cell.split(' - ')[0].replace("Round ","").replace(" round","")
        rd_column_list.append(rd)
    return rd_column_list

def set_column_names(df):
    """
    This sets the column names based on the largest section so far present;
    If there has been a section of 8, it will set all the way through Sp8. If that fails,
    it tries for Sp7, Sp6, and finally Sp5.
    """
    columns = ['Sect.', 'Judge(s)', 'Room', 'Sp1', 'Sp2', 'Sp3', 'Sp4', 'Sp5',
               'Sp6', 'Sp7', 'Sp8']   
    for col_count in [len(columns), len(columns)-1, len(columns)-2, len(columns)-3]:
        try:
            df.columns = columns[:col_count+1]
            break
        except ValueError:
            continue
    return df

def parse_judge_column(df):
    """
    The 'Judge(s)' column has the Judge Code AND Judge Name in the same box (e.g., R1 Noah Ford)
    This parses that text to separate it into the code and name separately
    Also it drops the room column while we're at it
    """
    df['temp'] = df['Judge(s)'].str.split(' ')  # splits into list of individual words
    df['JudgeCode'] = df['temp'].str[0]  # pulls first "word" as the judge code
    df['temp'] = df['temp'].str[1:]  # redefines temp with the code removed
    df['Judge'] = [' '.join(map(str, j)) for j in df['temp']]  # recombines the name into one string
    df.drop(['Judge(s)', 'Room', 'temp'], axis=1, inplace=True)
    return df


def parse_to_section_by_judge():
    file_location = ROOT + r'\Manual\Sections (Raw Format).xlsx'
    
    master_df_by_judge = pd.DataFrame()
    for tournament_index, sheet in enumerate(progress(util.get_tournament_list())):
        df = pd.read_excel(file_location, sheet_name=sheet, header=None)
        tournament_name = df[0][0]
        
        df = util.drop_speechwire_rows(df)
        event_column_list = util.create_event_column_list(df, tournament_name)
        rd_column_list = create_rd_column_list(df, tournament_name)
        
        df = set_column_names(df)
            
        df['Tournament'] = sheet
        df["Event"] = event_column_list
        df["Round"] = rd_column_list
        
        df = util.drop_unneeded_rows(df, tournament_name, mode='sections')
  
        df[['Sect.']] = df[['Sect.']].ffill()  # fills all nans below with the last non-nan value
        df['Sect.'] = df['Sect.'].replace(
            {'FINAL':'Champs',
             'NEXTIN':'Honors',
             'MERIT':'Merit',
             'CONSOLATION':'Consolation'},
            )
        
        df = parse_judge_column(df)

        df = util.move_column(df, 'Round', 0)
        df = util.move_column(df, 'Event', 0)
        df = util.move_column(df, 'Tournament', 0)
        df = util.move_column(df, 'Judge', 4)
        df = util.move_column(df, 'JudgeCode', 4)

        master_df_by_judge = pd.concat([master_df_by_judge, df], axis=0).reset_index(drop=True)
    return master_df_by_judge
    
def convert_to_section_by_room(df):
    data = util.create_container(['J2', 'J3', 'J4', 'J5', 'JC2', 'JC3', 'JC4', 'JC5'])
    
    df_judge = df[df.isna().sum(axis=1) < 7].reset_index(drop=True)
    for i, row in df.iterrows():
        nans = sum(df.iloc[i].isna())
        if nans <= 6: #6+ NaNs mean it's a blank row, 6 is the minimum. Trust me.
            nan_counter = {1:0,2:0,3:0,4:0}
            for item in nan_counter:
                try:
                    nan_counter[item] = sum(df.iloc[i+item].isna())
                except IndexError: 
                    pass
            #5 Judge round
            if all(nan_counter[i] >= 6 for i in [1, 2, 3, 4]):
                for j in range(1,5):
                    data[f'J{j+1}'].append(df['Judge'][i+j])
                    data[f'JC{j+1}'].append(df['JudgeCode'][i+j])
            #3 judges in round (row with data is followed by 2 nan rows (2 more judges))
            elif all(nan_counter[i] >= 6 for i in [1, 2]):
                data['J2'].append(df['Judge'][i+1])
                data['JC2'].append(df['JudgeCode'][i+1])
                data['J3'].append(df['Judge'][i+2])
                data['JC3'].append(df['JudgeCode'][i+2])
                for column in ['J4','JC4','J5','JC5']:
                    data[column].append(np.nan)
            #2 judges in round (row with data followed by one nan row but the next is not)
            elif nan_counter[1] >= 6: 
                data['J2'].append(df['Judge'][i+1])
                data['JC2'].append(df['JudgeCode'][i+1])
                for column in ['J3','JC3','J4','JC4','J5','JC5']:
                    data[column].append(np.nan)
            else:
                for column in ['J2','JC2','J3','JC3','J4','JC4','J5','JC5']:
                    data[column].append(np.nan)
    for column in data:
        try:
            df_judge[column] = data[column]
        except ValueError:
            input(column)
    df_judge['JudgeCount'] = df_judge[['Judge', 'J2', 'J3','J4','J5']].apply(
        lambda row: row.count(), axis=1)
    column_order = ['Tournament','Event','Round','Sect.',
        'JudgeCount','JudgeCode','JC2','JC3','JC4','JC5','Judge','J2','J3','J4','J5',
        'Sp1','Sp2','Sp3','Sp4','Sp5','Sp6','Sp7', 'Sp8']
    df_judge = df_judge.reindex(columns=column_order)
    return df_judge 

def standardize_judge_names(df):
    df['Judge'] = df['Judge'].apply(std.standardize_name)
    return df

def parse_raw_sections():
    df_by_judge = parse_to_section_by_judge()
    df_by_judge = standardize_judge_names(df_by_judge)
    df_by_room = convert_to_section_by_room(df_by_judge)
    return df_by_judge, df_by_room
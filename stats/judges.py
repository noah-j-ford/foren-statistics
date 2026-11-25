"""
Uses:
    Sections by Judge.xlsx
    Results by Entry.xlsx
    Judge Comment Length (Raw Format).xlsx

Updates:
    Sections by Judge.xlsx

Creates:
    Stats by Judges.xlsx
"""

import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from standardization import Standardizer
import utils as util
from config import ROOT
from formatting import write_sheet
std = Standardizer()

def create_judge_sections():
    df = pd.read_excel(ROOT + r'\Code\Sections by Judge.xlsx')
    for i, row in df.iterrows():
        if pd.notna(row['Sp1']):
            # If there's a speaker in the round [not blank row], store the row temporarily
            filled_row = df.filter(regex='Sp').iloc[i, :8]
        else: 
            # otherwise, replace the current row with the filled row above it
            speakers = df.filter(regex='Sp').columns
            df.loc[i, speakers] = filled_row[speakers]
    return df

def create_reference_dict():
    ref = pd.read_excel(ROOT + r'\Results by Entry.xlsx')
    
    # List of columns we want to build dictionaries for.
    metrics = ['Competitor', 'Cume_P', 'Cume_F', 'PrelimResult',
               'FinalResult', 'P1', 'P2', 'P3', 'F1', 'F2', 'F3', 'F4', 'F5', 'S1', 'S2', 'S3']
    
    # Build the nested dictionary
    data = {}
    tournament_groups = ref.groupby('Tournament')
    
    for tournament_name, df_tournament in tournament_groups:
        data[tournament_name] = {}
        
        event_groups = df_tournament.groupby('Event')
        for event_name, df_event in event_groups:
            data[tournament_name][event_name] = {
                metric: dict(zip(df_event['Code'], df_event[metric]))
                for metric in metrics
            }
            
    return data

def map_reference_dict(df, data):
    frames = []
    stats = ['Competitor', 'Cume_P', 'Cume_F', 'PrelimResult', 'FinalResult',
             'P1', 'P2', 'P3', 'F1', 'F2', 'F3', 'F4', 'F5', 'S1', 'S2', 'S3']
    tournament_groups = df.groupby('Tournament')
    for tournament_name, df_tournament in tournament_groups:
        event_groups = df_tournament.groupby('Event')
        for event_name, df_event in event_groups:
            df_event = df_event.copy()
            for stat in stats:
                for num in [f'{j+1}' for j in range(8)]:
                    try:
                        df_event[f"{stat}_{num}"] = df_event[f"Sp{num}"].map(
                            data[tournament_name][event_name][stat]
                        )
                    except KeyError:  # Sp8
                        pass
            frames.append(df_event)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=0)

def determine_ranks_list(df, row, i):
    previous_round_of_this_event_at_this_tournament_had_two_judges = False
    prefix_dict = {
        ('1', 2): ['P1', 'P2'],
        ('2', 2): ['P2', 'P3'],  # Manually overriden to P3, P4 for Nat Quals
        ('3', 2): ['P5', 'P6'],  # Nat Quals
        ('Final', 3): ['F1', 'F2', 'F3'],  # Champs OR 3-judge Honors; Overridden to S{#} later for Semis
        ('Final', 5): ['F1', 'F2', 'F3', 'F4', 'F5'],
        ('Final', 2): ['F1', 'F2'],
        ('Semifinal', 3): ['S1', 'S2', 'S3'],
    }
    # temporarily filter full df to strictly the rows that apply to THAT EXACT SECTION (each row equals one judge)  
    temp = df[(df['Tournament']==row['Tournament']) & (df['Event']==row['Event']) & (df['Round']==row['Round']) & (df['Sect.']==row['Sect.'])]
    temp = temp.reset_index()

    if len(temp) != 1:  # If there's >1 judge in the section
            
        # Set flag to True to manually override for P3 below
        if row['Round'] == '1' and len(temp) == 2:
            previous_round_of_this_event_at_this_tournament_had_two_judges = True
            
        if (row['Round'], len(temp)) in prefix_dict:
            if row['Sect.'] == 'Semifinal':
                prefixes = ['S1', 'S2', 'S3']
            elif row['Round'] == '2' and row['Tournament'] in ['NQ_N', 'NQ_N DX', 'NQ_S', 'NQ_S DX']:
                prefixes = ['P3', 'P4']
            else:
                prefixes = prefix_dict[(row['Round'], len(temp))]
            for j, prefix in enumerate(prefixes):
                if temp['index'][j] == i:
                    ranks = df.filter(regex=f'{prefix}_').iloc[i, :8]
                    break
                
    else:  
        # if Rd '2' is actually P3 bc its preceded by a 2-judge flight
        if previous_round_of_this_event_at_this_tournament_had_two_judges:
            ranks = df.filter(regex='P3_').iloc[i, :8]
            
            # Check if finished going through round 2 of that flight by looking to see if
            # the next row is either for a final or a new event (no final was run) 
            if df['Event'][i+1] != row['Event'] or df['Sect.'][i+1] == 'Final': 
                previous_round_of_this_event_at_this_tournament_had_two_judges = False
                
        elif row['Round'] in ['1', '2', '3']:  
            ranks = df.filter(regex=f'P{row["Round"]}_').iloc[i, :8]
        elif row['Round'] == 'Final' and row['Sect.'] in ['Honors', 'Merit', 'Consolation']:
            ranks = df.filter(regex=f'F{row["Round"]}_').iloc[i, :8] # Select Judge 1 of final's ranks (bc there is only one judge)
    try:
        return ranks
    except UnboundLocalError:
        pass
    
def clean_judge_expanded(df):
    largest_section_size = len(df.filter(regex='Sp').columns)
    for i in [f'{j+1}' for j in range(largest_section_size)]:
        df[f'Rk_{i}'] = np.nan
    df.reset_index(drop=True, inplace=True)
    for i, row in df.iterrows():
        ranks = determine_ranks_list(df, row, i)
        for j, rank in enumerate(ranks): 
            df.at[i, f'Rk_{j+1}'] = rank
    return df

#### Judge Evaluation Functions
def calculate_accuracy_score(result, squared=0):
    value = 0
    before = 0
    for x in result:
        if pd.notna(x):
            if squared == 0:
                value += abs(before - x)
            elif squared == 1:
                value += (abs(before - x)**2)
            before = x
    return value

def reorder_judge_ranks(judge_ranks, consensus):
    judge_temp = {}
    for i, judge_rank in enumerate(judge_ranks):
        judge_temp[judge_rank] = consensus.to_list()[i]
    sorted_judge_ranks = dict(sorted(judge_temp.items())) #Sorts according to correct values

    judge_ranks = list(sorted_judge_ranks.values())
    return judge_ranks

def get_accuracy_score(judge_ranks, consensus, squared=0):
    consensus_value = calculate_accuracy_score(consensus.sort_values(), squared)
    judge_value = calculate_accuracy_score(judge_ranks, squared)
    accuracy_score = judge_value - consensus_value
    return accuracy_score
    
def evaluate_judges(df):
    judge_scores = {'Score':[], 'Squared':[]}  # !!!
    
    for i, row in df.iterrows():
        judge_ranks = df.filter(regex='Rk_').iloc[i, :8] #['Rk_1',(...), 'Rk_7']
        if df['Round'][i] != 'Final':
            consensus = df.filter(regex='PrelimResult_').iloc[i, :8]
        elif df['Round'][i] == 'Final':
            consensus = df.filter(regex='Cume_F_').iloc[i, :8]
        else:
            consensus = None
        judge_ranks = reorder_judge_ranks(judge_ranks, consensus)
        raw_score = get_accuracy_score(judge_ranks, consensus)
        squared_score = get_accuracy_score(judge_ranks, consensus, squared=1)
        judge_scores['Score'].append(raw_score)
        judge_scores['Squared'].append(squared_score)
    df['Score'] = judge_scores['Score']
    df['Squared'] = judge_scores['Squared']
    df.to_excel(ROOT + r'\Code\Sections by Judge.xlsx', index=False)

def count_ballots(df):
    count = 0
    for i, row in df.iterrows():
        rd = df.filter(regex='Rk_').loc[i, :].iloc[:8] #['Rk_1',(...), 'Rk_7']
        for item in rd:
            if pd.notna(item):
                count+=1
    return count

def create_judge_sheet(df):
    data = {'Judge':[], 'Rounds':[], 'Ballots':[], 'Score':[], 'Squared':[]}  # !!!
    df['Judge'] = df['Judge'].apply(std.standardize_name)
    judge_groups = df.groupby('Judge')
    
    for judge_name, df_judge in judge_groups:
        data['Judge'].append(judge_name)
        data['Rounds'].append(len(df_judge))
        data['Ballots'].append(count_ballots(df_judge))
        data['Score'].append(df_judge['Score'].mean())
        data['Squared'].append(df_judge['Squared'].mean())
        #to do: # of finals judged, # of rounds of each event judged, error by event

    df_judges = pd.DataFrame()
    for variable, values in data.items():
        df_judges[variable] = values
        
    df_judges = df_judges.sort_values(by=['Rounds'], ascending=False)
    return df_judges

def process_judge_data(judges):
    data = {'Judge':[], 'Team':[], 'Avg Char':[], 'Ballots':[], 'Char':[]}  # !!!
    
    for judge in judges:
        data['Judge'].append(judge)
        
        team = '/'.join(list(set(judges[judge]['Team'])))
        data['Team'].append(team)
        
        ballots = sum(judges[judge]['Ballots'])
        characters = sum(judges[judge]['Characters'])
        
        data['Avg Char'].append( round((characters/ballots), 0) )
        data['Ballots'].append(ballots)
        data['Char'].append(characters)
    df = pd.DataFrame(data)
    return df
        
def process_comment_length():
    df = pd.DataFrame()
    judges = {}
    for sheet in util.get_tournament_list(judges=True):
        tempdf = pd.read_excel(ROOT + r'\Manual\Judge Comment Length (Raw Format).xlsx',
                                sheet_name=sheet
                                )
        for i, row in tempdf.iterrows():
            judge = std.standardize_name(row['Judge'])
            if judge not in judges:
                judges[judge] = util.create_container(['Team', 'Length', 'Ballots', 'Characters'])
            
            team = std.standardize_school_name(row['Team'])
            length = row['Average comment length']
            ballots = row['# of comments']
            characters = length * ballots
            
            judges[judge]['Team'].append(team)
            judges[judge]['Length'].append(length)
            judges[judge]['Ballots'].append(ballots)
            judges[judge]['Characters'].append(characters)
 
    df = process_judge_data(judges)
    return df
        
def combine_ballots_and_error(df_ballots, df_judges):
    df_ballots = df_ballots.sort_values(['Judge']).reset_index(drop=True) 
    df_ballots.rename({'Judge':'Judge_2'}, axis=1, inplace=True)
    df_judges = df_judges.sort_values(['Judge']).reset_index(drop=True)
    df_judges = df_judges.rename({'Ballots':'Ballots_Varsity'},axis=1)
    varsity_judges = df_judges['Judge'].to_list()
    df_ballots = df_ballots[df_ballots['Judge_2'].isin(varsity_judges)].reset_index(drop=True)
        #Drop judges who have not judged any varsity rounds (but have judged novice rounds)
    df = pd.concat([df_judges,df_ballots],axis=1)
    df.drop(['Judge_2'],axis=1,inplace=True)
    df = df.reindex(columns=['Judge', 'Team', 'Rounds', 'Ballots', 'Avg Char', 'Char',
                             'Ballots_Varsity', 'Score', 'Squared'])
    df = df.sort_values(['Rounds', 'Ballots'],
                        ascending=[False, False]).reset_index(drop=True)
    return df

def get_judge_accuracy_tier(x):
    if x < 10:
        return 'Terrible'
    if 25 > x >= 10:
        return 'Bad'
    if 40 > x >= 25:
        return 'Mediocre'
    if 60 > x >= 40:
        return 'Average'
    if 75 > x >= 60:
        return 'Good'
    if 90 > x >= 75:
        return 'Great'
    if x >= 90:
        return 'Excellent'

def get_judge_percentile_scores(df):
    df['Length'] = round(df['Avg Char'].rank(pct=True)*100,0)
    
    df['Percentile_A'] = df['Score'].rank(pct=True, ascending=False)
    df['Percentile_B'] = df['Squared'].rank(pct=True, ascending=False)
    df['Quality'] = round(df[['Percentile_A', 'Percentile_B']].mean(axis=1)*100,0)
    df['Tier'] = df['Quality'].apply(get_judge_accuracy_tier)
    df.drop(['Score','Squared','Percentile_A','Percentile_B'],axis=1, inplace=True)
    
    df.drop(['Char','Ballots_Varsity'],axis=1,inplace=True) #Kept on separate line bc maybe I want these back in the future
    return df

def save_judge_formatting(df):
    df.rename({'Team':'Tm', 'Rounds':'Rds'}, axis=1, inplace=True)
    df = util.add_header_row(df)
    writer = pd.ExcelWriter(ROOT + r'\Stats by Judges.xlsx', engine='xlsxwriter')
    write_sheet(writer, 
                df=df, sheet_name="Judges", layout="judge_stats", 
                index=False, header=False)
    writer.close()

def process_judges():
    df = create_judge_sections() #6.768
    data = create_reference_dict() #3.012
    df = map_reference_dict(df, data) #5.972
    
    df = clean_judge_expanded(df)
    evaluate_judges(df)
    df_judges = create_judge_sheet(df)
    df_ballots = process_comment_length()
    df = combine_ballots_and_error(df_ballots, df_judges)
    df = get_judge_percentile_scores(df)
    save_judge_formatting(df)

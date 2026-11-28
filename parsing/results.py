"""
Uses:
    -Results (Raw Format).xlsx
    
Creates:
    -dataframe for stats_competitors to process into Results by Entry.xlsx, i guess
    
    NO IT DOESN'T
    -Results by Entry.xlsx     [fka: Results.xlsx]

What it does: Takes raw Speechwire results spreadsheets and produces the clean, 
unified Results by Entry.xlsx. This is purely a parsing and normalization job. 
It knows about Speechwire's quirks — the multi-tournament format, flighted rounds, 
LSW's weird DUO structure, OID's special casing — 
but it doesn't know anything about statistics.
"""
import warnings
import pandas as pd
import numpy as np
import parsing.edgecases as edg
from config import YEAR, ROOT, TOURNAMENTS
import utils as util
from reports.timing import progress
warnings.filterwarnings('ignore')

# =============================================================================
#### RAW FORMAT
# =============================================================================

def division_text_in_prelim_column(df):
    """
    Checks if first value in the 'Prelims' column is actually a 'Novice'/'Varsity' string
    """
    cell = df['Prelims'].to_list()[0]
    if cell in ['Varsity', 'Novice']:
        return True
    return False

def insert_div_column(df):
    new_df = pd.DataFrame()
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        if division_text_in_prelim_column(df_event):
            column_names = df_event.columns.to_list()[:-2]
            column_names.insert(3, 'Division')
            column_names = column_names[:-1]
            column_names.append('Tournament')
            column_names.append('Event')
            df_event.columns = column_names
        else:
            # idk why or when exactly, but the 3rd to last column is a column of nans (including
            # the column name) so this is explicitly naming it and then moving it into position
            column_count = len(df_event.columns)
            cols = df_event.columns.tolist()
            cols[column_count - 3] = 'Division'
            df_event.columns = cols
            
            df_event = util.move_column(df_event, 'Division', 3)            
        new_df = pd.concat([new_df, df_event], axis=0)
    return new_df

def push_div_column_for_group_events(df):
    """
    11/13/26 here, explaining your function to yourself
        So this literally just takes the full tournament df and then checks
        if there are ranks in a Division column (meaning some event lacks the
        column) so it locates the index_list of that event and then double-checks
        it is an issue and then does the Excel equivalent of "insert 6 cells",
        "move cells to right"
    """
    
    #If you don't do this, it pushes the Tournament name into the Event column for DUO and OID.
    df_metadata = df[['Tournament', 'Event']]
    # OID DOESNT HAVE DIV BUT DUO DOES. ITS SPLIT MID EVENT
    if len(df['Division'].value_counts()) > 3:  # There's more than 'Novice'/'Varsity'/NaN
        for event_name in ['DUO', 'OID', 'Duet']:
            if event_name in df['Event'].values:
                # Creates list of indices of that event
                index_list = df[df['Event'] == event_name].index.tolist()
                if index_list:
                    # Check that that event actually DOESNT HAVE A DIV COLUMN
                    if df['Division'][index_list[0]] not in ['Varsity', 'Novice']:
                        
                        # Force columns from index 3 onward to genuinely become 'object' dtype
                        df = pd.concat([df.iloc[:, :3], df.iloc[:, 3:].astype("object")], axis=1)
                            # pd.concat is required because it bypasses both
                                # A) duplicate column name errors and
                                # B) pandas 2.0+ dtype locks 
                                    # (it got mad I want to put "1" (from a "string" column) 
                                    # into a float64 column))
                        
                        # Shift columns starting from the 6th column (index 5)
                        df.iloc[index_list, 3:] = df.iloc[index_list, 3:].shift(axis=1)
                        # Shift() shifts by 1 automatically,
                            # specify axis=1 for the column rather than creating blank row
                        # '3' is the index (column) where Division sits at (the 4th, 0-indexed)
    df_data = df.drop(['Tournament','Event'], axis=1)
    df = pd.concat([df_data, df_metadata], axis=1)
    return df

def check_event_for_division_header(df, i, division_header):    
    # i = tournament name header
    # i + 1 = event name header
    # i + 2 = table headers
    columns = df.iloc[i+2, :].to_list()
    if 'Division' in columns and i == 0:
        division_header = 'first event' # the first event header has 'Division' in it
    elif 'Division' in columns:
        division_header = 'other event' # another event has 'Division' in it (but not the first)
    return division_header

def locate_division_header(df, tournament_name):
    division_header = None
    for i, row in df.iterrows():
        if row[0] == tournament_name:
            division_header = check_event_for_division_header(df, i, division_header)
            if division_header is not None:
                break
    return division_header

def process_raw_dataframe(df, sheet):
    tournament_name = df[0][0]
    df = util.drop_speechwire_rows(df)
    division_header = locate_division_header(df, tournament_name)
    
    df, df_finals, df_semis = edg.check_for_elim_rounds(df, sheet, tournament_name)

    event_column_list = util.create_event_column_list(df, tournament_name)
    df.columns = df.iloc[2, :].to_list()
    df['Tournament'] = sheet
    df['Event'] = event_column_list
    df = util.drop_unneeded_rows(df, tournament_name, mode="results")

    #insert division column if it needs to be lol
    if division_header == 'first event':
        df = push_div_column_for_group_events(df)
    elif division_header == 'other event':
        df = insert_div_column(df)

    df = util.move_column(df, 'Event', 0)
    df = util.move_column(df, 'Tournament', 0)

    df.rename({'Competitor(s)':'Competitor'}, axis = 1, inplace=True)
    #Drops leftover blank "Varsity [Event]" header rows
    df = df[df['Competitor'] == df['Competitor']].reset_index(drop=True)
    
    for drop_col in ['Head to', 'Judges']:
        try:
            df.drop([drop_col], axis=1, inplace=True)
        except KeyError:
            pass

    if df_finals is not None:
        df = edg.attach_elim_data(df, df_finals, df_semis)
    return df

def clean_raw_results():
    file_location = ROOT + r'\Manual\Results (Raw Format).xlsx'
    data = {}
    for sheet in progress(util.get_tournament_list()):
        df = pd.read_excel(file_location, sheet_name=sheet, header=None)
        df = process_raw_dataframe(df, sheet)
        data.update({sheet:df})
    return data

# %%
# =============================================================================
#### MANUAL RAW RESULT TO PROCESSED FORMAT
# =============================================================================

def pull_out_div_from_prelims(df):
    prelims_index = df.columns.to_list().index('Prelims')
    division_index = df.columns.to_list().index('Division')
    total_columns = len(df.columns)

    # Create mask to identify rows where Prelims column (prelims_index) are varsity/nov
    # Use .values to get a NumPy array
    mask = df.iloc[:, prelims_index].isin(['Varsity','Novice']).values

    # Shift cells in rows where the condition is met
    df.iloc[mask, prelims_index:total_columns-1] = df.iloc[mask, prelims_index+1:total_columns].values  # Shift values to the left
    df.iloc[mask, division_index] = df.iloc[mask, prelims_index]  # Move "foo" or "bar" into the last column
    return df

def push_div_column_for_group_events_secondary(df):
    if len(df['Division'].value_counts()) > 3: #There's more than 'Novice','Varsity',NaN
        for event_name in ['DUO','OID','Duet']: 
            if event_name in df['Event'].to_list():
                index_list = df[df['Event'] == event_name].index.to_list()   #Creates list of indices of that event     
                df.iloc[index_list[0]:index_list[-1]+1,5:] = df.iloc[index_list[0]:index_list[-1]+1,5:].shift(axis=1) 
                #Takes first and last indices of the event (the start and end of the blank) to shift (ADDS ONE BC IT ISN'T INCLUSIVE OF THE LAST ROW APPARENTLY)
                #Shift() shifts by 1 automatically, specify axis=1 for the column rather than creating blank row
                #'5' is the index (column) where Division sits at (the 6th, 0-indexed)
    return df    

def add_blank_columns(df):
    for column in (['Division', 'Opps.', 'Opp. Avg', 'S1', 'S2', 'S3', 'Cume_S', 
                   'Recips_S', 'Cume_ST','Recips_ST','Semi_Sec','Semi_Rd_Rk',
                   'Semi_Result', 'Cume_TOTAL', 'Recips_TOTAL', 'P4', 'P5', 'P6']):
                   # 'Finals', 'Finals.1']):
        if column in df.columns.to_list():
            if column == 'Division':
                df = push_div_column_for_group_events_secondary(df)
        else:
            df[column] = '' #appends blank column to end of df
            if column == 'Division':
                if 'Varsity' in df['Prelims'].to_list():
                #There are events which had combined novice/varsity while DI (top of sheet)
                #did not; need to find the rows that have Division stored in 'Prelims' (P1)
                #column and pop that information out into a new Division column
                    df = pull_out_div_from_prelims(df)
    return df

def split_ranks_string_to_list(x):
    """123->[1,2,3]; 12->[1,2,np.nan]; 1->[1,np.nan, np.nan]; etc."""
    ranks = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    if pd.notna(x):
        ranks = [x[i] if i < len(x) else np.nan for i in range(6)]
        if len(x) > 6:
            print(x, len(x)) # For debugging purposes
    return ranks
  
def handle_flighted_tournaments(df):
    df['PrelimsA'] = df['PrelimsA'].astype('str')
    df['PrelimsB'] = df['PrelimsB'].astype('str')
    df['PrelimRanks'] = df['PrelimsA'] + df['PrelimsB']
    df['PrelimRanks'] = df['PrelimRanks'].apply(split_ranks_string_to_list)
    df['P1'] = df['PrelimRanks'].apply(lambda x: x[0]).astype(int, errors='ignore')
    df['P2'] = df['PrelimRanks'].apply(lambda x: x[1]).astype(int, errors='ignore')
    df['P3'] = df['PrelimRanks'].apply(lambda x: x[2]).astype(int, errors='ignore')
    df.drop(['PrelimsA','PrelimsB','PrelimRanks'],axis=1,inplace=True)
    return df

def handle_nat_quals(df):
    df['PrelimRanks'] = df['PrelimsA'] + ', ' + df['PrelimsB'] + ', ' + df['PrelimsC']
    df['PrelimRanks'] = df['PrelimRanks'].str.replace(', ','')
    df['PrelimRanks'] = df['PrelimRanks'].apply(split_ranks_string_to_list)
    for i in range(6):
        df[f'P{i+1}'] = df['PrelimRanks'].apply(lambda x: x[i]).astype(int,errors='ignore')
    return df

def handle_two_ranks(df):
    if df.dtypes['PrelimsA'].name == 'int64' and df.dtypes['PrelimsB'].name == 'int64':
        #This is a two-round, two-ranks tournament. [Doane, Elkhorn]
        df.rename({'PrelimsA':'P1', 'PrelimsB':'P2'},axis=1,inplace=True)
        df['P3'] = ''
    else:
        df = handle_flighted_tournaments(df)
    return df

def clean_ranks_down_to_integers(x):
    if type(x) == int or type(x) == float: #It's "1" or nan
        if pd.notna(x):
            x = int(x)
        return x
    if ', ' in x: #It is either "1, 1" or "1 (50), 1 (50)"
        x = x.split(', ')
        x_list = []
        for item in x:
            x_list.append(item[0])
        x = ''.join(x_list) #"1, 1, 1" -> 111; "1 (50), 1 (50)" -> '11'         
        return x
    if '(' in x: #It's "1 (50)"
        x = int(x[0]) #"1 (50)" -> 1
        return x

def define_prelim_rank_columns(df):        
    #3 rounds, 'division' column
    if 'Unnamed: 7' in df.columns.to_list() and 'Unnamed: 8' in df.columns.to_list():
        df.rename({'Prelims':'P1','Unnamed: 7':'P2','Unnamed: 8':'P3'}, 
                  axis=1, inplace=True) 
    #3 rounds, no 'division' column
    elif 'Unnamed: 6' in df.columns.to_list() and 'Unnamed: 7' in df.columns.to_list():
        if df['Tournament'][0] in ['NQ_N', 'NQ_S', 'NQ_N DX', 'NQ_S DX']:
            df.rename({'Prelims':'PrelimsA','Unnamed: 6':'PrelimsB','Unnamed: 7':'PrelimsC'},
                      axis=1, inplace=True)
        else:
            df.rename({'Prelims':'P1','Unnamed: 6':'P2','Unnamed: 7':'P3'},
                      axis=1, inplace=True)
    #flighted/2-round, 'division' column
    elif 'Unnamed: 7' in df.columns.to_list():
        df.rename({'Prelims':'PrelimsA','Unnamed: 7':'PrelimsB'},
                  axis=1, inplace=True)
    #flighted/2-round, no 'division' column
    elif 'Unnamed: 6' in df.columns.to_list():
        df.rename({'Prelims':'PrelimsA','Unnamed: 6':'PrelimsB'},
                  axis=1, inplace=True)
    else:
        print(df['Tournament'][0])
        
    if 'P1' in df.columns.to_list():
        for column in ['P1','P2','P3']:
            df[column] = df[column].apply(clean_ranks_down_to_integers)
    
    if 'PrelimsC' in df.columns.to_list():
        df = handle_nat_quals(df)
    if 'PrelimsA' in df.columns.to_list() and 'PrelimsB' in df.columns.to_list():
        for column in ['PrelimsA','PrelimsB']:
            df[column] = df[column].apply(clean_ranks_down_to_integers)
        df = handle_two_ranks(df)
        
    return df

def drop_irrelevant_columns(df):
    for column in ['Spkr.', 'Opp. Avg..1', 'Prelim', '1s', 'Finals.1', 'Playoff', 
                   'Spkr..1', 'Prelim.1', 'Drop B/W']:
        try:
            df.drop([column],axis=1,inplace=True)
        except KeyError:
            pass
    return df

def move_columns(df):
    column_dict = {'Div':5, 'P1':6, 'P2':7, 'P3':8, 'Cume_P':9, 'Recips_P':10,
            'PrelimResult':11, 'F1':12, 'F2':13, 'F3':14, 'Cume_F':15, 'Recips_F':16,
            'Final_Rd_Rk':17, 'FinalResult':18, 'Break':19, 'OppAvgRk':20, 'OppBeat':21,
            'F4':22, 'F5':23, 'S1':24, 'S2':25, 'S3':26,
            'Cume_S':27, 'Recips_S':28, 'Cume_ST':29, 'Recips_ST':30, 'Semi_Sec':31,
            'Semi_Rd_Rk':32, 'Semi_Result':33, 'Cume_TOTAL':34, 'Recips_TOTAL':35,
            'P4':36, 'P5':37, 'P6':38,
            }
    for column, index in column_dict.items():
        column_to_move = df.pop(column)
        df.insert(loc=index, column=column, value=column_to_move)
    return df

def rename_columns(df):
    df.rename({'Team':'Tm','Division':'Div',#'Recips':'Recips_P',
               'Opp. Avg.':'OppAvgRk','Opps.':'OppBeat'},axis=1,inplace=True)
    if 'All ranks' in df.columns.to_list():
        df.rename({'All ranks':'Cume_P','Rank':'Cume_F'},axis=1,inplace=True)
    else:
        df.rename({'Rank':'Cume_P','Rank.1':'Cume_F'},axis=1,inplace=True)
    return df

def handle_finals_ranks(df):
    #For when Results sheet already splits finals ranks into 3 columns
    if 'Unnamed: 12' in df.columns.to_list() and 'Unnamed: 13' in df.columns.to_list():
        df.rename({'Finals':'F1','Unnamed: 12':'F2','Unnamed: 13':'F3'},axis=1,inplace=True) 
        df['F4'] = np.nan
        df['F5'] = np.nan
        return df
    
    if 'Unnamed: 13' in df.columns.to_list() and 'Unnamed: 14' in df.columns.to_list():
        df.rename({'Finals':'F1','Unnamed: 13':'F2','Unnamed: 14':'F3'},axis=1,inplace=True) 
        df['F4'] = np.nan
        df['F5'] = np.nan
        return df

    df['Finals'] = df['Finals'].apply(clean_ranks_down_to_integers)
    df['Finals'] = df['Finals'].astype('str')
    df['Finals'] = df['Finals'].apply(split_ranks_string_to_list) #'111' -> ['1','1','1']
    for i in range(0,5): #Creates F1, F2, F3, F4, and F5
        df[f'F{i+1}'] = (
            df['Finals']
            .str[i]
            .replace('0', np.nan)
            .astype('float64')
        )
    df.drop(['Finals'], axis=1, inplace=True)       
    return df

def calculate_recips(x):
    try:
        return 1 / int(x)
    except (ValueError, ZeroDivisionError):
        return 0

def calculate_recips_for_rounds(df, rd, rank_cols, output_col, rename_from=None):
    # Issues still: rk in [1,2,3] vs [1,2,3,4,5], and the columns dropped
    # also the columns summed together
    """rd is either 'P' or 'F'"""
    recips_col_name = "Recips" if rd == 'P' else 'Recips.1'
    df.rename({recips_col_name: f'Recips_{rd}'}, axis=1, inplace=True)
    for rk in ['1','2','3']:
        df[f'{rd}R{rk}'] = df[f'{rd}{rk}'].apply(calculate_recips)
    df['Recips_{rd}'] = df['{rd}R1'] + df['{rd}R2'] + df['{rd}R3']
    df['Recips_{rd}'] = round(df['Recips_{rd}'],2)
    df.drop(['{rd}R1','{rd}R2','{rd}R3'], axis=1, inplace=True)
    return df
    pass #!!!

def calculate_prelims_recips(df):
    df.rename({'Recips':'Recips_P'},axis=1,inplace=True)
    for rk in ['1','2','3']:
        df[f'PR{rk}'] = df[f'P{rk}'].apply(calculate_recips)
    df['Recips_P'] = df['PR1'] + df['PR2'] + df['PR3']
    df['Recips_P'] = round(df['Recips_P'],2)
    df.drop(['PR1','PR2','PR3'],axis=1,inplace=True)
    return df

def calculate_finals_recips(df):
    df.rename({'Recips.1':'Recips_F'},axis=1,inplace=True)
    for rk in ['1','2','3','4','5']:
        df[f'FR{rk}'] = df[f'F{rk}'].apply(calculate_recips)
    
    df['Recips_F'] = df['FR1'] + df['FR2'] + df['FR3'] + df['FR4'] + df['FR5']
    df['Recips_F'] = round(df['Recips_F'],2)
    df.drop(['FR1','FR2','FR3','FR4','FR5'],axis=1,inplace=True)
    return df

def evaluate_break_type(x):
    """Returns final_rd_rk, final_result, and break_type"""
    try:
        final_rd_rk = int(x)
        return final_rd_rk, final_rd_rk, 1 #1=Champs
    except ValueError:
        if pd.isna(x):  # Check for NaN
            return x, 'PrelimResult', 0
        final_rd_rk = int(x[0])

        if '(X)' in x:
            return final_rd_rk, final_rd_rk + 6, 2 #2=Honors
        if '(Y)' in x:
            return final_rd_rk, final_rd_rk + 12, 3 #3=Merit
        if '(Z)' in x:
            return final_rd_rk, final_rd_rk + 18, 4 #4=Consi

def create_break_columns(df):
    df['Finals.1'] = df['Finals.1'].apply(evaluate_break_type)
    
    # df['Final_Rd_Rk', 'FinalResult', 'Break'] = (
    #     )
    
    # df['Final_Rd_Rk'], df['FinalResult'], df['Break'] = (
    #     )
    
    df['Final_Rd_Rk'] = (
        df['Finals.1']
        .apply(lambda x: x[0])
        .astype(int, errors='ignore')
    )
    
    df['FinalResult'] = (
        df['Finals.1']
        .apply(lambda x: x[1])
        .astype(int, errors='ignore')
    )
    
    df['Break'] = (
        df['Finals.1']
        .apply(lambda x: x[2])
        .astype(int, errors='ignore')
    )
    return df

def add_prelim_result(df):
    data = []
    for i, row in df.iterrows():
        if i == 0:
            prelim_result = 1
            event_name = row['Event']
            data.append(prelim_result)
        else:
            if row['Event'] == event_name: #it's still the same event
                prelim_result += 1
            else:
                event_name = row['Event']
                prelim_result = 1
            data.append(prelim_result)
    df['PrelimResult'] = data
    return df

def fix_finalresult(df):
    data = []
    for i, row in df.iterrows():
        if row['FinalResult'] != 'PrelimResult':
            data.append(df['FinalResult'][i])
        else:
            data.append(df['PrelimResult'][i])
    df['FinalResult'] = data
    return df

def add_index_column(df):
    df.reset_index(inplace=True)
    df.rename({'index':'INDEX'},axis=1,inplace=True)
    df['INDEX'] = df['INDEX']+1 #1-indexed rather than 0-indexed
    return df

def sort_sheet(df):
    tournament_order = TOURNAMENTS[YEAR].keys()
    df['Tournament'] = pd.Categorical(df['Tournament'], tournament_order)
    df.sort_values(['Tournament', 'Event', 'FinalResult'], 
                   ascending=[False, True, True], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df  

def mimic_excel_column_name_conventions(df):
    # Replace NaN or None column names with "Unnamed: #"
    df.columns = [
        f"Unnamed: {i}" if col is None or (isinstance(col, float) and np.isnan(col)) else col
        for i, col in enumerate(df.columns)
    ]
    
    # Update duplicate column names with a ".1", ".2", etc. appended
    new_columns = pd.Series(df.columns)
    counts = new_columns.groupby(new_columns).cumcount()  # Track counts for each duplicate group
    df.columns = np.where(counts == 0, new_columns, new_columns + '.' + counts.astype(str))
    return df
    
def parse_raw_results(data):
    df_merged = pd.DataFrame()
    for tournament in progress(data):    
        df = data[tournament].copy()
        df = mimic_excel_column_name_conventions(df)
        df = add_blank_columns(df)
        
        df = define_prelim_rank_columns(df)
        df = handle_finals_ranks(df)
        df = calculate_prelims_recips(df)
        df = calculate_finals_recips(df)
        
        df = create_break_columns(df)
        df = add_prelim_result(df)
        if tournament == 'LSW':
            df = edg.fix_lsw_duo_prelims(df)
        df = fix_finalresult(df)
        
        df = drop_irrelevant_columns(df) 
        df = rename_columns(df)
        df = move_columns(df)
        
        df_merged = pd.concat([df_merged, df],axis=0)
    df_merged = sort_sheet(df_merged) 
    df_merged = add_index_column(df_merged)

    df_merged.replace('W', np.nan, inplace=True)
    df_merged = df_merged.apply(util.safe_to_numeric)
    if YEAR == '25-26':
        df_merged = edg.manually_update_nat_quals_info_semis(df_merged)
    return df_merged

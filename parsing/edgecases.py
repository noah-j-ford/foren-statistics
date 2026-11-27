import pandas as pd
import numpy as np
from config import YEAR
import utils as util


#### LSW Bullshit
def process_df_finals(df):
    df_finals = pd.DataFrame()
    df = util.drop_headers(df, 'Final round')
    
    df.reset_index(drop=True, inplace=True)
    event_groups = df.groupby('Event')
    for event_name, df_event in event_groups:
        #Drops Event header
        df_event = util.drop_event_header(df_event)
        df_event.reset_index(drop=True, inplace=True)

        columns = df_event.iloc[0,:].to_list()
        [columns[-3], columns[-2], columns[-1]] = ['Event', 'Tournament', 'Break']
        df_event.columns = columns
        
        df_event = util.drop_headers(df_event, columns[0])  # drop table headers
        try:
            df_event.drop(['Judges'], axis=1, inplace=True)
        except KeyError:
            pass
        df_event = df_event.dropna(axis=1, how='all')

        if len(df_event.columns) == 16:
            df_event.columns = ['Code', 'Competitor', 'Team', 'F1', 'F2', 'F3', 'F4',
                                'F5', 'Cume_TOTAL', 'Recips_TOTAL', 'Cume_F', 'Recips_F',
                                'FinalResult', 'Event', 'Tournament', 'Break']
        elif len(df_event.columns) == 14: #OID Champs at LSW 2026
            df_event.columns = ['Code', 'Competitor', 'Team', 'F1', 'F2','F3','F4','F5',
                                'Cume_F','Recips_F','FinalResult',
                                'Event','Tournament','Break']
            df_event['Cume_TOTAL'] = np.nan
            df_event['Recips_TOTAL'] = np.nan
            
            df_event['temp'] = (
                df_event['FinalResult'].fillna(0).astype(int).astype(str) + '_' +
                df_event['Break'].fillna(0).astype(int).astype(str)
                )

            df_event['FinalResult'] = df_event['temp'].apply(correct_oid_finalresult)
            df_event.drop(['temp'],axis=1,inplace=True)
            
        elif len(df_event.columns) == 12: #OID Honors? I Presume?
            df_event.columns = ['Code', 'Competitor', 'Team', 'F1', 'F2', 'F3',
                                'Cume_F', 'Recips_F', 'FinalResult', 'Event', 
                                'Tournament', 'Break']
            df_event['F4'] = np.nan
            df_event['F5'] = np.nan
            df_event['Cume_TOTAL'] = np.nan
            df_event['Recips_TOTAL'] = np.nan

            df_event['temp'] = (
                df_event['FinalResult'].fillna(0).astype(int).astype(str) + '_' +
                df_event['Break'].fillna(0).astype(int).astype(str)
                )

            df_event['FinalResult'] = df_event['temp'].apply(correct_oid_finalresult)
            df_event.drop(['temp'],axis=1,inplace=True)

        else:
            print(f"Something is wrong with: {event_name}")
            
        column_order = ['Code','Competitor', 'Team', 'F1', 'F2', 'F3', 'F4', 'F5',
                        'Cume_TOTAL', 'Recips_TOTAL', 'Cume_F', 'Recips_F', 
                        'FinalResult', 'Event', 'Tournament', 'Break']
        df_event = df_event.reindex(columns=column_order)
        df_finals = pd.concat([df_finals, df_event], axis=0)
    
    df_finals = df_finals.apply(util.safe_to_numeric)
    df_finals.reset_index(drop=True, inplace=True)
    return df_finals


def create_semi_sections_column(df):
    semi_sections, char = [[], 64] #ord('A') = 65, 'B' = 66, etc.
                                   #There's an initial header that will always add 1
                                   #on the first loop, so this is 64 instead of 65
    event_flag = 'DI'
    
    for i, row in df.iterrows():
        cell = row[0]
        event = row['Event']
        if event != event_flag:
            char = 64
            event_flag = event
        if cell.endswith(' round'):
            char +=1
        semi_sections.append(chr(char))
    df['Semi_Sec'] = semi_sections
    return df


def process_df_semis(df):
    df.reset_index(drop=True, inplace=True)
    df = create_semi_sections_column(df)

    df = df.dropna(axis=1, how='all')
    df = util.drop_headers(df, 'Semifinal round')
    df = util.drop_nan_rows(df, 3)  #drops semifinalist rows not in that section (and are thus nan)

    columns = df.iloc[0,:].to_list()
    [columns[-4], columns[-3], columns[-2], columns[-1]] = ['Event', 'Tournament', 'Break', 'Semi_Sec']

    [columns[3], columns[4], columns[5]] = ['S1','S2','S3']

    df.columns = columns
    df = util.drop_headers(df, columns[0])  # drop table headers
    df.rename({'Name':'Competitor',
               'All ranks':'Cume_ST',
               'All':'Recips_ST',
               'Rank':'Cume_S',
               'Recips':'Recips_S',
               'Place':'Semi_Result'}, 
              axis=1, inplace=True)

    df = df.apply(util.safe_to_numeric)

    # Sorting by primary and secondary score columns within each group
    df.sort_values(by=['Event', 'Semi_Sec', 'Cume_S', 'Recips_S'],
                   ascending=[True, True, True, False], inplace=True)
    # Ranking scores within each Event and Semifinal Section
    df['Semi_Rd_Rk'] = df.groupby(['Event', 'Semi_Sec']).cumcount() + 1

    df.reset_index(drop=True, inplace=True)
    return df


def create_finals_list(df):
    break_codes = {
        "Final":1, "Next-in Final":2, "Merit Final":3, "Consolation Final":4, "Semifinal":5,
        }

    finals_list, finals_name = [[],""]
    
    for i, row in df.iterrows():
        cell = row[0]
        if cell.endswith(' round'):
            finals_name = cell.replace(' round','')
        finals_list.append(finals_name)
    df['Break'] = finals_list 
    df['Break'] = df['Break'].map(break_codes)
    return df


def process_df_elim(df, sheet, tournament_name):
    df = util.drop_headers(df, 'Elimination round results')
    df.reset_index(drop=True, inplace=True)
    event_column_list = util.create_event_column_list(df, tournament_name)
    df['Event'] = event_column_list
    df['Tournament'] = sheet
    
    df = util.drop_headers(df, tournament_name)
    df = util.drop_nan_rows(df, 0)

    df = create_finals_list(df)

    df_finals = df[df['Break'] == 1]
    df_finals = process_df_finals(df_finals)

    df_semis = df[df['Break'] == 5]
    df_semis = process_df_semis(df_semis)

    return df_finals, df_semis


def append_semi_and_finals_data(df, df_finals, df_semis):
    for df_temp in [df, df_finals, df_semis]:
        df_temp['Event'] = df_temp['Event'].astype(str).str.upper()  # "INF" was converted to infinity
        df_temp['ID'] = df_temp['Code'] + df_temp['Event']
    df_finals.index = df_finals['ID']
    df_semis.index = df_semis['ID']

    data_finals = util.create_container(
        ['F1', 'F2', 'F3', 'Cume_F', 'Recips_F', 'FinalResult', 'F4', 'F5', 'Cume_TOTAL', 
         'Recips_TOTAL']
        )
                                        
    data_semis = util.create_container(
        ['S1', 'S2', 'S3', 'Cume_S', 'Recips_S', 'Cume_ST', 'Recips_ST', 'Semi_Sec', 'Semi_Rd_Rk',
         'Semi_Result']
        )

    for i, row in df.iterrows():
        ID = row['ID']
        for column, f_list in data_finals.items():
            if ID in df_finals['ID'].to_list():
                f_list.append(df_finals.loc[ID, column])
            else:
                f_list.append(np.nan)
        for column, s_list in data_semis.items():
            if ID in df_semis['ID'].to_list():
                s_list.append(df_semis.loc[ID, column])
            else:
                s_list.append(np.nan)
    df_finals, df_semis = pd.DataFrame(data_finals), pd.DataFrame(data_semis)
    df = pd.concat([df, df_finals, df_semis], axis=1)
    return df


def check_for_elim_rounds(df, sheet, tournament_name):
    try:
        idx = df[0].to_list().index('Elimination round results')-2
        df_elim = df.iloc[idx:,:]
        df = df.iloc[:idx,:]
        df = df.dropna(axis=1, how='all')
        df_finals, df_semis = process_df_elim(df_elim, sheet, tournament_name)
        return df, df_finals, df_semis
    except ValueError:
        return df, None, None


def attach_elim_data(df, df_finals, df_semis):
    df = append_semi_and_finals_data(df, df_finals, df_semis)
    df['Finals'] = (
        df['F1'].fillna(0).astype(int).astype(str) + ', ' +
        df['F2'].fillna(0).astype(int).astype(str) + ', ' +
        df['F3'].fillna(0).astype(int).astype(str) + ', ' +
        df['F4'].fillna(0).astype(int).astype(str) + ', ' +
        df['F5'].fillna(0).astype(int).astype(str)
        )
    df['Finals'] = df['Finals'].replace('0, 0, 0, 0, 0', np.nan)

    df.drop(['F1','F2','F3','F4','F5'], axis=1, inplace=True)
    df = manually_fix_oids(df)
    df.rename({'Cume_F':'Rank',
               'Recips_F':'Recips',
               'FinalResult':'Finals.1'},
              axis=1, inplace=True)
    return df


def correct_oid_finalresult(x):
    replacements = {'1':'','2':' (X)','3':' (Y)','4':' (Z)'}
    final_rd_rk = x.split('_')[0]
    break_value = x.split('_')[1]
    value = final_rd_rk + replacements[break_value]
    return value


def manually_fix_oids(df):
    manual_dict = {
        '24-25': {
            'D135OID':
                 {'Finals':'1, 1, 1', 'Cume_F':3,'Recips_F':3,'FinalResult':'1 (X)'},
            'I118OID':
                 {'Finals':'2, 2, 2', 'Cume_F':6, 'Recips_F':1.5, 'FinalResult':'2 (X)'},
            'H107OID':
                 {'Finals':'3, 3, 3', 'Cume_F':9, 'Recips_F':1, 'FinalResult':'3 (X)'},
            'H102OID':
                 {'Finals':'4, 4, 4', 'Cume_F':12, 'Recips_F':0.75, 'FinalResult':'4 (X)'},
            'Z110OID':
                 {'Finals':'1, 3, 1', 'Cume_F':5, 'Recips_F':2.33, 'FinalResult':'1 (Y)'}, 
            'J105OID':
                 {'Finals':'4, 1, 2', 'Cume_F':7, 'Recips_F':1.75, 'FinalResult':'2 (Y)'},
            'AK107OID':
                 {'Finals':'3, 2, 3', 'Cume_F':8, 'Recips_F':1.17, 'FinalResult':'3 (Y)'},
            'Z105OID':
                 {'Finals':'2, 4, 4', 'Cume_F':10, 'Recips_F':1, 'FinalResult':'4 (Y)'},
             },
        '25-26': {
            'T101OID':
                 {'Finals':'1, 2, 1', 'Cume_F':4, 'Recips_F':2.5, 'Final_Result':'1 (X)'},
            'AA109OID':
                 {'Finals':'2, 1, 2', 'Cume_F':5, 'Recips_F':2, 'Final_Result':'2 (X)'},
            'SS131OID':
                 {'Finals':'3, 4, 3', 'Cume_F':10, 'Recips_F':0.92, 'Final_Result':'3 (X)'},
            'GG101OID':
                 {'Finals':'4, 3, 4', 'Cume_F':11, 'Recips_F':0.83, 'Final_Result':'4 (X)'},
            },
        }
    df.index = df['ID']
    for code, data in manual_dict[YEAR].items():
        for variable in data:
            df.at[code, variable] = manual_dict[YEAR][code][variable]

    df.reset_index(drop=True, inplace=True)
    df.drop(['ID'],axis=1,inplace=True)
    return df


def fix_lsw_duo_prelims(df):
    data = []
    for i, row in df.iterrows():
        event_name = row['Event']
        prelim_result = row['PrelimResult']
        if event_name == 'DUO':
            if prelim_result > 24: #24 is the number of duet entries
                prelim_result = prelim_result-24
        data.append(prelim_result)
    df['PrelimResult'] = data
    return df


def manually_update_nat_quals_info_semis(df):
    update_data = {
        'Moyo Ogun':  # name functions as speaker code
            {'S1':2, 'S2':2, 'S3':2, 'Cume_S':6, 
             'Recips_ST':13, 'Semi_Sec':'B', 'Semi_Rd_Rk':2, 'Semi_Result':1},
        'Anoushka Jacob':
            {'S1':3, 'S2':1, 'S3':1, 'Cume_S':5, 
             'Recips_ST':13, 'Semi_Sec':'A', 'Semi_Rd_Rk':1, 'Semi_Result':2},
        'Nya Curtis':
            {'S1':1, 'S2':2, 'S3':2, 'Cume_S':5, 
             'Recips_ST':14, 'Semi_Sec':'A', 'Semi_Rd_Rk':2, 'Semi_Result':3},
        'Meher Mahl':
            {'S1':4, 'S2':1, 'S3':1, 'Cume_S':8,
             'Recips_ST':16, 'Semi_Sec':'B', 'Semi_Rd_Rk':1, 'Semi_Result':4},
        'Claire Timperley':
            {'S1':1, 'S2':3, 'S3':4, 'Cume_S':6,
             'Recips_ST':17, 'Semi_Sec':'B', 'Semi_Rd_Rk':3, 'Semi_Result':5},
        'Braelyn Bouton':
            {'S1':2, 'S2':3, 'S3':4, 'Cume_S':9,
             'Recips_ST':18, 'Semi_Sec':'A', 'Semi_Rd_Rk':3, 'Semi_Result':6},
        'Brooke Samson':
            {'S1':3, 'S2':4, 'S3':3, 'Cume_S':10,
             'Recips_ST':21, 'Semi_Sec':'B', 'Semi_Rd_Rk':4, 'Semi_Result':7},
        'Ashmiza Shaik':
            {'S1':4, 'S2':4, 'S3':3, 'Cume_S':11,
             'Recips_ST':22, 'Semi_Sec':'A', 'Semi_Rd_Rk':4, 'Semi_Result':8},
        }
    for i, row in df.iterrows():
        if row['Tournament'] == 'NQ_N':
            if row['Event'] == 'INF':
                if row['Competitor'] in update_data.keys():
                    data = update_data[row['Competitor']]
                    for column, value in data.items():
                        col_index = df.columns.to_list().index(column)
                        df.iat[i, col_index] = value
    return df
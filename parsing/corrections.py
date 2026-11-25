from config import YEAR


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
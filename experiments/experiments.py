import pandas as pd
from config import ROOT, NE_NORTH_SCHOOLS

def create_specifier_list():
    """Used for Nat Quals"""
    df = pd.read_excel(ROOT + r'\ELO.xlsx')
    df = df[df['Tm'].isin(NE_NORTH_SCHOOLS)]
    df.reset_index(drop=True, inplace=True)
    df = df.drop_duplicates(subset='Competitor', keep="first")
    
    specifier_list = df['Competitor'].to_list() 
    specifier_list.append(0)
    return specifier_list

# %% from local minima - used for visualizing/creating elo tier breaks

# from common_methods import *
import numpy
from numpy import array, linspace
from sklearn.neighbors import KernelDensity
from matplotlib import pyplot
from scipy.signal import argrelextrema
from config import ROOT
import pandas as pd


def greatest_diffs_cluster(elo_list, cluster_count=14):
	boundaries = sorted(list(range(len(elo_list) - 1)), key=lambda i: elo_list[i + 1] - elo_list[i], reverse=True)
	return sorted([elo_list[b] for b in boundaries[:cluster_count]])


def kde_cluster(elo_list, K=10, save=False, index=0):
    global minima_shown
    # elo_list = list of elo scores as integers
    # k = number of minima/tiers, not the Elo k value
    
    pyplot.clf()
    min_elo, max_elo = min(elo_list), max(elo_list)
    
    elo_array = array(elo_list).reshape(-1, 1)
    kde = KernelDensity(bandwidth=K).fit(elo_array)
    
    space = linspace(min_elo, max_elo, num=int(max_elo - min_elo) * 2)
    estimates = kde.score_samples(space.reshape(-1, 1))
    
    mins = argrelextrema(estimates, numpy.less)[0]
    
    pyplot.plot(space, estimates)
    pyplot.plot(space[mins], estimates[mins], 'ro')
    pyplot.title(f"K: {K:.1f} - Number of minima: {len(mins)}")
    if len(mins) not in minima_shown:
        # minima_shown.append(len(mins))
        pyplot.show()
    
    if save:
        pyplot.savefig(f"kdes/{index}.png", dpi=320)
    
    return [space[k] for k in mins]

def get_elo_list():
    df = pd.read_excel(ROOT + r'\ELO.xlsx')
    elo_list = df['ELO'].sort_values().to_list()
    return elo_list

def do_local_minima_stuff():
    minima_shown = range(12)

    elo_list = get_elo_list()
    
    # View plots
    for b in range(1, 140):  # originally range(1, 281) [k = 0.1 to 28.0]
    	kde_cluster(elo_list, K=b/10, save=False, index=b)
    
    kde_boundaries = kde_cluster(elo_list, K=13.4)
    print(kde_boundaries)
    # greatest_diff_boundaries = greatest_diffs_cluster(elo_list, cluster_count=14)
    
    # print('\n\n\n\n\n\n\n\n'*5, greatest_diff_boundaries)
    tiers = {"F":517, #0-517
             "D-":610, #518-610
             "D":750, #611-750
             "D+":850, #751-850 manual break added
             "C-":956, #851-956
             "C":1023, #957-1023 
             "C+":1132, #1024-1132
             "B-":1229, #1133-1229
             "B":1271, #1230-1271
             "B+":1347, #1272-1347
             "A-":1413, #1348-1413
             "A":1488, #1414-1488
             "A+":1600, #1489-1600
             "S":1742, #1601-1742
             "S+":9999} #1742+
    
    tier_names = ["F", "D-", "D", "D+", "C-", "C", "B-", "B", "B+", "A-", "A", "A+", "S", "S+"]
    tier_colors = ["00b050", "24bb45", "4bc735", "6fd226", "93de15", "b8e900",
    		               "dcf400", "ffff00", "ffd600", "ffac00", "ff5d00", "ff5700",
    		               "ff2b00", "ff0000", "ff0000"]
		

# %% Novice statistics - does not work with updated pipeline yet
import results as rst #Clean_Base_Results_Format,Automated_Results,Process_Results
import sections as sct #convert_raw_to_base_xlsx, concatenate_base_to_master_sheet, create_speaker_section_sheet, get_competitor_section_stats
import h2h #make_h2h, class_a_h2h
import elo #create_elo_sections_sheet, run_elo
import depthchart as dpt #make_depth_chart
import os

"""
Manual Novice changes beyond what varsity requires:
    changing Results.xlsx header fields bc finals don't exist
    Drop "Novice" from event names in Results (Raw Format).xlsx AND Sections (Raw Format).xlsx
"""


def update_4n6_novice(tourney_sheets, year='25-26', NO_OID_FLAG=0, most_recent_tournament=False):
    #### RESULTS
    rst.process_results(tourney_sheets, year)
    print("RESULTS DONE!    ", end='') 
    
    #### SECTIONS
    sct.convert_raw_to_base_xlsx(tourney_sheets, year) 
    sct.concatenate_base_to_master_sheet(tourney_sheets, year)
    sct.create_speaker_section_sheet(year) 
    sct.get_competitor_section_stats(year)   
    print("\rSECTIONS DONE!   ", end='', flush=True) 

    #### H2Hs
    h2h.make_h2hs(year, NO_OID_FLAG=NO_OID_FLAG)    
    h2h.class_a_h2h(year)  
    print("\rH2H DONE!        ", end='', flush=True) 

    #### ELO
    elo.create_elo_sections_sheet(year)    
    elo.run_elo(year, most_recent_tournament=most_recent_tournament)   
    print("\rELO DONE!        ", end='', flush=True)

    #### DEPTH CHART
    dpt.make_depth_chart(year=year)   
    print("\rDEPTH CHART DONE!",end='', flush=True)

# novice_sheets = ['MN Novice', 'MW GOLD', 'PLVS', 'Pius X', 'Bryan GOLD']
# update_4n6_novice(novice_sheets, year='25-26/Novice')

# %% update_4n6_for_eval - deprecated, does not work with current program structure

import results as rst #Clean_Base_Results_Format,Automated_Results,Process_Results
import sections as sct #convert_raw_to_base_xlsx, concatenate_base_to_master_sheet, create_speaker_section_sheet, get_competitor_section_stats
import h2h #make_h2h, class_a_h2h
import elo #create_elo_sections_sheet, run_elo
import os

def update_4n6_for_eval(tourney_sheets_all, year='24-25', NO_OID_FLAG=0, most_recent_tournament=False):
    no_oid_tournaments = {'24-25':{'PLVS', 'OBVH'}, '23-24':{'BW','PLVH'}}
    for i in range(len(tourney_sheets_all)):
        tourney_sheets = tourney_sheets_all[:i+1]
        most_recent_tournament = tourney_sheets[-1]

        NO_OID_FLAG = 1 if most_recent_tournament in no_oid_tournaments[year] else 0
    
        #### RESULTS
        rst.process_results(tourney_sheets, year)
        
        competitor_location = rf"C:\Users\noahj\Desktop\Forensics\{year}\Competitor Stats.xlsx"
        competitor_destination = rf"C:\Users\noahj\Desktop\Forensics\{year}\Code\Sifting\Competitor Stats ({most_recent_tournament}).xlsx"
        os.rename(competitor_location, competitor_destination)
        
        #### SECTIONS
        sct.convert_raw_to_base_xlsx(tourney_sheets, year)
        sct.concatenate_base_to_master_sheet(tourney_sheets, year)
        # Speaker by Speaker
        sct.create_speaker_section_sheet(year)
        #Master By Rounds
        sct.get_competitor_section_stats(year)
        
        #### H2Hs
        h2h.make_h2hs(year, NO_OID_FLAG=NO_OID_FLAG)
    
        #### ELO
        elo.create_elo_sections_sheet(year)
        
        section_location = rf"C:\Users\noahj\Desktop\Forensics\{year}\Code\Sections (ELO).xlsx"
        section_destination = rf"C:\Users\noahj\Desktop\Forensics\{year}\Code\Sifting\Sections (ELO) ({most_recent_tournament}).xlsx"
        os.rename(section_location, section_destination)
        
        elo.run_elo_for_eval(year, most_recent_tournament=most_recent_tournament)
        

# tourney_sheets_all = ['BW','PLVH','MS','Pius X','PLVS','Norr','LH','Creighton Prep','LSE','Doane','EHS','LSW','LNE','MW','LNS','Marian','MN','LE']

# update_4n6_for_eval(tourney_sheets_all, year='23-24')

# %% Elo for eval stuff - also does not work with current pipeline

def create_full_competitor_dict_for_eval(year, BASE_RATING=1000, most_recent_tournament=False):
    df_competitors = pd.read_excel(f'C:/Users/noahj/Desktop/Forensics/{year}/Code/Sifting/Competitor Stats ({most_recent_tournament}).xlsx')
    event_groups = df_competitors.groupby('Event')
    elo_data = {}

    for e in ['DI', 'DUO', 'ENT', 'EXT', 'HI', 'IMP', 'INF', 'OID', 'OO', 'POE', 'POI']:
        elo_data.update({e:{}})
    for event in event_groups:
        event_name = str(event[0])
        df_event = event[1].reset_index(drop=True)
        for i in range(0,len(df_event)):
            competitor_name = df_event['Competitor'][i]
            player_temp = Player(competitor_name,rating=BASE_RATING)
            elo_data[event_name].update({competitor_name:player_temp})
    return elo_data, df_competitors

def initialize_elo_for_eval(K_VALUE,D_VALUE,EXP, year, most_recent_tournament=False):
    elo_data, df_competitors = create_full_competitor_dict_for_eval(year, most_recent_tournament=most_recent_tournament)
    
    Elo = MultiElo(k_value=K_VALUE,d_value=D_VALUE, score_function_base=EXP)
    StableElo = MultiElo(k_value=(K_VALUE*.75),d_value=D_VALUE, score_function_base=EXP)
    ChampsElo = MultiElo(k_value=K_VALUE/3,d_value=D_VALUE,score_function_base=1)
    StableChampsElo = MultiElo(k_value=(K_VALUE*.75)/3,d_value=D_VALUE,score_function_base=1)
    
    df = pd.read_excel(f'C:/Users/noahj/Desktop/Forensics/{year}/Code/Sifting/Sections (ELO) ({most_recent_tournament}).xlsx')
    df = map_tournament_order_onto_spreadsheet(df, year)
    return df, elo_data, Elo, df_competitors, ChampsElo, StableElo, StableChampsElo

def save_elo_formatting_for_eval(df, year, most_recent_tournament=False):
    for column in ['ELO','Up%','Break%']:
        df[column] = round(df[column])
    for column in ['AvgRk','AvgChampsRk']:
        df[column] = round(df[column],2)
    df['Tier'] = df['ELO'].apply(get_elo_tier)
    df = df[['Event', 'Competitor', 'Tm', 'ELO', 'Ballots', 'AvgRk', 'AvgChampsRk', 'Up%',
             'Break%', 'Class', 'District', 'Tier','DepthPts']]
    if most_recent_tournament==False:
        writer = pd.ExcelWriter(f'C:/Users/noahj/Desktop/Forensics/{year}/ELO.xlsx',
                                engine='xlsxwriter')
    else:
        writer = pd.ExcelWriter(f'C:/Users/noahj/Desktop/Forensics/{year}/Code/ELO/ELO ({most_recent_tournament}).xlsx', engine='xlsxwriter')
    df.to_excel(writer,sheet_name='ELO',index=False)  
    fmt_header = writer.book.add_format({"bold":True,
                                  "font_name": "Calibri",
                                  "font_size":"8",
                                  "align":"left",
                                  "valign":"top",
                                  "bold":True})
    fmt = writer.book.add_format({"font_name": "Calibri",
                                  "font_size":"8",
                                  "align":"left",
                                  "valign":"top"})
    writer.sheets['ELO'].set_column('A:A',width=2.5,cell_format=fmt)
    writer.sheets['ELO'].set_column('B:B',width=14,cell_format=fmt)
    writer.sheets['ELO'].set_column('C:C',width=4.5,cell_format=fmt)
    writer.sheets['ELO'].set_column('D:L',width=4,cell_format=fmt)
    writer.sheets['ELO'].set_column('M:M',width=7.5,cell_format=fmt)
    writer.sheets['ELO'].set_column('N:N',width=4,cell_format=fmt)

    # Apply the format to the header row
    for col_num, value in enumerate(df.columns.values):
        writer.sheets['ELO'].write(0, col_num, value, fmt_header)
    writer.sheets['ELO'].set_default_row(10.5)
    return writer

def run_elo_for_eval(year, K_VALUE=100,D_VALUE=500,EXP=1, most_recent_tournament=False):
    df, elo_data, Elo, df_competitors, ChampsElo, StableElo, StableChampsElo, = initialize_elo_for_eval(K_VALUE, D_VALUE, EXP, year, most_recent_tournament) #Consistently 5.0 seconds
    elo_data = calculate_elo_scores(df, elo_data, Elo, ChampsElo, StableElo, StableChampsElo)
    df_elo = create_elo_spreadsheet(elo_data)
    df_elo = expand_elo_stats(df_elo, df_competitors)
    writer = save_elo_formatting_for_eval(df_elo, year, most_recent_tournament=most_recent_tournament)
    writer.close()
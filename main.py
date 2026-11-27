from tqdm import tqdm

import parsing.results as prs
import parsing.sections as psc
from parsing import attach_sections
import stats.competitors as stc
import stats.schools as sch
import stats.tournaments as stn
import stats.judges as jdg
import stats.h2h as h2h
import stats.elo as elo
import stats.depthchart as dpt

def update_4n6(NO_OID_FLAG=0, most_recent_tournament=False):
    with tqdm(total=1000) as progress_bar:
        
        #### RESULTS
        df = prs.process_results()  # returns Results by Entry 
        stc.create_stats_by_competitor_sheet(df)
        sch.create_school_ranks_sheets(df)  
        stn.create_tournament_stats_sheet(df)
        progress_bar.update(76) #0:25   ~7.6%

        #### PARSE SECTIONS
        psc.parse_raw_sections()  # creates Sections by Room (fka Speaker by Speaker)
        attach_sections.to_entries()  # appends section data to Results by Entry (fka Master by Rounds)
        progress_bar.update(27+88+237)  #0:29  ~8.8%

        
        #### JUDGES (Rounds, Ballots, Error scores)
        jdg.process_judges()
        progress_bar.update(137)  #0:45  ~13.7%

        #### H2Hs
        h2h.make_h2hs(NO_OID_FLAG=NO_OID_FLAG) 
        progress_bar.update(200)  #0:36  ~10.9%

        #### ELO
        elo.create_elo_sections_sheet() 
        elo.run_elo(most_recent_tournament=most_recent_tournament)
        progress_bar.update(228)  #1:07  ~20.4%

        #### DEPTH CHART
        dpt.make_depth_chart() 
        progress_bar.update(4)  #1:07  ~20.4%

if __name__ == "__main__":
    update_4n6()



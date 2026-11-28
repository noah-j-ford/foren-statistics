import parsing.results
import parsing.sections
from parsing import attach_sections
import stats.competitors
import stats.schools
import stats.tournaments
import stats.judges
import stats.h2h as h2h
import stats.elo as elo
import stats.depthchart as dpt
from reports.timing import Stages, STAGE_NAMES

def update_4n6():
    stages = Stages(STAGE_NAMES)
    
    #### RESULTS
    with stages.stage('Cleaning raw results...'):  # 2.14%
        data = parsing.results.clean_raw_results()
    with stages.stage('Parsing results...'):  # 1.52%
        results_by_entry = parsing.results.parse_raw_results(data)
    with stages.stage('Getting competitor stats...'):  # 16.91%
        stats_by_competitor = stats.competitors.create_stats_by_competitor(results_by_entry)
    with stages.stage('Getting school stats...'):  # 1.44%
        stats.schools.create_stats_by_school(results_by_entry)
    with stages.stage('Getting tournament stats...'):  # 0.4%
        stats.tournaments.create_stats_by_tournament(results_by_entry)

    #### PARSE SECTIONS
    with stages.stage('Parsing raw sections...'):  # 2.5%
        sections_by_judge, sections_by_room = parsing.sections.parse_raw_sections()
    with stages.stage('Attaching sections to entries...'):  # 11.94%
        results_by_entry = attach_sections.to_entries(results_by_entry, sections_by_room)

    
    #### JUDGES (Rounds, Ballots, Error scores)
    with stages.stage('Creating sections by judge...'):  # 34.19%
        sections_by_judge = stats.judges.create_sections_by_judge(results_by_entry, sections_by_judge)
    with stages.stage('Getting stats by judge...'):  # 3.55%
        stats.judges.create_stats_by_judge(sections_by_judge)

    #### H2Hs
    with stages.stage('Simulating head-to-heads...'):  # 39.33%
        h2h.make_h2hs(results_by_entry) 

    #### ELO
    with stages.stage('Creating elo sections by room...'):  # 1.53%
        sections_by_room = elo.create_elo_sections_sheet(results_by_entry, sections_by_room)
    with stages.stage('Running full Elo simulations...'):  # 30.26%
        df_elo = elo.run_elo(stats_by_competitor, sections_by_room)

    #### DEPTH CHART
    with stages.stage('Creating the depth chart...'):  # 0.67%
        dpt.make_depth_chart(stats_by_competitor, df_elo) 
    stages.save()

if __name__ == "__main__":
    update_4n6()



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
    with stages.stage('clean results'):
        data = parsing.results.clean_raw_results()
    with stages.stage('parse results'):
        results_by_entry = parsing.results.parse_raw_results(data)
    with stages.stage('competitor stats'):
        pass
        stats_by_competitor = stats.competitors.create_stats_by_competitor(results_by_entry)
    with stages.stage('school stats'):
        pass
        stats.schools.create_stats_by_school(results_by_entry)
    with stages.stage('tournament stats'):
        pass
        stats.tournaments.create_stats_by_tournament(results_by_entry)

    #### PARSE SECTIONS
    with stages.stage('parse sections'):
        sections_by_judge, sections_by_room = parsing.sections.parse_raw_sections()
    with stages.stage('attach sections to entries'):
        results_by_entry = attach_sections.to_entries(results_by_entry, sections_by_room)

    
    #### JUDGES (Rounds, Ballots, Error scores)
    with stages.stage('sections by judge'):
        pass
        sections_by_judge = stats.judges.create_sections_by_judge(results_by_entry, sections_by_judge)
    with stages.stage('stats by judge'):
        pass
        stats.judges.create_stats_by_judge(sections_by_judge)

    #### H2Hs
    with stages.stage('h2hs'):
        pass
        h2h.make_h2hs(results_by_entry) 

    #### ELO
    with stages.stage('elo sections by room'):
        sections_by_room = elo.create_elo_sections_sheet(results_by_entry, sections_by_room)
    with stages.stage('run elo'):
        df_elo = elo.run_elo(stats_by_competitor, sections_by_room)

    #### DEPTH CHART
    with stages.stage('depth chart'):
        dpt.make_depth_chart(stats_by_competitor, df_elo) 
    stages.save()

if __name__ == "__main__":
    update_4n6()



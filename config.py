YEAR = '25-26'
MOST_RECENT_TOURNAMENT = 'A4'

ROOT = fr"C:\Users\noahj\Desktop\Forensics\{YEAR}"
NAME_CORRECTIONS_PATH = r"C:\Users\noahj\Desktop\Forensics\Code\Standardization.xlsx"
EVENT_LIST = ['DI', 'DUO', 'ENT', 'EXT', 'HI', 'IMP', 'INF', 'OID', 'OO', 'POE', 'POI']
ROUND_NAMES = ['1', '2', '3', 'Final', 'Semifinal']  # only used by stats_sections...

TOURNAMENTS = {
    '26-27': {
        'PLVS':1, 'OBVH':2, 'MS':3, 'Pius X':4, 'Norris':5, 'LH':6, 'PLVH':7, 'LSE':8,
        'Fre':9, 'GE':10, 'RC':11, 'SFL':12, 'EHS':13, 'LSW':14, 'LNE':15, 'MW':16,
        'BW':17, 'LNS':18, 'Marian':19, 'MN':20, 'LE':21, 
        'NQ_N':22, 'NQ_N DX':23, 'NQ_S':24, 'NQ_S DX':25, 
        'A1':26, 'A2':27, 'A3':28, 'A4':29,
    },
    
    '25-26': {
        'OBVH':1, 'PLVS':2, 'MS':3, 'Pius X':4, 'Norris':5, 'LH':6, 'PLVH':7, 'LSE':8,
        'Fre':9, 'GE':10, 'RC':11, 'SFL':12, 'EHS':13, 'LSW':14, 'LNE':15, 'MW':16,
        'BW':17, 'LNS':18, 'Marian':19, 'MN':20, 'LE':21, 
        'NQ_N':22, 'NQ_N DX':23, 'NQ_S':24, 'NQ_S DX':25, 
        'A1':26, 'A2':27, 'A3':28, 'A4':29,
    },
    
    '25-26/Novice': {
        'MN Novice':1, 'MW GOLD':2, 'PLVS':3, 'Pius X':4, 'Bryan GOLD':5, 'LH':6,
        'MS GOLD':7, '__ GOLD':8,
    },
    
    '24-25': {
        'PLVS':1, 'OBVH':2, 'MS':3, 'Pius X':4, 'LNK':5, 'Norr':6, 'LH':7, 'LSE':8,
        'Fre':9, 'EHS':10, 'LSW':11, 'LNE':12, 'MW':13,
        'BW':14, 'LNS':15, 'Marian':16, 'MN':17, 'LE':18,
        'NQ_N':19, 'NQ_S':20, 'A1':21, 'A2':22, 'A3':23, 'A4':24,          
    },
    
    '23-24':{
        'BW':1,'PLVH':2,'MS':3,'Pius X':4, 'Norr':5,'PLVS':6,'LH':7,'Creighton Prep':8,'LSE':9,
        
        'Doane':10,'Westside':11,'RC':12,'EHS':13,'LSW':14,'LNE':15,'MW':16,
        'LNS':17,'Marian':18,'MN':19,'LE':20,'NQ_N':21,'NQ_S':22,'A1':23,'A4':24,
    },
}


NO_JUDGE_SHEETS = ["SFL", "NQ_N", "NQ_N DX", "NQ_S", "NQ_S DX", "A3", "A4"]

NE_NORTH_SCHOOLS = ['MN','LSW','MW','Norf','Fre','OBVH','Scotus','Marian','Benn','MS']

ELO_K_VALUE = 100
ELO_D_VALUE = 500
ELO_EXP = 1
BASE_RATING = 1000

NO_OID_FLAG = 0
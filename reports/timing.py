import pstats
import pandas as pd

import json, time
from contextlib import contextmanager
from pathlib import Path
from tqdm import tqdm
from config import TIMINGS_PATH

TIMINGS = Path(TIMINGS_PATH)
STAGE_NAMES = ['Cleaning raw results...', 
               'Parsing results...', 
               'Getting competitor stats...',
               'Getting school stats...',             # N/A progress
               'Getting tournament stats...',         # N/A progress
               'Parsing raw sections...', 
               'Attaching sections to entries...',
               'Creating sections by judge...',
               'Getting stats by judge...',
               'Simulating head-to-heads...', 
               'Creating elo sections by room...',
               'Running full Elo simulations...', 
               'Creating the depth chart...',         # N/A progress
               ]

OVERALL_TOTAL = 1000

class StageHandle:
    def __init__(self, parent, inner, weight, total):
        self.parent, self.inner, self.weight, self.total = parent, inner, weight, total
        self.credited = 0.0

    def update(self, n=1):
        self.inner.update(n)
        if self.total:
            amount = min(self.weight * n / self.total,
                         self.weight - self.credited)   # never exceed the stage's share
            if amount > 0:
                self.credited += amount
                self.parent.bar.update(amount)
                
    def wrap(self, iterable, total=None):
        total = total or (len(iterable) if hasattr(iterable, '__len__') else None)
        if total:
            self.total = total
            self.inner.total = total
            self.inner.refresh()
        for item in iterable:
            yield item
            self.update()


class Stages:
    current = None   # the active StageHandle, if any

    def __init__(self, names):
        last = json.loads(TIMINGS.read_text()) if TIMINGS.exists() else {}
        default = OVERALL_TOTAL / len(last) if last else 1.0
        self.weights = {n: last.get(n, default) for n in names}
        self.base = 0.0          # summed weight of completed stages
        self.new = {}
        self.bar = tqdm(total=OVERALL_TOTAL, position=0, desc='Overall',
                        bar_format='{desc} {percentage:3.0f}%|{bar}| {elapsed}<{remaining}')

    @contextmanager
    def stage(self, name, total=None):
        w = self.weights[name]
        inner = tqdm(total=total, position=1, leave=False, desc=name, unit='it')
        handle = StageHandle(self, inner, w, total)
        Stages.current = handle
        t0 = time.perf_counter()
        try:
            yield handle
        finally:
            Stages.current = None
            inner.close()
        self.new[name] = time.perf_counter() - t0
        self.base += w
        self.bar.n = self.base          # snap to exact value, fixing float drift
        self.bar.refresh()

    def save(self):
        total = sum(self.new.values())
        for name, t in self.new.items():
            self.new[name] = max(1, round((t / total) * OVERALL_TOTAL))
        TIMINGS.write_text(json.dumps(self.new))
        self.bar.n = OVERALL_TOTAL
        self.bar.refresh()
        self.bar.close()
        

def progress(iterable, total=None):
    """Wrap a loop's iterable in the active stage's bar.
    Returns the iterable unchanged when no stage is active (notebooks, tests)."""
    if Stages.current is None:
        return iterable
    return Stages.current.wrap(iterable, total)


def get_profiler_stats():
    # command prompt: python -m cProfile -o run_11_26_26.prof main.py
    profile_path = r"C:\Users\noahj\Desktop\Forensics\Code\foren-statistics\run_11_26_26.prof"
    
    p = pstats.Stats(profile_path).sort_stats("cumulative")
    rows = []
    for (filename, line, func_name), (cc, nc, tt, ct, callers) in p.stats.items():
        rows.append({
            "filename": filename,
            "line": line,
            "function": func_name,
            "primitive_calls": cc,
            "total_calls": nc,
            "tottime": tt,
            "percall_tot": tt / nc if nc else 0,
            "cumtime": ct,
            "percall_cum": ct / cc if cc else 0,
        })
    
    df = pd.DataFrame(rows).sort_values(by="cumtime", ascending=False)
    
    df.to_excel("Profile Times.xlsx", index=False)
    
    
# %%
# total = 27.71727160003502
# pcts = {"clean results": 0.5926439000031678, 
# "parse results": 0.4203191999986302,
#  "competitor stats": 4.688294400002633, 
#  "school stats": 0.3988400000016554, 
#  "tournament stats": 0.11144310000236146,
#   "parse sections": 0.6916168000025209,
#    "attach sections to entries": 3.309597200001008,
#     "sections by judge": 9.477146400000493,
#      "stats by judge": 0.9839353999996092, 
#      "h2hs": 10.902149000001373, 
#      "elo sections by room": 0.42336100000102306, 
# "run elo": 8.38860850000492, 
# "depth chart": 0.18653940000513103}

# for st, val in pcts.items():
#     print(round(val/total, 4), st)
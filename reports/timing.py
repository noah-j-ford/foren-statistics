import pstats
import pandas as pd

import json, time
from contextlib import contextmanager
from pathlib import Path
from tqdm import tqdm
from config import ROOT

TIMINGS = Path(ROOT) / "timings.json"

class Stages:
    def __init__(self, names):
        last = json.loads(TIMINGS.read_text()) if TIMINGS.exists() else {}
        default = sum(last.values()) / len(last) if last else 1.0
        self.weights = {n: last.get(n, default) for n in names}
        self.bar = tqdm(total=sum(self.weights.values()))
        self.new = {}

    @contextmanager
    def stage(self, name):
        t0 = time.perf_counter()
        yield
        self.new[name] = time.perf_counter() - t0
        self.bar.update(self.weights[name])

    def save(self):
        TIMINGS.write_text(json.dumps(self.new))

def get_profiler_stats():
    profile_path = r"C:\Users\noahj\Desktop\Forensics\Code\foren-statistics\run.prof"
    
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
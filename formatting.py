BASE = {
    "font_name": "Calibri",
    "font_size": 8,
    "align": "left",
    "valign": "top",
    }

HEADER = {
    "font_name": "Calibri",
    "font_size": 8,
    "align": "left",
    "valign": "top",
    "bold": True,
    }

ROTATED_HEADER = {  # ROTATED header, for h2h sheets (?)
    "font_name": "Calibri",
    "font_size": 8, 
    "align": "center", 
    "rotation": 90,
    }



LAYOUTS = {
    "results_by_entry": {"cols": {
        'A:B':4, 'C:C':3, 'D:F':4, 'G:G':3, 'H:H':12, 'I:K':1, 'L:N':3,'O:O':8, 'P:R':1, 'S:V':3,
        'W:W':8, 'X:BD':3, 'BE:BU':1, 'BV:BW':2,
        }, "rotated_header": False},
    
    "judge_stats":  {"cols": {
        "A:A": 14, "B:B": 5, "C:C": 2.5, "D:D": 4.5, "E:E":5.5, "F:G":4.5, "H:H":5.5,
        }, "rotated_header": False},
    
    "school_stats": {"cols": {
        "A:A": 13.5, "B:C": 4.25, "D:U": 4,
        }, "rotated_header": False},
    
    "depth_chart":  {"cols": {
        "A:A": 13, "B:K": 5,
        }, "rotated_header": False},
    
    "h2h_winpct":   {"cols": {
        "A:A": 10.5, "B:IA": 3.5,
        },  "rotated_header": True},
    
    "h2h_counts":   {"cols": {
        "A:A": 10.5, "B:IA": 1.75,
        }, "rotated_header": True},
    
    "h2h_master":   {"cols": {
        "A:ZA": 10.5,
        },  "rotated_header": True},
    
    "elo":          {"cols": {
        'A:A':2.5, 'B:B':14, 'C:C':4.5, 'D:M':4, 'N:N':7.5, 'O:O':4,
        }, "rotated_header": False},
    
    "elo_pred":     {"cols": {
        "A:A": 10.5, "B:JZ":3,
        }, "rotated_header": True},
    
}

def write_sheet(writer, df, sheet_name, layout, **to_excel_kwargs):
    spec = LAYOUTS[layout]
    df.to_excel(writer, sheet_name=sheet_name, **to_excel_kwargs)
    ws = writer.sheets[sheet_name]
    fmt = writer.book.add_format(BASE)
    for cols, width in spec["cols"].items():
        ws.set_column(cols, width=width, cell_format=fmt)
    if spec["rotated_header"]:
        ws.set_row(0, None, writer.book.add_format(ROTATED_HEADER))
    else:
        ws.set_row(0, None, writer.book.add_format(HEADER))
    ws.set_default_row(10.5)

import base64
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import eel
import pandas as pd

# DO NOT RE-INVENT: Using your already implemented generator example
from typst_generator import generate_pdfs


def get_workspace_dir() -> Path:
    """Returns the main workspace directory for the generator."""
    path = Path.home() / "Documents" / "GeneratorZaswiadczen"
    path.mkdir(parents=True, exist_ok=True)
    return path


@eel.expose
def load_library():
    """Reads all trainings from the workspace."""
    workspace = get_workspace_dir()
    entries = []
    
    if workspace.exists():
        for entry in workspace.iterdir():
            if entry.is_dir():
                json_path = entry / "data.json"
                if json_path.exists():
                    try:
                        data = json.loads(json_path.read_text(encoding="utf-8"))
                        id_str = entry.name
                        created_at = int(id_str.split('_')[0]) if '_' in id_str else 0
                        
                        entries.append({
                            "id": id_str,
                            "name": data.get("training", {}).get("nazwa_szkolenia", "Szkolenie"),
                            "date": data.get("training", {}).get("data_szkolenia", ""),
                            "created_at": created_at
                        })
                    except Exception:
                        pass
                        
    entries.sort(key=lambda x: x["created_at"], reverse=True)
    return entries


@eel.expose
def create_training(participants):
    """Creates a new folder and instantiates default training data."""
    timestamp = int(time.time())
    id_str = f"{timestamp}_nowe_szkolenie"
    folder_path = get_workspace_dir() / id_str
    folder_path.mkdir(parents=True, exist_ok=True)

    default_training = {
        "nazwa_szkolenia": "Nowe Szkolenie",
        "numer_szkolenia": "NR/202X",
        "data_szkolenia": "",
        "miejsce_szkolenia": "",
        "prowadzacy": "",
        "tematyka": "1. Wprowadzenie",
        "czas_trwania": "8 godz",
        "czas_trwania_od_do": "09:00 - 16:00",
        "data_wystawienia": ""
    }

    data = {
        "training": default_training,
        "participants": participants,
        "last_gen_training": None,
        "last_gen_participants": None
    }

    (folder_path / "data.json").write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    return id_str


@eel.expose
def load_training(id_str: str):
    """Loads a training snapshot from disk."""
    base_path = get_workspace_dir() / id_str
    json_path = base_path / "data.json"
    
    data = json.loads(json_path.read_text(encoding="utf-8"))
    
    gen_path = base_path / "data_gen.json"
    if gen_path.exists():
        try:
            gen_data = json.loads(gen_path.read_text(encoding="utf-8"))
            data["last_gen_training"] = gen_data.get("training")
            data["last_gen_participants"] = gen_data.get("participants")
        except Exception:
            pass
            
    return data


@eel.expose
def save_training(id_str: str, training: dict, participants: list):
    """Saves the form and participants to the active json file."""
    folder_path = get_workspace_dir() / id_str
    if not folder_path.exists():
        raise Exception("Folder szkolenia już nie istnieje!")
        
    data = {
        "training": training,
        "participants": participants,
        "last_gen_training": None,
        "last_gen_participants": None
    }
    
    json_path = folder_path / "data.json"
    json_path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


@eel.expose
def generate_pdfs_api(id_str: str):
    """Executes the pre-existing Typst generator module."""
    folder_path = get_workspace_dir() / id_str
    if not folder_path.exists():
        raise Exception("Folder szkolenia nie istnieje.")
    
    try:
        # Utilize the already implemented library call
        project_dir = folder_path.resolve()
        generate_pdfs(project_dir)
        
        # Save snapshot for diff tracking exactly like in Rust
        source_json = folder_path / "data.json"
        gen_snapshot = folder_path / "data_gen.json"
        gen_snapshot.write_text(source_json.read_text(encoding="utf-8"), encoding="utf-8")
        
        return "PDF wygenerowane pomyślnie!"
    except Exception as e:
        raise Exception(f"Błąd Typst: {str(e)}")


@eel.expose
def open_native_path(id_str: str, subpath: str = None):
    """Opens a native explorer window or PDF file."""
    path = get_workspace_dir() / id_str
    if subpath:
        path = path / subpath
        
    if not path.exists():
        raise Exception("Ten plik jeszcze nie istnieje. Wygeneruj PDF.")
        
    path_str = str(path)
    if sys.platform == "win32":
        os.startfile(path_str)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path_str])
    else:
        subprocess.Popen(["xdg-open", path_str])


# --- DATA PARSING HELPERS ---

def fix_date(raw_val: str) -> str:
    cleaned = re.sub(r'[-\,\_\/\\\.]', ' ', str(raw_val)).strip()
    parts = cleaned.split()
    if len(parts) < 3:
        return str(raw_val)
        
    try: day = int(parts[0])
    except ValueError: day = 1
        
    month_raw = parts[1].lower()
    months = {
        "styczeń": 1, "stycznia": 1, "styczen": 1, "01": 1, "1": 1,
        "luty": 2, "lutego": 2, "02": 2, "2": 2,
        "marzec": 3, "marca": 3, "03": 3, "3": 3,
        "kwiecień": 4, "kwietnia": 4, "kwiecien": 4, "04": 4, "4": 4,
        "maj": 5, "maja": 5, "05": 5, "5": 5,
        "czerwiec": 6, "czerwca": 6, "06": 6, "6": 6,
        "lipiec": 7, "lipca": 7, "07": 7, "7": 7,
        "sierpień": 8, "sierpnia": 8, "sierpien": 8, "08": 8, "8": 8,
        "wrzesień": 9, "września": 9, "wrzesien": 9, "09": 9, "9": 9,
        "październik": 10, "października": 10, "pazdziernik": 10, "10": 10,
        "listopad": 11, "listopada": 11, "11": 11,
        "grudzień": 12, "grudnia": 12, "grudzien": 12, "12": 12,
    }
    
    month = months.get(month_raw)
    if not month:
        try: month = int(month_raw)
        except ValueError: month = 1
        
    year_raw = parts[2]
    if len(year_raw) == 2:
        year = f"19{year_raw}" if int(year_raw) > 30 else f"20{year_raw}"
    else:
        year = year_raw
        
    return f"{day:02d}.{month:02d}.{year}"

def fix_location(raw: str) -> str:
    if not raw or str(raw).lower() == "nan":
        return "Nieznane"
    result = []
    capitalize_next = True
    for c in str(raw):
        if c.isalpha():
            result.append(c.upper() if capitalize_next else c.lower())
            capitalize_next = False
        else:
            result.append(c)
            capitalize_next = True
    return "".join(result)

def get_polish_weight(c: str) -> int:
    weights = {'a': 10, 'ą': 20, 'b': 30, 'c': 40, 'ć': 50, 'd': 60, 'e': 70, 'ę': 80, 'f': 90, 'g': 100, 'h': 110, 'i': 120, 'j': 130, 'k': 140, 'l': 150, 'ł': 160, 'm': 170, 'n': 180, 'ń': 190, 'o': 200, 'ó': 210, 'p': 220, 'r': 230, 's': 240, 'ś': 250, 't': 260, 'u': 270, 'w': 280, 'y': 290, 'z': 300, 'ź': 310, 'ż': 320}
    return weights.get(c.lower(), 1000 + ord(c))


@eel.expose
def parse_spreadsheet(b64_str: str) -> list:
    """Takes base64 file buffer from frontend, parses and formats participants."""
    file_bytes = base64.b64decode(b64_str)
    
    try:
        # Requires: pip install pandas python-calamine
        df = pd.read_excel(io.BytesIO(file_bytes), engine="calamine", header=None, skiprows=1)
    except Exception as e:
        raise Exception(f"Wystąpił problem podczas odczytu pliku: {str(e)}")
        
    raw_participants = []
    
    for _, row in df.iterrows():
        # Match columns: B (name)=1, C (date)=2, D (place)=3, F (email)=5
        if pd.isna(row.iloc[1]) or str(row.iloc[1]).strip() == "":
            continue
            
        name = str(row.iloc[1]).strip()
        birth_date_raw = str(row.iloc[2]).strip() if len(row) > 2 and not pd.isna(row.iloc[2]) else ""
        birth_place_raw = str(row.iloc[3]).strip() if len(row) > 3 and not pd.isna(row.iloc[3]) else "Nieznane"
        email = str(row.iloc[5]).strip() if len(row) > 5 and not pd.isna(row.iloc[5]) else None
        
        sorting_name = name.split()[-1].lower() if name else ""
        
        raw_participants.append({
            "participant": {
                "imie_nazwisko": name,
                "data_urodzenia": fix_date(birth_date_raw),
                "miejsce_urodzenia": fix_location(birth_place_raw),
                "locked": False
            },
            "sorting_name": sorting_name,
            "email": email
        })

    # Sort matching the Rust custom locale strategy
    raw_participants.sort(key=lambda x: [get_polish_weight(c) for c in x["sorting_name"]])

    # Deduplicate keeping entries with email records where available
    final_list = []
    i = 0
    while i < len(raw_participants):
        curr = raw_participants[i]
        best_idx = i
        j = i + 1
        
        while j < len(raw_participants):
            nxt = raw_participants[j]
            if curr["sorting_name"] == nxt["sorting_name"] and curr["participant"]["data_urodzenia"] == nxt["participant"]["data_urodzenia"]:
                if raw_participants[best_idx]["email"] is None and nxt["email"] is not None:
                    best_idx = j
                j += 1
            else:
                break
                
        final_list.append(raw_participants[best_idx]["participant"])
        i = j
        
    return final_list


if __name__ == "__main__":
    # Eel expects web assets in a specific folder. 
    # Store your index.html inside a directory named `web`.
    eel.init("web")
    eel.start("index.html", size=(1280, 800), mode="chrome")

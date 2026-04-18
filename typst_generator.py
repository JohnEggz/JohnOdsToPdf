import json
import logging
import sys
from pathlib import Path
from typing import Final, Union, Any, Dict, List, Tuple

import typst

# Module-level logger - does not configure logging, only provides a handle
logger = logging.getLogger(__name__)

# Constants for file names
TEMPLATE_CERTIFICATE: Final[str] = "certyfikat.typ"
TEMPLATE_ATTENDANCE: Final[str] = "lista_obecnosci.typ"
DATA_FILE: Final[str] = "data.json"

class TypstGeneratorError(Exception):
    """Custom exception for generator-specific errors."""
    pass

def get_bundle_dir() -> Path:
    """
    Returns the absolute path to the bundled assets directory.
    Priority 1: PyInstaller temporary folder (_MEIPASS).
    Priority 2: The 'assets' folder relative to this script's location.
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS).resolve() / "assets"
    
    # Resolve relative to this file's location to handle deep imports
    return Path(__file__).parent.resolve() / "assets"

def _load_json_data(path: Path) -> Dict[str, Any]:
    """Internal helper to load and validate JSON data."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise TypstGeneratorError(f"Failed to read or parse data file at {path}: {e}")

def generate_pdfs(working_dir: Union[str, Path]) -> None:
    """
    Core function to generate PDF documents.
    Designed to be called from external scripts (always imported).
    
    Args:
        working_dir: The directory on the disk where data.json is located 
                    and where the output PDFs should be saved.
    """
    # 1. Path Resolution & Validation
    work_path: Path = Path(working_dir).resolve()
    data_path: Path = work_path / DATA_FILE
    assets_path: Path = get_bundle_dir()
    
    if not work_path.is_dir():
        raise TypstGeneratorError(f"Working directory does not exist: {work_path}")
    
    if not data_path.is_file():
        raise TypstGeneratorError(f"Required data file missing at: {data_path}")

    # 2. Template Mapping
    # (Template Source, Output Target)
    tasks: List[Tuple[Path, Path]] = [
        (assets_path / TEMPLATE_CERTIFICATE, work_path / "certyfikaty.pdf"),
        (assets_path / TEMPLATE_ATTENDANCE, work_path / "lista_obecnosci.pdf"),
    ]

    # Verify templates exist in the bundle
    for template_path, _ in tasks:
        if not template_path.is_file():
            raise TypstGeneratorError(f"Internal asset missing: {template_path}")

    # 3. Data Serialization
    # Complex Python objects must be stringified for the typst-py sys_inputs bridge
    raw_data: Dict[str, Any] = _load_json_data(data_path)
    typst_inputs: Dict[str, str] = {
        "training": json.dumps(raw_data.get("training", {})),
        "participants": json.dumps(raw_data.get("participants", []))
    }

    # 4. Compilation Loop
    for template_path, output_path in tasks:
        logger.info("Compiling template: %s", template_path.name)
        
        try:
            typst.compile(
                str(template_path),
                output=str(output_path),
                root=str(assets_path),
                sys_inputs=typst_inputs
            )
            logger.info("Successfully saved: %s", output_path.name)
            
        except Exception as e:
            msg = str(e)
            # Detect common Typst script errors for better debugging
            if "file not found" in msg.lower() and "{" in msg:
                logger.error("Typst error: Missing 'json.decode()' in .typ file or invalid sys_inputs usage.")
            
            raise TypstGeneratorError(f"Compilation failed for {template_path.name}: {msg}") from e

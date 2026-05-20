import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Sett opp en dedikert fil for tankeprosess-logger
TRACE_FILE = Path(__file__).resolve().parent.parent.parent.parent.parent / "ki_kollega_trace.log"

class TraceLogger:
    """
    Sørger for visuelle spor i terminalen og fil for agent-prosesseringen.
    Gjør det lettere å se 'tankeprosessen' til KI Kollega.
    """
    
    # ANSI Farger
    COLORS = {
        "supervisor": "\033[1;34m",  # Blått
        "researcher": "\033[1;32m",  # Grønt
        "analyst": "\033[1;33m",     # Gult
        "reflector": "\033[1;35m",   # Magenta
        "compressor": "\033[1;36m",  # Cyan
        "writer": "\033[1;31m",      # Rødt
        "guardian": "\033[1;30m",    # Grått
        "reset": "\033[0m"
    }

    @classmethod
    def _write_to_file(cls, node_name: str, message: str, is_route: bool = False):
        """Skriver sporet til ki_kollega_trace.log uten fargekoder."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = "  ↳ ROUTE  |" if is_route else f"▶ {node_name.upper():<10} |"
            with open(TRACE_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {prefix} {message}\n")
        except Exception:
            pass

    @classmethod
    def log_node(cls, node_name: str, message: str, data: any = None):
        """Logger en hendelse fra en spesifikk node."""
        color = cls.COLORS.get(node_name.lower(), cls.COLORS["reset"])
        reset = cls.COLORS["reset"]
        
        # Forkort lange meldinger
        display_msg = str(message)
        if len(display_msg) > 120:
            display_msg = display_msg[:117] + "..."
            
        print(f"\n{color}▶ {node_name.upper():<10}{reset} | {display_msg}")
        
        # Skriv til fil for de som ikke ser terminalen
        cls._write_to_file(node_name, display_msg)
        
        if data:
            # Hvis vi har data og kanskje er i debug modus
            if os.getenv("DEBUG_AGENTS") == "true":
                import json
                try:
                    pretty_data = json.dumps(data, indent=2, ensure_ascii=False)
                    print(f"{color}      DATA:{reset} {pretty_data[:500]}")
                    with open(TRACE_FILE, "a", encoding="utf-8") as f:
                        f.write(f"      DATA: {pretty_data[:300]}...\n")
                except:
                    pass

        # Logg også til vanlig logger
        logger.info(f"AGENT_TRACE [{node_name}]: {message}")

    @classmethod
    def log_decision(cls, from_node: str, to_node: str, reasoning: str = ""):
        """Logger en ruting-beslutning."""
        reset = cls.COLORS["reset"]
        blue = cls.COLORS["supervisor"]
        
        reason_str = f" ({reasoning})" if reasoning else ""
        print(f"{blue}  ↳ ROUTE{reset}  | {from_node} -> {to_node}{reason_str}")
        
        # Skriv til fil
        cls._write_to_file("supervisor", f"{from_node} -> {to_node}{reason_str}", is_route=True)

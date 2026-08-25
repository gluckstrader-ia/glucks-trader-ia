from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path
import json
import uuid


# =====================================================
# AI MEMORY LAYER V1
# =====================================================

MEMORY_PATH = Path(
    "app/data/ai_memory.json"
)


# =====================================================
# INITIALIZATION
# =====================================================

def ensure_memory_storage():

    MEMORY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not MEMORY_PATH.exists():

        MEMORY_PATH.write_text(
            "[]",
            encoding="utf-8",
        )


# =====================================================
# LOAD / SAVE
# =====================================================

def load_memory() -> List[Dict[str, Any]]:

    ensure_memory_storage()

    try:

        content = MEMORY_PATH.read_text(
            encoding="utf-8"
        )

        return json.loads(content)

    except Exception:

        return []



def save_memory(data: List[Dict[str, Any]]):

    ensure_memory_storage()

    MEMORY_PATH.write_text(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )



# =====================================================
# CREATE SIGNAL MEMORY
# =====================================================

def create_signal_memory(
    analysis: Dict[str, Any],
):

    ai_brain = analysis.get(
        "ai_brain",
        {},
    )


    final_signal = analysis.get(
        "final_signal",
        {},
    )


    memory = {

        "id":
            str(uuid.uuid4()),


        "timestamp":
            datetime.now().isoformat(),


        "asset":
            analysis.get(
                "asset",
                "",
            ),


        "timeframe":
            analysis.get(
                "timeframe",
                "",
            ),


        "direction":
            final_signal.get(
                "direction",
                "NEUTRO",
            ),


        "signal_confidence":
            ai_brain.get(
                "signal_confidence",
                "",
            ),


        "trade_quality_score":
            ai_brain.get(
                "trade_quality_score",
                0,
            ),


        "trade_quality_label":
            ai_brain.get(
                "trade_quality_label",
                "",
            ),


        "module_alignment":
            ai_brain.get(
                "module_alignment",
                "",
            ),


        "decision_state":
            ai_brain.get(
                "decision_state",
                "",
            ),


        "decision_color":
            ai_brain.get(
                "decision_color",
                "",
            ),


        "entry":
            final_signal.get(
                "entry",
            ),


        "stop":
            final_signal.get(
                "stop",
            ),


        "target":
            final_signal.get(
                "target",
            ),


        "result":
            None,


        "closed":
            False,

    }


    return memory



# =====================================================
# STORE MEMORY
# =====================================================

def store_signal_memory(
    analysis: Dict[str, Any],
):

    memories = load_memory()

    memory = create_signal_memory(
        analysis
    )

    memories.append(
        memory
    )

    save_memory(
        memories
    )

    return memory



# =====================================================
# HISTORY
# =====================================================

def get_signal_history(
    limit: int = 100,
):

    memories = load_memory()

    return memories[-limit:]



# =====================================================
# UPDATE RESULT
# =====================================================

def update_signal_result(
    memory_id: str,
    result: str,
    profit_points: float = 0,
):

    memories = load_memory()


    for item in memories:

        if item.get("id") == memory_id:

            item["result"] = result

            item["profit_points"] = profit_points

            item["closed"] = True

            break


    save_memory(
        memories
    )


# =====================================================
# SIMILAR PATTERNS V1
# =====================================================

def find_similar_patterns(
    direction: str,
    module_alignment: str,
    limit: int = 50,
):

    memories = load_memory()


    matches = []


    for item in reversed(memories):

        if (
            item.get("direction") == direction
            and
            item.get("module_alignment")
            == module_alignment
        ):

            matches.append(
                item
            )


        if len(matches) >= limit:

            break


    return matches
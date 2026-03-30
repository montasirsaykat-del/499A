# ─────────────────────────────────────────────
#  config.py  –  Central configuration for math_eval
# ─────────────────────────────────────────────

import os

# ── Data ──────────────────────────────────────
DATA_FOLDER = os.path.join(os.getcwd(), "data")  # ← change to your local data path
MAX_SAMPLES_PER_CATEGORY = 150            # cap per dataset to balance total

# ── Model ─────────────────────────────────────
MODEL_NAME      = "Qwen/Qwen2.5-Math-7B-Instruct"
USE_4BIT_QUANT  = True     # BitsAndBytes 4-bit (RTX 3060 12 GB)
DEVICE          = "cuda"   # "cpu" for CPU-only fallback

# ── Reasoning ─────────────────────────────────
COT_MAX_NEW_TOKENS = 512
TOT_MAX_NEW_TOKENS = 1024
TOT_NUM_BRANCHES   = 3

# ── Resume / Checkpoint ───────────────────────
CHECKPOINT_FILE  = os.path.join("results", "checkpoint.json")
AUTOSAVE_EVERY   = 50     # generate partial reports every N samples
RESUME_ENABLED   = True   # False → delete checkpoint and start fresh

# ── Output formats ────────────────────────────
SAVE_CSV  = True
SAVE_HTML = True
SAVE_PDF  = True

# ── Results folder ────────────────────────────
RESULTS_DIR = "results"

# ── Dataset → Category mapping ────────────────
DATASET_CATEGORY_MAP = {
    "aqua_rat":                          "Algebra",
    "gsm8k_test (1)":                    "Arithmetic",
    "gsm8k_test":                        "Arithmetic",
    "logiqa_test":                       "Logic",
    "math_algebra":                      "Algebra",
    "math_counting_and_probability":     "Counting_Probability",
    "math_geometry":                     "Geometry",
    "math_intermediate_algebra":         "Algebra",
    "math_number_theory":                "Number_Theory",
    "math_prealgebra":                   "Algebra",
    "math_precalculus":                  "PreCalculus",
    "math_test (1)":                     "Competition",
    "math_test":                         "Competition",
    "mgsm_bn":                           "Word_Problem",
    "mgsm_de":                           "Word_Problem",
    "mgsm_es":                           "Word_Problem",
    "mgsm_en":                           "Arithmetic",
    "scibench_physics":                  "Physics",
}

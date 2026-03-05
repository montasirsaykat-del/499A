# math_eval — CoT vs ToT Mathematical Reasoning Evaluator

Evaluate Chain-of-Thought (CoT) vs Tree-of-Thought (ToT) reasoning on
mathematical datasets using any HuggingFace causal-LM.

---

## Quick start

### 1 · Install dependencies

```bash
cd math_eval
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

> **GPU note** — `bitsandbytes` requires a CUDA-capable GPU (tested on RTX 3060 12 GB).
> On CPU-only machines set `USE_4BIT_QUANT = False` in `config.py`.

---

### 2 · Configure

Open **`config.py`** and set:

```python
DATA_FOLDER = r"C:\Users\YourName\data"   # ← override with your data directory
MODEL_NAME  = "Qwen/Qwen2.5-Math-7B-Instruct"
```

> **Default**: `DATA_FOLDER` defaults to `./data` (a `data/` subfolder inside the
> current working directory). You only need to change it if your files are elsewhere.

Other useful settings:

| Setting | Default | Description |
|---|---|---|
| `MAX_SAMPLES_PER_CATEGORY` | 150 | Cap per dataset |
| `AUTOSAVE_EVERY` | 50 | Partial report every N samples |
| `RESUME_ENABLED` | True | Auto-resume from checkpoint |
| `USE_4BIT_QUANT` | True | BitsAndBytes 4-bit quantisation |
| `SAVE_CSV` / `SAVE_HTML` / `SAVE_PDF` | True | Toggle output formats |

---

### 3 · Dataset folder structure

Place your dataset files (`.xlsx` or `.csv`) inside `DATA_FOLDER`:

```
data/
├── gsm8k_test (1).xlsx
├── math_algebra.xlsx
├── math_geometry.xlsx
├── math_counting_and_probability.xlsx
├── math_intermediate_algebra.xlsx
├── math_number_theory.xlsx
├── math_prealgebra.xlsx
├── math_precalculus.xlsx
├── math_test (1).xlsx
├── mgsm_bn.xlsx
├── mgsm_de.xlsx
├── mgsm_en.xlsx
├── mgsm_es.xlsx
├── logiqa_test.xlsx
├── scibench_physics.xlsx
└── aqua_rat.xlsx
```

Dataset → Category mapping (defined in `config.py`):

| File stem | Category |
|---|---|
| `aqua_rat` | Algebra |
| `gsm8k_test (1)` | Arithmetic |
| `logiqa_test` | Logic |
| `math_algebra` | Algebra |
| `math_counting_and_probability` | Counting_Probability |
| `math_geometry` | Geometry |
| `math_intermediate_algebra` | Algebra |
| `math_number_theory` | Number_Theory |
| `math_prealgebra` | Algebra |
| `math_precalculus` | PreCalculus |
| `math_test (1)` | Competition |
| `mgsm_bn` / `mgsm_de` / `mgsm_es` | Word_Problem |
| `mgsm_en` | Arithmetic |
| `scibench_physics` | Physics |

---

### 4 · Run

```bash
python evaluate.py
```

Sample output:
```
🆕 No checkpoint found – starting from scratch.
🔄 Loading model: Qwen/Qwen2.5-Math-7B-Instruct …
✅ Model loaded

📂 gsm8k_test (1)  →  category: Arithmetic  |  total: 150  |  done: 0  |  remaining: 150
Arithmetic: 100%|██████████| 150/150 [12:34<00:00]
  💾 Auto-saved at 50 samples (elapsed: 0:04:10)
  💾 Auto-saved at 100 samples (elapsed: 0:08:21)
  💾 Auto-saved at 150 samples (elapsed: 0:12:34)
...
🎉 Evaluation complete!
   Total samples evaluated: 1500
   Elapsed time: 2:05:44
✅ Summary CSV saved → results/evaluation_report.csv
✅ HTML report saved → results/evaluation_report.html
✅ PDF report saved → results/evaluation_report.pdf
```

---

### 5 · Interrupt and resume

#### If interrupted (Ctrl-C):

```
^C
⚠️  INTERRUPTED! Saving progress…
✅ Partial CSV saved → results/evaluation_report.csv
✅ Partial HTML saved → results/evaluation_report.html
✅ Progress saved! Run again to resume from where you stopped.
```

#### Resume next day:

```bash
python evaluate.py
```

Output:
```
📂 Resuming from checkpoint: 847 samples already done
   Per category: {'Arithmetic': 150, 'Algebra': 200, 'Geometry': 45, …}
```

#### Force a fresh start:

```bash
python evaluate.py --fresh
```

Or set `RESUME_ENABLED = False` in `config.py`.

---

### 6 · Output files

After a complete (or interrupted) run you will find:

```
results/
├── checkpoint.json          ← auto-saved after every sample
├── evaluation_report.csv    ← summary CSV (one row per category)
├── detailed_results.csv     ← per-sample CSV
├── evaluation_report.html   ← self-contained HTML report with embedded graphs
├── evaluation_report.pdf    ← PDF report with graphs
└── evaluation_graphs.png    ← 4-chart matplotlib figure (generated separately)
```

`evaluation_report.csv` format:
```
Category,Questions,CoT_Acc_Pct,ToT_Acc_Pct,Best_Method,Difference_Pct
Arithmetic,150,55.3,51.8,CoT,3.5
Algebra,300,62.1,59.4,CoT,2.7
...
```

---

### 7 · Model information

| Setting | Value |
|---|---|
| Default model | `Qwen/Qwen2.5-Math-7B-Instruct` |
| Quantisation | 4-bit NF4 via BitsAndBytes |
| GPU requirement | ≥ 12 GB VRAM (RTX 3060 or better) |
| Expected GSM8K accuracy | ~85% (CoT) |

---

### 8 · Project structure

```
math_eval/
├── config.py              ← all configuration knobs
├── checkpoint_manager.py  ← atomic checkpoint save / load / resume
├── report_generator.py    ← CSV / HTML / PDF report generation
├── evaluate.py            ← main evaluation script
├── requirements.txt       ← Python dependencies
├── README.md              ← this file
└── results/               ← output directory (created automatically)
```

# CopyNE demo: how to re-run

Reproduces the evaluation of CopyNE (Zhou et al., ACL 2024) with the released checkpoint on AISHELL-1.
Upstream code: <https://github.com/zsLin177/CopyNE>, pinned at commit `e6c0c574421f4b251e7693d9fc3bf4749e29aeeb`.

**Status (2 Nov 2026): prepared, not yet executed on a GPU.** See "What has been checked" below.

## Quick start (Colab, T4)

1. Copy this folder to Google Drive (`MyDrive/final_project/code/copyne`).
2. Open `01_copyne_setup_baseline.ipynb` in Colab with a GPU runtime and run the cells in order.
3. Results go to `RESULTS_DIR` on Drive (`summary.csv`, per-mode `.asr` outputs, `.cer`/`.ne-cer` alignments, `env.txt`).

## Command line

```bash
bash setup_env.sh                                   # clone at pinned commit + Python 3.10 venv (work/)
python prepare_data.py --repo work/CopyNE           # AISHELL-1 test audio, manifests, gold .text
# download the released checkpoint folder (Google Drive link in the upstream README) to ./ckpt
python run_demo.py --repo work/CopyNE --venv work/venv310 --model-dir ckpt --limit 50 --out results/smoke
python run_demo.py --repo work/CopyNE --venv work/venv310 --model-dir ckpt --manifest test-ne --out results/test-ne
```

A CUDA GPU is required: upstream `main.py` always initializes NCCL and DDP, even for one GPU.

## What the scripts do

| File | Purpose |
|---|---|
| `requirements-eval.txt` | Pinned packages for Python 3.10 (differences from upstream below) |
| `setup_env.sh` | Clone at a fixed commit, build a Python 3.10 venv with `uv`, install the pins |
| `prepare_data.py` | Download only the 20 test speakers, extract, rewrite manifest paths, write `*.text` gold files, check every wav exists |
| `run_demo.py` | Run `evaluate` in three decoding modes, compute CER and NE-CER, write `summary.csv` and `env.txt` |
| `01_copyne_setup_baseline.ipynb` | The same steps for Colab, plus a qualitative-example cell |

Decoding modes (same model, same dictionary `test_ne.vocab`, beam 10, copy threshold 0.9):

| Mode | Meaning |
|---|---|
| `ctc_greedy_search` | Acoustic-only CTC decoding; the dictionary is not used |
| `attention` | Attention decoding with the context encoder, token by token |
| `copy_attention` | Full CopyNE: copy a whole entity from the dictionary |

Which row is "without biasing" in the report table is still to be agreed by the team. Our own numbers are
`\ours{}`; numbers quoted from the paper are `\authorrep{}`.

Evaluation sets (from the upstream manifests): `test-ne` has 2244 utterances and 3082 entities, `test_addne` the
full test set of 7176 utterances. Both use the 20 AISHELL-1 test speakers (S0764 to S0916).

## Problems found in the upstream repo (and what we did)

1. `requirements.txt` cannot be installed: `torch==2.0.1` and `torchaudio==2.0.0` conflict (torchaudio 2.0.0 needs torch 2.0.0).
   We use `torchaudio==2.0.2`.
2. `main.py` imports `gradio` at the top, but it is not in `requirements.txt`. We pin `gradio==3.50.2` (our choice).
3. The README data step stops after `tar -zxvf data_aishell.tgz`. The audio is inside per-speaker tarballs
   (`wav/S0002.tar.gz`, ...) that must be extracted too; `prepare_data.py` does this.
4. The README evaluate example uses `conf/copyne.yaml` and `char.vocab`, but the released checkpoint is for
   `conf/copyne-conformer.yaml` and the web-demo command uses `multi_char.vocab`. `run_demo.py` uses the conformer
   config and picks the vocabulary by matching the checkpoint's output size.
5. The gold `test-ne.text` that `compute-necer.sh` needs is not in the repo (`*.text` is git-ignored upstream);
   `prepare_data.py` generates it from the manifest.
6. No LICENSE file in the repo. Code is only used here for evaluation.
7. Python 3.12+ breaks upstream (`imp` was removed) and torch 2.0.1 has no wheels for it, hence the Python 3.10 venv.

## What has been checked

| Item | State |
|---|---|
| Pinned requirements resolve together on Python 3.10 | Checked with `uv pip install --dry-run` (not installed) |
| Manifest statistics, speaker list, path rewriting, gold `.text`, missing-wav check | Run on dummy wav files |
| `compute-necer.sh` and the result parser | Run on dummy predictions (known error counts matched) |
| Download of audio (Hugging Face / OpenSLR) | **Not tested**: hosts were not reachable from the preparation environment |
| Checkpoint download and contents (file names, which vocabulary it needs) | **Not tested**: Google Drive was not reachable |
| `torchrun main.py evaluate` on a GPU, and the numbers | **Not run** |
| License of the released checkpoint | Unknown |

## Notes for the ablation (TV3 + TV4)

- The dictionary is a JSON `{entity: id}` file passed with `--test_ne_dict`; `test_ne.vocab` holds the
  entities of the test set. Dictionary-size ablations can build smaller or larger files with the same format
  (entities from `train_ne.vocab` or `dev_ne.vocab` serve as distractors).
- Evaluation uses beam search and is deterministic; `--seed` has no effect on it.
- Colab sessions end: keep results on Drive after every run.

#!/usr/bin/env python3
"""Evaluate the released CopyNE checkpoint and compute CER / NE-CER.

Three decoding modes of the same model are run on the same manifest and dictionary:
  ctc_greedy_search  acoustic-only CTC decoding; the NE dictionary is not used        (no biasing)
  attention          attention decoding with the context encoder, token by token     (CLAS-style biasing)
  copy_attention     CopyNE: copy a whole entity from the dictionary                  (full method)
Which of these is "without biasing" in the report table is a team decision; all three are recorded.

    python run_demo.py --repo work/CopyNE --venv work/venv310 --model-dir /path/to/ckpt --limit 50 --out results/smoke
    python run_demo.py --repo work/CopyNE --venv work/venv310 --model-dir /path/to/ckpt --out results/test-ne
"""
import argparse, csv, json, os, re, subprocess, sys
from pathlib import Path

ALL_MODES = ["ctc_greedy_search", "attention", "copy_attention"]
VOCABS = {"char.vocab": "data_to_upload/aishell_vocab/char.vocab", "multi_char.vocab": "data_to_upload/multi_char.vocab"}
OVERALL = re.compile(r"Overall -> ([\d.]+) % N=(\d+) C=(\d+) S=(\d+) D=(\d+) I=(\d+)")


def run(cmd, cwd, env=None, log=None):
    print("$", " ".join(map(str, cmd)), flush=True)
    f = open(log, "w") if log else None
    try:
        subprocess.run(list(map(str, cmd)), cwd=cwd, env=env, check=True, stdout=f, stderr=subprocess.STDOUT if f else None)
    finally:
        if f:
            f.close()


def checkpoint_file(model_dir):
    for name in ("avg.model", "best.model"):
        if (Path(model_dir) / name).exists():
            return name
    sys.exit(f"No avg.model or best.model in {model_dir}. Contents: {sorted(os.listdir(model_dir))}")


def detect_vocab(repo, venv, ckpt):
    """Pick the vocabulary whose size matches the checkpoint's output layer."""
    sizes = {n: sum(1 for _ in open(Path(repo) / p, encoding="utf8")) for n, p in VOCABS.items()}
    code = ("import torch,sys,json\n"
            "ck=torch.load(sys.argv[1],map_location='cpu')\n"
            "sd=ck.get('model_state_dict',ck)\n"
            "want=set(json.loads(sys.argv[2]).values())\n"
            "print(json.dumps(sorted({int(v.shape[0]) for v in sd.values() if hasattr(v,'shape') and len(v.shape)>=1 and int(v.shape[0]) in want})))\n")
    out = subprocess.run([str(Path(venv) / "bin/python"), "-c", code, str(ckpt), json.dumps(sizes)],
                         check=True, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    hit = json.loads(out)
    names = [n for n, s in sizes.items() if s in hit]
    if len(names) != 1:
        sys.exit(f"Cannot pick the vocabulary automatically (vocab sizes {sizes}, matches {hit}). Pass --char-dict.")
    print(f"vocabulary: {names[0]} (size {sizes[names[0]]})")
    return VOCABS[names[0]]


def parse_overall(path):
    last = None
    for line in open(path, encoding="utf8", errors="ignore"):
        m = OVERALL.search(line)
        if m:
            last = m
    if not last:
        return None
    return {"rate": float(last.group(1)), "N": int(last.group(2)), "C": int(last.group(3)),
            "S": int(last.group(4)), "D": int(last.group(5)), "I": int(last.group(6))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--venv", required=True)
    ap.add_argument("--model-dir", required=True, help="dir containing avg.model or best.model")
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default="test-ne", choices=["test-ne", "test_addne"])
    ap.add_argument("--ne-dict", default="data_to_upload/aishell_vocab/test_ne.vocab")
    ap.add_argument("--char-dict", default="auto")
    ap.add_argument("--config", default="conf/copyne-conformer.yaml")
    ap.add_argument("--modes", nargs="+", default=ALL_MODES, choices=ALL_MODES)
    ap.add_argument("--copy-threshold", type=float, default=0.9)
    ap.add_argument("--beam-size", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0, help="only the first N utterances (smoke test)")
    ap.add_argument("--port", type=int, default=29501)
    a = ap.parse_args()

    repo, venv, out = Path(a.repo).resolve(), Path(a.venv).resolve(), Path(a.out).resolve()
    model_dir = Path(a.model_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    ds = repo / "data_to_upload" / "aishell_dataset"
    name = a.manifest

    if a.limit:                                    # subset manifest + gold text, same directory
        name = f"{a.manifest}-first{a.limit}"
        rows = open(ds / f"{a.manifest}.json", encoding="utf8").read().splitlines()[: a.limit]
        (ds / f"{name}.json").write_text("\n".join(rows) + "\n", encoding="utf8")
        with open(ds / f"{name}.text", "w", encoding="utf8") as f:
            for r in rows:
                d = json.loads(r)
                f.write(f"{d['key']} {d['txt']}\n")
    gold = ds / f"{name}.text"
    if not gold.exists():
        sys.exit(f"{gold} not found - run prepare_data.py first")

    ckpt_name = checkpoint_file(model_dir)
    char_dict = detect_vocab(repo, venv, model_dir / ckpt_name) if a.char_dict == "auto" else a.char_dict

    env = dict(os.environ, PATH=f"{venv/'bin'}{os.pathsep}{os.environ['PATH']}")
    rows = []
    for mode in a.modes:
        tag = f"{name}.{mode}"
        cmd = [venv / "bin/torchrun", "--nnodes=1", "--nproc_per_node=1", f"--master_port={a.port}", "main.py", "evaluate",
               "--char_dict", char_dict, "--add_context", "--att_type", "simpleatt", "--add_copy_loss",
               "--config", a.config, "--input", ds / f"{name}.json", "--test_ne_dict", a.ne_dict,
               "--path", model_dir, "--res", out / tag, "--decode_mode", mode,
               "--copy_threshold", a.copy_threshold, "--batch_size", a.batch_size, "--beam_size", a.beam_size]
        if ckpt_name == "avg.model":
            cmd.append("--use_avg")
        run(cmd, repo, env, log=out / f"{tag}.stdout")
        pred = out / f"{tag}.asr"
        run(["bash", "compute-necer.sh", gold, pred], repo, env, log=out / f"{tag}.metrics.log")
        cer, ner = parse_overall(f"{pred}.cer"), parse_overall(f"{pred}.ne-cer")
        speed = re.search(r"elapsed, ([\d.]+) Sents/s", open(out / f"{tag}.stdout", errors="ignore").read())
        rows.append({"mode": mode, "CER": cer and cer["rate"], "NE-CER": ner and ner["rate"],
                     "chars": cer and cer["N"], "entity_chars": ner and ner["N"],
                     "sents_per_s": float(speed.group(1)) if speed else None})
        print(rows[-1], flush=True)

    with open(out / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    freeze = subprocess.run([str(venv / "bin/python"), "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    (out / "env.txt").write_text(f"copyne_commit {commit}\nargs {vars(a)}\ncheckpoint {ckpt_name}\nchar_dict {char_dict}\n\n{freeze}")
    print("\nmode                CER     NE-CER")
    for r in rows:
        print(f"{r['mode']:<18} {r['CER']}  {r['NE-CER']}")


if __name__ == "__main__":
    main()

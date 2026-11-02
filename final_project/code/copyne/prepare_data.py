#!/usr/bin/env python3
"""Prepare the AISHELL-1 *test* audio that CopyNE evaluates on.

The CopyNE repo ships the json manifests and vocabularies but not the audio. Evaluation only needs the
20 test speakers, so by default we fetch just their per-speaker tarballs instead of the 15 GB archive.

Steps: (1) find the speakers in the test manifests, (2) download + extract their audio,
(3) rewrite the `wav` paths in the manifests to absolute paths, (4) write the gold `.text` files that
compute-necer.sh needs (the upstream repo does not include them), (5) check that every wav exists.

    python prepare_data.py --repo work/CopyNE                 # Hugging Face per-speaker tarballs
    python prepare_data.py --repo work/CopyNE --source openslr  # fallback: full data_aishell.tgz (~15 GB)
"""
import argparse, importlib.util, json, re, subprocess, sys, tarfile
from pathlib import Path

MANIFESTS = ["test-ne.json", "test_addne.json"]   # entity-rich subset (2244 utts) and full test set (7176 utts)


def read_jsonl(p):
    with open(p, encoding="utf8") as f:
        return [json.loads(l) for l in f if l.strip()]


def speakers_of(manifests):
    spk = []
    for m in manifests:
        for d in read_jsonl(m):
            s = re.search(r"/(S\d{4})/", d["wav"]).group(1)
            if s not in spk:
                spk.append(s)
    return sorted(spk)


def extract(tar_path, dest, members=None):
    with tarfile.open(tar_path) as t:
        try:                                   # safe extraction filter (Python >= 3.12 / 3.11.4+)
            t.extractall(dest, members=members, filter="data")
        except TypeError:
            t.extractall(dest, members=members)


def fetch_hf(speakers, work):
    from huggingface_hub import hf_hub_download
    out = []
    for s in speakers:
        out.append(hf_hub_download("AISHELL/AISHELL-1", f"data_aishell/wav/{s}.tar.gz",
                                   repo_type="dataset", local_dir=work))
    return out


def fetch_openslr(speakers, work):
    import requests
    url = "https://us.openslr.org/resources/33/data_aishell.tgz"
    tgz = Path(work) / "data_aishell.tgz"
    if not tgz.exists():
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(tgz, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    members = [f"data_aishell/wav/{s}.tar.gz" for s in speakers]
    subprocess.run(["tar", "-xzf", str(tgz), "-C", str(work)] + members, check=True)
    return [Path(work) / m for m in members]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="path to the cloned CopyNE repo")
    ap.add_argument("--source", choices=["hf", "openslr"], default="hf")
    ap.add_argument("--download-dir", default=None, help="where tarballs are kept (default: <repo>/../audio_cache)")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    data = repo / "data_to_upload"
    ds = data / "aishell_dataset"
    cache = Path(a.download_dir or repo.parent / "audio_cache").resolve()
    cache.mkdir(parents=True, exist_ok=True)
    wav_dir = data / "data_aishell" / "wav"
    wav_dir.mkdir(parents=True, exist_ok=True)

    manifests = [ds / m for m in MANIFESTS]
    spk = speakers_of(manifests)
    print(f"{len(spk)} test speakers: {spk[0]} .. {spk[-1]}")

    if not all((wav_dir / "test" / s).is_dir() for s in spk):
        tars = fetch_hf(spk, cache) if a.source == "hf" else fetch_openslr(spk, cache)
        for t in tars:
            extract(t, wav_dir)     # each tarball unpacks to <split>/<speaker>/*.wav
    else:
        print("audio already extracted")

    # Reuse the upstream helper so the manifests end up exactly as the README expects.
    sp = importlib.util.spec_from_file_location("cwp", repo / "scripts" / "change_wav_path.py")
    cwp = importlib.util.module_from_spec(sp); sp.loader.exec_module(cwp)
    for m in manifests:
        cwp.change_wav_path(str(m), str(data))

    missing = 0
    for m in manifests:
        rows = read_jsonl(m)
        miss = [d["wav"] for d in rows if not Path(d["wav"]).exists()]
        missing += len(miss)
        with open(m.with_suffix(".text"), "w", encoding="utf8") as f:     # gold transcripts, "key text"
            for d in rows:
                f.write(f"{d['key']} {d['txt']}\n")
        print(f"{m.name}: {len(rows)} utterances, {len(miss)} missing wav, gold -> {m.with_suffix('.text').name}")
    if missing:
        sys.exit(f"ERROR: {missing} wav files not found. Check the extraction layout under {wav_dir}")
    print("OK")


if __name__ == "__main__":
    main()

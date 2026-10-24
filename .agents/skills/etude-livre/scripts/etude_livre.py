#!/usr/bin/env python3
"""Outil CLI pour l'étude exégétique et homilétique d'un livre entier de la Bible.

Sous-commandes :
  - collect : récupère les textes bibliques (NEG79, LSG, S21, Darby, NBS, grec/hébreu),
              l'interlinéaire morphologique, l'apparat SBLGNT, l'introduction MacArthur
              et les transcriptions de sermons Grace to You.
  - lexicon : récupère intégralement une entrée Thayer (grec) ou BDB (hébreu).
  - render  : génère Plan-Serie-<Livre>-1-<N>.pdf à partir de son fichier Markdown.
  - portal  : génère le portail autonome index.html à partir d'une spécification JSON.
  - verify  : exécute les contrôles de clôture sur un dossier <Livre>/ (4*N+7 fichiers,
              absence de tiret cadratin, résolution des liens et ancres, exactitude NEG79).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class RateLimitError(RuntimeError):
    """Erreur levée lorsque le serveur distant renvoie HTTP 429 (Too Many Requests)."""


BOOKS_TABLE: list[dict[str, Any]] = [
    {"num": 1, "name": "Genèse", "slug": "Genese", "usfm": "GEN", "bh": "genesis", "sbl": "", "mob": "gen", "chapters": 50},
    {"num": 2, "name": "Exode", "slug": "Exode", "usfm": "EXO", "bh": "exodus", "sbl": "", "mob": "exo", "chapters": 40},
    {"num": 3, "name": "Lévitique", "slug": "Levitique", "usfm": "LEV", "bh": "leviticus", "sbl": "", "mob": "lev", "chapters": 27},
    {"num": 4, "name": "Nombres", "slug": "Nombres", "usfm": "NUM", "bh": "numbers", "sbl": "", "mob": "num", "chapters": 36},
    {"num": 5, "name": "Deutéronome", "slug": "Deuteronome", "usfm": "DEU", "bh": "deuteronomy", "sbl": "", "mob": "deu", "chapters": 34},
    {"num": 6, "name": "Josué", "slug": "Josue", "usfm": "JOS", "bh": "joshua", "sbl": "", "mob": "jos", "chapters": 24},
    {"num": 7, "name": "Juges", "slug": "Juges", "usfm": "JDG", "bh": "judges", "sbl": "", "mob": "jdg", "chapters": 21},
    {"num": 8, "name": "Ruth", "slug": "Ruth", "usfm": "RUT", "bh": "ruth", "sbl": "", "mob": "rut", "chapters": 4},
    {"num": 9, "name": "1 Samuel", "slug": "1-Samuel", "usfm": "1SA", "bh": "1_samuel", "sbl": "", "mob": "1sa", "chapters": 31},
    {"num": 10, "name": "2 Samuel", "slug": "2-Samuel", "usfm": "2SA", "bh": "2_samuel", "sbl": "", "mob": "2sa", "chapters": 24},
    {"num": 11, "name": "1 Rois", "slug": "1-Rois", "usfm": "1KI", "bh": "1_kings", "sbl": "", "mob": "1ki", "chapters": 22},
    {"num": 12, "name": "2 Rois", "slug": "2-Rois", "usfm": "2KI", "bh": "2_kings", "sbl": "", "mob": "2ki", "chapters": 25},
    {"num": 13, "name": "1 Chroniques", "slug": "1-Chroniques", "usfm": "1CH", "bh": "1_chronicles", "sbl": "", "mob": "1ch", "chapters": 29},
    {"num": 14, "name": "2 Chroniques", "slug": "2-Chroniques", "usfm": "2CH", "bh": "2_chronicles", "sbl": "", "mob": "2ch", "chapters": 36},
    {"num": 15, "name": "Esdras", "slug": "Esdras", "usfm": "EZR", "bh": "ezra", "sbl": "", "mob": "ezr", "chapters": 10},
    {"num": 16, "name": "Néhémie", "slug": "Nehemie", "usfm": "NEH", "bh": "nehemiah", "sbl": "", "mob": "neh", "chapters": 13},
    {"num": 17, "name": "Esther", "slug": "Esther", "usfm": "EST", "bh": "esther", "sbl": "", "mob": "est", "chapters": 10},
    {"num": 18, "name": "Job", "slug": "Job", "usfm": "JOB", "bh": "job", "sbl": "", "mob": "job", "chapters": 42},
    {"num": 19, "name": "Psaumes", "slug": "Psaumes", "usfm": "PSA", "bh": "psalms", "sbl": "", "mob": "psa", "chapters": 150},
    {"num": 20, "name": "Proverbes", "slug": "Proverbes", "usfm": "PRO", "bh": "proverbs", "sbl": "", "mob": "pro", "chapters": 31},
    {"num": 21, "name": "Ecclésiaste", "slug": "Ecclesiaste", "usfm": "ECC", "bh": "ecclesiastes", "sbl": "", "mob": "ecc", "chapters": 12},
    {"num": 22, "name": "Cantique des Cantiques", "slug": "Cantique-des-Cantiques", "usfm": "SNG", "bh": "songs", "sbl": "", "mob": "sng", "chapters": 8},
    {"num": 23, "name": "Ésaïe", "slug": "Esaie", "usfm": "ISA", "bh": "isaiah", "sbl": "", "mob": "isa", "chapters": 66},
    {"num": 24, "name": "Jérémie", "slug": "Jeremie", "usfm": "JER", "bh": "jeremiah", "sbl": "", "mob": "jer", "chapters": 52},
    {"num": 25, "name": "Lamentations", "slug": "Lamentations", "usfm": "LAM", "bh": "lamentations", "sbl": "", "mob": "lam", "chapters": 5},
    {"num": 26, "name": "Ézéchiel", "slug": "Ezechiel", "usfm": "EZK", "bh": "ezekiel", "sbl": "", "mob": "eze", "chapters": 48},
    {"num": 27, "name": "Daniel", "slug": "Daniel", "usfm": "DAN", "bh": "daniel", "sbl": "", "mob": "dan", "chapters": 12},
    {"num": 28, "name": "Osée", "slug": "Osee", "usfm": "HOS", "bh": "hosea", "sbl": "", "mob": "hos", "chapters": 14},
    {"num": 29, "name": "Joël", "slug": "Joel", "usfm": "JOL", "bh": "joel", "sbl": "", "mob": "joe", "chapters": 3},
    {"num": 30, "name": "Amos", "slug": "Amos", "usfm": "AMO", "bh": "amos", "sbl": "", "mob": "amo", "chapters": 9},
    {"num": 31, "name": "Abdias", "slug": "Abdias", "usfm": "OBA", "bh": "obadiah", "sbl": "", "mob": "oba", "chapters": 1},
    {"num": 32, "name": "Jonas", "slug": "Jonas", "usfm": "JON", "bh": "jonah", "sbl": "", "mob": "jon", "chapters": 4},
    {"num": 33, "name": "Michée", "slug": "Michee", "usfm": "MIC", "bh": "micah", "sbl": "", "mob": "mic", "chapters": 7},
    {"num": 34, "name": "Nahum", "slug": "Nahum", "usfm": "NAM", "bh": "nahum", "sbl": "", "mob": "nah", "chapters": 3},
    {"num": 35, "name": "Habacuc", "slug": "Habacuc", "usfm": "HAB", "bh": "habakkuk", "sbl": "", "mob": "hab", "chapters": 3},
    {"num": 36, "name": "Sophonie", "slug": "Sophonie", "usfm": "ZEP", "bh": "zephaniah", "sbl": "", "mob": "zep", "chapters": 3},
    {"num": 37, "name": "Aggée", "slug": "Aggee", "usfm": "HAG", "bh": "haggai", "sbl": "", "mob": "hag", "chapters": 2},
    {"num": 38, "name": "Zacharie", "slug": "Zacharie", "usfm": "ZEC", "bh": "zechariah", "sbl": "", "mob": "zec", "chapters": 14},
    {"num": 39, "name": "Malachie", "slug": "Malachie", "usfm": "MAL", "bh": "malachi", "sbl": "", "mob": "mal", "chapters": 4},
    {"num": 40, "name": "Matthieu", "slug": "Matthieu", "usfm": "MAT", "bh": "matthew", "sbl": "Matt", "mob": "mat", "chapters": 28},
    {"num": 41, "name": "Marc", "slug": "Marc", "usfm": "MRK", "bh": "mark", "sbl": "Mark", "mob": "mar", "chapters": 16},
    {"num": 42, "name": "Luc", "slug": "Luc", "usfm": "LUK", "bh": "luke", "sbl": "Luke", "mob": "luk", "chapters": 24},
    {"num": 43, "name": "Jean", "slug": "Jean", "usfm": "JHN", "bh": "john", "sbl": "John", "mob": "joh", "chapters": 21},
    {"num": 44, "name": "Actes", "slug": "Actes", "usfm": "ACT", "bh": "acts", "sbl": "Acts", "mob": "act", "chapters": 28},
    {"num": 45, "name": "Romains", "slug": "Romains", "usfm": "ROM", "bh": "romans", "sbl": "Rom", "mob": "rom", "chapters": 16},
    {"num": 46, "name": "1 Corinthiens", "slug": "1-Corinthiens", "usfm": "1CO", "bh": "1_corinthians", "sbl": "1Cor", "mob": "1co", "chapters": 16},
    {"num": 47, "name": "2 Corinthiens", "slug": "2-Corinthiens", "usfm": "2CO", "bh": "2_corinthians", "sbl": "2Cor", "mob": "2co", "chapters": 13},
    {"num": 48, "name": "Galates", "slug": "Galates", "usfm": "GAL", "bh": "galatians", "sbl": "Gal", "mob": "gal", "chapters": 6},
    {"num": 49, "name": "Éphésiens", "slug": "Ephesiens", "usfm": "EPH", "bh": "ephesians", "sbl": "Eph", "mob": "eph", "chapters": 6},
    {"num": 50, "name": "Philippiens", "slug": "Philippiens", "usfm": "PHP", "bh": "philippians", "sbl": "Phil", "mob": "phi", "chapters": 4},
    {"num": 51, "name": "Colossiens", "slug": "Colossiens", "usfm": "COL", "bh": "colossians", "sbl": "Col", "mob": "col", "chapters": 4},
    {"num": 52, "name": "1 Thessaloniciens", "slug": "1-Thessaloniciens", "usfm": "1TH", "bh": "1_thessalonians", "sbl": "1Thess", "mob": "1th", "chapters": 5},
    {"num": 53, "name": "2 Thessaloniciens", "slug": "2-Thessaloniciens", "usfm": "2TH", "bh": "2_thessalonians", "sbl": "2Thess", "mob": "2th", "chapters": 3},
    {"num": 54, "name": "1 Timothée", "slug": "1-Timothee", "usfm": "1TI", "bh": "1_timothy", "sbl": "1Tim", "mob": "1ti", "chapters": 6},
    {"num": 55, "name": "2 Timothée", "slug": "2-Timothee", "usfm": "2TI", "bh": "2_timothy", "sbl": "2Tim", "mob": "2ti", "chapters": 4},
    {"num": 56, "name": "Tite", "slug": "Tite", "usfm": "TIT", "bh": "titus", "sbl": "Titus", "mob": "tit", "chapters": 3},
    {"num": 57, "name": "Philémon", "slug": "Philemon", "usfm": "PHM", "bh": "philemon", "sbl": "Phlm", "mob": "phm", "chapters": 1},
    {"num": 58, "name": "Hébreux", "slug": "Hebreux", "usfm": "HEB", "bh": "hebrews", "sbl": "Heb", "mob": "heb", "chapters": 13},
    {"num": 59, "name": "Jacques", "slug": "Jacques", "usfm": "JAS", "bh": "james", "sbl": "Jas", "mob": "jam", "chapters": 5},
    {"num": 60, "name": "1 Pierre", "slug": "1-Pierre", "usfm": "1PE", "bh": "1_peter", "sbl": "1Pet", "mob": "1pe", "chapters": 5},
    {"num": 61, "name": "2 Pierre", "slug": "2-Pierre", "usfm": "2PE", "bh": "2_peter", "sbl": "2Pet", "mob": "2pe", "chapters": 3},
    {"num": 62, "name": "1 Jean", "slug": "1-Jean", "usfm": "1JN", "bh": "1_john", "sbl": "1John", "mob": "1jo", "chapters": 5},
    {"num": 63, "name": "2 Jean", "slug": "2-Jean", "usfm": "2JN", "bh": "2_john", "sbl": "2John", "mob": "2jo", "chapters": 1},
    {"num": 64, "name": "3 Jean", "slug": "3-Jean", "usfm": "3JN", "bh": "3_john", "sbl": "3John", "mob": "3jo", "chapters": 1},
    {"num": 65, "name": "Jude", "slug": "Jude", "usfm": "JUD", "bh": "jude", "sbl": "Jude", "mob": "jud", "chapters": 1},
    {"num": 66, "name": "Apocalypse", "slug": "Apocalypse", "usfm": "REV", "bh": "revelation", "sbl": "Rev", "mob": "rev", "chapters": 22},
]


def resolve_book(identifier: str) -> dict[str, Any]:
    """Résout un livre biblique par son numéro (1-66), son nom français, son slug ou son code USFM."""
    ident = identifier.strip().lower()
    for b in BOOKS_TABLE:
        if (
            str(b["num"]) == ident
            or b["name"].lower() == ident
            or b["slug"].lower() == ident
            or b["usfm"].lower() == ident
            or b["bh"].lower() == ident
        ):
            return b
    raise ValueError(f"Livre biblique introuvable : {identifier!r}")


class HttpClient:
    """Client HTTP avec limitation de débit par domaine et réessais exponentiels."""

    def __init__(self, rate_limit_rps: float = 2.0, max_retries: int = 3) -> None:
        self.min_interval = 1.0 / max(rate_limit_rps, 0.1)
        self.max_retries = max_retries
        self.last_call_by_host: dict[str, float] = {}

    def _wait_rate_limit(self, host: str) -> None:
        now = time.monotonic()
        last = self.last_call_by_host.get(host, 0.0)
        elapsed = now - last
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_by_host[host] = time.monotonic()

    def get(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        for attempt in range(1, self.max_retries + 1):
            self._wait_rate_limit(host)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                body = ""
                try:
                    body = exc.read().decode("utf-8", errors="replace")[:400]
                except Exception:
                    pass
                if exc.code == 429:
                    raise RateLimitError(
                        f"HTTP 429 (Too Many Requests) sur {url} "
                        f"(intervalle min={self.min_interval:.2f}s). Corps: {body}"
                    ) from exc
                if 500 <= exc.code < 600 and attempt < self.max_retries:
                    delay = 1.5 ** attempt
                    print(
                        f"[retry {attempt}/{self.max_retries}] HTTP {exc.code} sur {url}, "
                        f"attente {delay:.1f}s...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    continue
                raise RuntimeError(
                    f"Erreur HTTP {exc.code} sur {url}. Détails: {body}"
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < self.max_retries:
                    delay = 1.5 ** attempt
                    print(
                        f"[retry {attempt}/{self.max_retries}] Erreur réseau sur {url} ({exc}), "
                        f"attente {delay:.1f}s...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    continue
                raise RuntimeError(f"Erreur réseau sur {url}: {exc}") from exc
        raise RuntimeError(f"Échec après {self.max_retries} tentatives sur {url}")


def clean_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def clean_inline(s: str) -> str:
    s = re.sub(r"<button[^>]*>.*?</button>", "", s, flags=re.S)
    s = re.sub(r'<span class="note">.*?</span>', "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ").replace("\u202f", " ")
    return re.sub(r"\s+", " ", s).strip()


def clean_neg(s: str) -> str:
    return re.sub(r"\[[a-z]\]", "", s).strip()


def cmd_collect(args: argparse.Namespace) -> None:
    book = resolve_book(args.book)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sermons_dir = out_dir / "sermons"
    sermons_dir.mkdir(parents=True, exist_ok=True)

    client = HttpClient(rate_limit_rps=args.rate_limit)
    bnum = book["num"]
    ch_start = args.chapter_start or 1
    ch_end = args.chapter_end or book["chapters"]

    if book["mob"]:
        intro_url = f"https://www.myopenbible.com/bible/intro/gty/{book['mob']}"
        try:
            intro_raw = client.get(intro_url)
            intro_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", intro_raw, flags=re.S)
            intro_paras = [
                clean_inline(p)
                for p in re.findall(r"<(?:p|h[1-6]|li|tr)[^>]*>(.*?)</(?:p|h[1-6]|li|tr)>", intro_text, re.S)
            ]
            intro_clean = "\n".join(p for p in intro_paras if p)
            (out_dir / f"intro_{book['mob']}.txt").write_text(intro_clean, encoding="utf-8")
        except Exception as exc:
            print(f"[info] Introduction non récupérée sur {intro_url}: {exc}", file=sys.stderr)

    if book["sbl"]:
        app_url = f"https://raw.githubusercontent.com/LogosBible/SBLGNT/master/data/sblgntapp/text/{book['sbl']}.txt"
        try:
            app_txt = client.get(app_url)
            (out_dir / f"sblgntapp_{book['sbl']}.txt").write_text(app_txt, encoding="utf-8")
        except Exception as exc:
            print(f"[info] Apparat SBLGNT non récupéré: {exc}", file=sys.stderr)

    sermon_codes: list[str] = []
    if args.sermon_codes:
        sermon_codes = [c.strip() for c in args.sermon_codes.split(",") if c.strip()]
    elif bnum >= 40 and args.max_sermons > 0:
        sermon_codes = [f"{bnum}-{i}" for i in range(1, args.max_sermons + 1)]

    s_results = []
    for code in sermon_codes:
        url = f"https://www.gty.org/sermons/{code}"
        try:
            raw = client.get(url)
        except Exception:
            if not args.sermon_codes:
                break
            continue
        title_m = re.search(r'<h1[^>]*class="media-page--title"[^>]*>(.*?)</h1>', raw, re.S)
        if not title_m:
            title_m = re.search(r"<title>(.*?)</title>", raw, re.S)
        title = clean_html(title_m.group(1)) if title_m else ""
        date_m = re.search(
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}", raw
        )
        date_str = date_m.group(0) if date_m else ""
        desc_m = re.search(
            r'<div class="media-page--description"[^>]*>(.*?)<div class="media-page--side">', raw, re.S
        )
        if not desc_m:
            desc_m = re.search(r'<div class="media-page--description"[^>]*>(.*)', raw, re.S)
        block = desc_m.group(1) if desc_m else raw
        paras = [clean_html(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", block, re.S)]
        paras = [p for p in paras if p and not p.startswith("ListenWatchRead")]
        text = "\n\n".join(paras)
        if len(text.split()) < 200:
            if not args.sermon_codes:
                break
            continue
        (sermons_dir / f"{code}.txt").write_text(text, encoding="utf-8")
        s_results.append(
            {
                "code": code,
                "url": url,
                "title": title,
                "date": date_str,
                "words": len(text.split()),
                "paras": len(paras),
            }
        )
    (sermons_dir / "summary.json").write_text(
        json.dumps(s_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    bg_neg: dict[str, str] = {}
    nbs_vers: dict[str, str] = {}
    il_data: dict[str, Any] = {}
    chapter_len: dict[int, int] = {}

    for c in range(ch_start, ch_end + 1):
        q = urllib.parse.quote_plus(f"{book['name']} {c}")
        raw_bg = client.get(f"https://www.biblegateway.com/passage/?search={q}&version=NEG1979")
        raw_bg = re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", raw_bg, flags=re.S)
        raw_bg = re.sub(
            r'<sup class="(?:footnote|crossreference|versenum)"[^>]*>.*?</sup>', "", raw_bg, flags=re.S
        )
        raw_bg = re.sub(r'<span class="chapternum">.*?</span>', "", raw_bg, flags=re.S)
        raw_bg = re.sub(r'<div class="(?:footnotes|crossrefs)"[^>]*>.*?</div>', "", raw_bg, flags=re.S)
        v_nums = sorted(
            {
                int(m.group(1))
                for m in re.finditer(rf'class="text [A-Za-z0-9]+-{c}-(\d+)"', raw_bg)
            }
        )
        max_v = max(v_nums) if v_nums else 0
        chapter_len[c] = max_v
        for v in range(1, max_v + 1):
            chunks = [
                clean_inline(m.group(1))
                for m in re.finditer(rf'<span[^>]*class="text [A-Za-z0-9]+-{c}-{v}"[^>]*>(.*?)</span>', raw_bg, re.S)
            ]
            bg_neg[f"{c}.{v}"] = clean_neg(" ".join(x for x in chunks if x))

        raw_nbs = client.get(f"https://www.bible.com/bible/104/{book['usfm']}.{c}.NBS")
        for v in range(1, max_v + 1):
            chunks = []
            for m in re.finditer(
                rf'data-usfm="{book["usfm"]}\.{c}\.{v}">(.*?)(?=<span class="[^"]*_verse"|</div>)',
                raw_nbs,
                re.S,
            ):
                block = m.group(1)
                for cm in re.finditer(r'<span class="[^"]*_content">(.*?)</span>', block, re.S):
                    t = clean_inline(cm.group(1))
                    if t:
                        chunks.append(t)
            nbs_vers[f"{c}.{v}"] = " ".join(chunks).strip()

        raw_il = client.get(f"https://biblehub.com/interlinear/{book['bh']}/{c}.htm")
        cur_v = 1
        il_data[str(c)] = {}
        for m in re.finditer(r'<table class="tablefloat">(.*?)</table>', raw_il, re.S):
            tb = m.group(1)
            vm = re.search(r'<span class="reftop3">(\d+)', tb)
            if vm:
                cur_v = int(vm.group(1))
            vkey = f"{c}.{cur_v}"
            il_data[str(c)].setdefault(vkey, [])
            strong_m = re.search(r'href="/(?:greek|hebrew)/(\d+)\.htm"', tb)
            trans_m = re.search(r'<span class="translit"><a[^>]*>(.*?)</a></span>', tb)
            orig_m = re.search(r'<span class="(?:greek|hebrew)">(.*?)</span>', tb)
            eng_m = re.search(r'<span class="eng">(.*?)</span>', tb)
            gram_m = re.search(r'href="/grammar/[^"]*"\s+title="([^"]*)">(.*?)</a>', tb)
            il_data[str(c)][vkey].append(
                {
                    "strong": strong_m.group(1) if strong_m else "",
                    "translit": clean_inline(trans_m.group(1)) if trans_m else "",
                    "orig": clean_inline(orig_m.group(1)) if orig_m else "",
                    "eng": clean_inline(eng_m.group(1)) if eng_m else "",
                    "morph_code": clean_inline(gram_m.group(2)) if gram_m else "",
                    "morph_desc": clean_inline(gram_m.group(1)) if gram_m else "",
                }
            )

    (out_dir / "interlinear_parsed.json").write_text(
        json.dumps(il_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    all_data: dict[str, Any] = {}
    for c in range(ch_start, ch_end + 1):
        for v in range(1, chapter_len.get(c, 0) + 1):
            ref = f"{c}.{v}"
            ba_raw = client.get(f"https://www.bible.audio/comparateur-bible-{bnum}-{c}-{v}.htm")
            bh_raw = client.get(f"https://biblehub.com/texts/{book['bh']}/{c}-{v}.htm")
            ba_vers: dict[str, str] = {}
            for m in re.finditer(
                rf'<div class="card-body"><strong><a href="bible-([A-Z0-9]+)-{bnum}-\d+-\d+-complet-contexte-non\.htm">.*?</a>\s*-\s*</strong>(.*?)</div>',
                ba_raw,
                re.S,
            ):
                ba_vers[m.group(1)] = clean_inline(m.group(2))
            for m in re.finditer(
                r'<div class="card-header"><h3[^>]*>(.*?)</h3></div>\s*<div class="card-body">(.*?)</div>',
                ba_raw,
                re.S,
            ):
                t = clean_inline(m.group(1))
                if "grec" in t.lower() or "sbl" in t.lower() or "hébreu" in t.lower():
                    ba_vers["ORIG"] = clean_inline(m.group(2))
            bh_eds: dict[str, str] = {}
            for m in re.finditer(
                r'<span class="versiontext"><a[^>]*>(.*?)</a><br></span><span class="(?:greek|hebrew)">(.*?)</span>',
                bh_raw,
                re.S,
            ):
                bh_eds[clean_inline(m.group(1))] = clean_inline(m.group(2))

            all_data[ref] = {
                "NEG79_BG": bg_neg.get(ref, ""),
                "NEG79_BA": ba_vers.get("NEG", ""),
                "LSG": ba_vers.get("LSG", ""),
                "S21": ba_vers.get("S21", ""),
                "Darby": ba_vers.get("DBY", ""),
                "NBS": nbs_vers.get(ref, ""),
                "ORIG_BA": ba_vers.get("ORIG", ""),
                "editions": bh_eds,
            }

    verses_path = out_dir / "verses_data.json"
    verses_path.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Succès! Données collectées dans : {out_dir} ({len(all_data)} versets, {len(s_results)} sermons)")


def cmd_lexicon(args: argparse.Namespace) -> None:
    client = HttpClient(rate_limit_rps=args.rate_limit)
    lang = args.lang.lower()
    if lang not in ("greek", "hebrew"):
        raise ValueError("--lang doit être 'greek' ou 'hebrew'")
    numbers = [s.strip() for s in args.strong.split(",") if s.strip()]
    results: dict[str, str] = {}
    for num in numbers:
        url = f"https://biblehub.com/{lang}/{num}.htm"
        raw = client.get(url)
        if lang == "greek":
            m = re.search(
                r"Thayer's Greek Lexicon(.*?)(?:Strong's Exhaustive Concordance|Forms and Transliterations| Englishman's Concordance)",
                raw,
                re.S,
            )
        else:
            m = re.search(
                r"Brown-Driver-Briggs(.*?)(?:Strong's Exhaustive Concordance|Forms and Transliterations|Englishman's Concordance)",
                raw,
                re.S,
            )
        results[num] = clean_inline(m.group(1)) if m else clean_inline(raw)[:2000]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Succès! Entrées lexicales écrites dans : {out_path}")


PLAN_PDF_CSS = """@page { size: Letter; margin: 18mm 18mm 16mm; }
body { font-family: Georgia, "Times New Roman", serif; font-size: 11pt; line-height: 1.45; color: #1a1a1a; max-width: none; margin: 0; }
h1 { font-size: 22pt; color: #1A2A40; margin: 0 0 4pt; border-bottom: 2px solid #B8862B; padding-bottom: 4pt; }
h2 { font-size: 13.5pt; color: #1A2A40; margin: 16pt 0 5pt; border-bottom: 1px solid #d9c9a3; padding-bottom: 2pt; page-break-after: avoid; }
p, li { margin: 3pt 0; text-align: justify; hyphens: auto; }
ul, ol { margin: 3pt 0 3pt 16pt; padding: 0; }
em { color: #5a4a2a; }
strong { color: #1A2A40; }
hr { border: 0; border-top: 1px solid #d9c9a3; margin: 10pt 0; }
table { border-collapse: collapse; margin: 6pt 0; font-size: 10pt; }
th, td { border-bottom: 1px solid #e3d6b8; padding: 3pt 10pt 3pt 0; text-align: left; }
th { color: #B8862B; font-variant: small-caps; }
a { color: #1A2A40; }
header#title-block-header { display: none; }
"""


def render_pdf_from_md(md_path: Path, title: str) -> Path:
    css_path = Path(tempfile.gettempdir()) / f"plan-{md_path.stem}.css"
    html_path = Path(tempfile.gettempdir()) / f"plan-{md_path.stem}.html"
    css_path.write_text(PLAN_PDF_CSS, encoding="utf-8")
    subprocess.run(
        [
            "pandoc",
            str(md_path),
            "-f",
            "markdown+lists_without_preceding_blankline",
            "-s",
            "--embed-resources",
            "--css",
            str(css_path),
            "--metadata",
            f"title={title} · Plan de prédication",
            "--metadata",
            "lang=fr",
            "-o",
            str(html_path),
        ],
        check=True,
    )
    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    chrome = next((p for p in chrome_candidates if os.path.exists(p)), None)
    if not chrome:
        raise RuntimeError("Navigateur Chrome ou Edge introuvable pour le rendu PDF.")
    pdf_path = md_path.with_suffix(".pdf")
    if pdf_path.exists():
        pdf_path.unlink()
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        check=True,
    )
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Échec de la génération du PDF : {pdf_path}")
    return pdf_path


def cmd_render(args: argparse.Namespace) -> None:
    """Rend le PDF d'un fichier Plan-Serie Markdown et vérifie l'absence de tiret cadratin."""
    md_path = Path(args.plan_md)
    if not md_path.exists():
        raise FileNotFoundError(f"Fichier Markdown introuvable : {md_path}")
    txt = md_path.read_text(encoding="utf-8").replace("\u2014", "-")
    md_path.write_text(txt, encoding="utf-8")
    m_title = re.search(r"^#\s+(.+)$", txt, re.M)
    title = m_title.group(1).strip() if m_title else md_path.stem
    pdf_path = render_pdf_from_md(md_path, title)
    print(f"Succès! PDF généré dans : {pdf_path} ({pdf_path.stat().st_size} octets)")


RESEARCH_SECTIONS = [
    ("contexte", "Contexte du passage"),
    ("arriere-plan", "Arrière-plan historique et culturel"),
    ("texte", "État du texte"),
    ("structure", "Structure et grammaire"),
    ("mots-cles", "Étude des mots-clés"),
    ("commentateurs", "Apports des commentateurs"),
    ("renvois", "Renvois et passages parallèles"),
    ("themes", "Thèmes théologiques"),
    ("reflexion", "Pistes de réflexion"),
]


def cmd_portal(args: argparse.Namespace) -> None:
    """Génère le portail autonome index.html à partir d'une spécification JSON."""
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    book = resolve_book(spec["book"])
    slug = book["slug"]
    bname = book["name"]
    n_chapters = book["chapters"]
    pad = 3 if n_chapters >= 100 else 2
    range_suffix = f"1-{n_chapters}" if n_chapters > 1 else "1"
    range_label = f"{bname} {range_suffix}"
    date_fr = spec["date_fr"]
    series_title = spec["series_title"]
    series_phrase = spec["series_phrase"]

    blocks = spec["blocks"]
    n_blocks = len(blocks)
    all_sermons = [s for b in blocks for s in b["sermons"]]

    puces_html = "".join(
        f'<li><a href="#sermon-{s["num"]}"><span class="vh">Sermon </span>{s["num"]}'
        f'<span class="vh"> ({bname} {s["num"]}\u00a0: {re.sub(r"<[^>]+>", "", s["title"])})</span></a></li>'
        for s in all_sermons
    )

    sommaire_base = f"Sommaire/Recherche-MacArthur-{slug}-{range_suffix}"
    sommaire_sections = "".join(
        f'<li><a href="{sommaire_base}.html#{sec_id}">{sec_label}'
        f'<span class="vh"> (recherche sur tout le livre)</span></a></li>'
        for sec_id, sec_label in RESEARCH_SECTIONS
    )

    mv_items = "".join(
        f'<li><span class="mv__ref"><span class="nw">{m["ref"]}</span></span> '
        f'<span class="mv__lib">{m["label"]}</span></li>'
        for m in spec["movements"]
    )

    sommaire_blocs_html = []
    for b in blocks:
        s_items = "".join(
            f'<li><a href="#sermon-{s["num"]}"><span class="sommaire__n" aria-hidden="true">{s["num"]}</span>'
            f'<span class="sommaire__ref">Dimanche {s["num"]} · <span class="nw">{bname} {s["num"]}</span></span>'
            f'<span class="vh">\u00a0: </span><span class="sommaire__lib">{s["title"]}</span></a></li>'
            for s in b["sermons"]
        )
        sommaire_blocs_html.append(
            f'<li class="sommaire__bloc"><p class="sommaire__nom">'
            f'<span class="sommaire__ch">{b["ch_label"]}</span><span class="vh">\u00a0: </span>'
            f'<span class="sommaire__titre">{b["short_title"]}</span></p>'
            f'<ol role="list">{s_items}</ol></li>'
        )
    sommaire_nav_html = "".join(sommaire_blocs_html)

    blocs_sections_html = []
    for b_idx, b in enumerate(blocks, start=1):
        cards_html = []
        for s in b["sermons"]:
            snum = s["num"]
            stitle_plain = re.sub(r"<[^>]+>", "", s["title"])
            ch_dir = f"{snum:0{pad}d}-{slug}-{snum}"
            ch_base = f"{ch_dir}/Recherche-MacArthur-{slug}-{snum}"
            ch_sections = "".join(
                f'<li><a href="{ch_base}.html#{sec_id}">{sec_label}'
                f'<span class="vh"> (recherche du dimanche {snum}\u00a0: {html.escape(stitle_plain)})</span></a></li>'
                for sec_id, sec_label in RESEARCH_SECTIONS
            )
            steps_html = "".join(
                f'<li><span class="etape__num" aria-hidden="true">{st["num"]}</span>'
                f'<span><span class="vh">{st["num"]} </span><span class="etape__nom">{st["name"]}</span> '
                f'<span class="etape__ref">{st["ref"]}</span></span></li>'
                for st in s["steps"]
            )
            gty_details = ""
            if s.get("gty_sermons"):
                gty_list = "".join(
                    f'<li><span class="gty__code"><span class="nw">{g["code"]}</span></span> '
                    f'<span><span class="gty__titre" lang="en">{g["title"]}</span> '
                    f'<span class="gty__ref"><span class="nw">{g["ref"]}</span></span></span></li>'
                    for g in s["gty_sermons"]
                )
                gty_details = (
                    f'<details class="repli">'
                    f'<summary><span>Sermons <abbr lang="en" title="Grace to You">GTY</abbr> de la '
                    f'<span class="nw">recherche ({len(s["gty_sermons"])})</span>'
                    f'<span class="vh"> du dimanche {snum}\u00a0: {html.escape(stitle_plain)}</span></span></summary>'
                    f'<div class="repli__corps"><ul class="gty" role="list">{gty_list}</ul></div>'
                    f'</details>'
                )
            trans_html = ""
            if s.get("transition"):
                tr = s["transition"]
                trans_html = (
                    f'<div class="transition">'
                    f'<p class="etiquette">Transition</p>'
                    f'<p class="transition__texte">{tr["text"]}</p>'
                    f'<p><a class="transition__lien" href="#sermon-{tr["next_num"]}">'
                    f'Vers le dimanche {tr["next_num"]}\u00a0: {tr["next_title"]}'
                    f'<span aria-hidden="true">\u00a0↓</span></a></p>'
                    f'</div>'
                )
            cards_html.append(
                f'<li class="sermon" id="sermon-{snum}" data-nav="sermon-{snum}">'
                f'<span class="s-n" aria-hidden="true">{snum}</span>'
                f'<h4 class="s-titre"><span class="s-kicker">Dimanche {snum} · <span class="nw">{bname} {snum}</span></span>'
                f'<span class="vh">\u00a0: </span><a href="{ch_base}.html">{s["title"]}<span class="vh"> (recherche exégétique)</span></a></h4>'
                f'<p class="s-gty">{s["gty_range"]}</p>'
                f'<p class="s-phrase"><span class="etiquette">Phrase à faire retenir</span> '
                f'<span class="s-phrase__txt"><span class="q">«</span>\u00a0{s["phrase"]}\u00a0<span class="q">»</span></span></p>'
                f'<div class="s-docs">'
                f'<a class="btn btn--plein" href="{ch_base}.html"><span>Lire la recherche<span class="vh"> du dimanche {snum}\u00a0: {html.escape(stitle_plain)}</span></span></a>'
                f'<a class="btn" href="{ch_base}.pdf"><span><span class="vh">Recherche du dimanche {snum}\u00a0: {html.escape(stitle_plain)}, version </span>PDF</span></a>'
                f'<a class="btn" href="{ch_base}.md"><span><span class="vh">Recherche du dimanche {snum}\u00a0: {html.escape(stitle_plain)}, version </span>Texte (.md)</span></a>'
                f'</div>'
                f'<div class="corps">'
                f'<div class="corps__col">'
                f'<p class="etiquette">Verset clé</p>'
                f'<figure class="verset"><blockquote><p><span class="q">«</span>\u00a0{s["key_verse"]["text"]}\u00a0<span class="q">»</span></p></blockquote>'
                f'<figcaption><span class="nw">{s["key_verse"]["ref"]}</span> · NEG79</figcaption></figure>'
                f'</div>'
                f'<div class="corps__col">'
                f'<p class="etiquette">Idée centrale</p><p class="idee">{s["central_idea"]}</p>'
                f'<p class="etiquette">Étapes</p><ol class="etapes" role="list">{steps_html}</ol>'
                f'</div></div>'
                f'<div class="pied-fiche">'
                f'<details class="repli"><summary><span>Sections de la recherche<span class="vh"> du dimanche {snum}\u00a0: {html.escape(stitle_plain)}</span></span></summary>'
                f'<div class="repli__corps"><ul class="sections" role="list">{ch_sections}</ul></div></details>'
                f'{gty_details}{trans_html}'
                f'<a class="retour" href="#sommaire">Retour au sommaire\u00a0<span aria-hidden="true">↑</span></a>'
                f'</div></li>'
            )
        blocs_sections_html.append(
            f'<section class="bloc" id="bloc-{b_idx}" aria-labelledby="bloc-{b_idx}-titre">'
            f'<h3 class="bloc__titre" id="bloc-{b_idx}-titre"><span class="bloc__ch">{b["ch_label"]}</span>'
            f'<span class="vh">\u00a0: </span><span class="bloc__nom">{b["full_title"]}</span></h3>'
            f'<ol class="sermons" role="list">{"".join(cards_html)}</ol></section>'
        )

    rappel_html = "".join(
        f'<li><a href="#sermon-{s["num"]}"><span class="rappel__n" aria-hidden="true">{s["num"]}</span>'
        f'<span class="vh">Dimanche {s["num"]}\u00a0: </span><span class="rappel__t">{s["rappel_short"]}</span></a></li>'
        for s in all_sermons
    )

    out_html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Étude de {range_label}</title>
<meta name="description" content="{html.escape(spec.get('meta_description', f'Accueil de l étude de {range_label} dans la perspective de John MacArthur.'))}">
<meta name="author" content="André-Guy Bruneau">
<meta name="color-scheme" content="dark">
<style>
  :root{{
    --nuit:#0a0a0a;--nuit-1:#121212;--nuit-2:#1b1b1b;
    --encre:#f3f0ec;--encre-doux:#c9c2ba;
    --or:#e8843c;--or-clair:#f6a85c;--feuille:#f0b659;--feuille-vif:#f7c97a;
    --filet:rgba(232,132,60,.28);--filet-fort:rgba(232,132,60,.65);
    --titre:"Cormorant Garamond","EB Garamond",Georgia,"Times New Roman",serif;
    --texte:"EB Garamond",Georgia,"Times New Roman",serif;
    --max:82rem;--colonne:46rem;--gout:clamp(1rem,4vw,2.5rem);
    --etiq:max(.875rem,.7em);--barre:6.6rem;color-scheme:dark;
  }}
  @media (min-width:48rem){{:root{{--barre:3.7rem;}}}}
  @media (max-height:30rem){{:root{{--barre:0rem;}}}}
  *{{box-sizing:border-box;}}
  html{{-webkit-text-size-adjust:100%;text-size-adjust:100%;scroll-padding-top:calc(var(--barre) + .9rem);}}
  body{{
    margin:0;font-family:var(--texte);font-size:clamp(1.2rem,.95rem + .85vw,1.45rem);line-height:1.75;
    color:var(--encre);background:var(--nuit);
    background-image:
      radial-gradient(120% 70% at 50% -10%, rgba(240,182,89,.10), transparent 55%),
      radial-gradient(90% 60% at 85% 8%, rgba(232,132,60,.06), transparent 60%),
      radial-gradient(100% 70% at 12% 35%, rgba(232,132,60,.05), transparent 58%);
    background-repeat:no-repeat;overflow-wrap:break-word;
  }}
  .grain{{
    position:fixed;inset:0;z-index:3;pointer-events:none;opacity:.03;mix-blend-mode:overlay;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }}
  .vignette{{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(135% 105% at 50% 35%, transparent 56%, rgba(0,0,0,.42) 100%);}}
  .tete,main,.pied{{position:relative;z-index:1;}}
  a{{color:var(--feuille);}}
  :focus-visible{{outline:3px solid var(--feuille-vif);outline-offset:3px;border-radius:4px;}}
  ::selection{{background:rgba(232,132,60,.34);color:#fff;}}
  .nw{{white-space:nowrap;}}
  .vh{{position:absolute !important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;}}
  abbr[title]{{text-decoration:underline dotted;text-decoration-thickness:1px;text-underline-offset:.18em;cursor:help;}}
  .q{{color:var(--or);font-style:normal;}}
  .evitement{{position:absolute;left:1rem;top:-8rem;z-index:100;padding:.6rem 1rem;border-radius:4px;background:var(--or);color:var(--nuit);font-weight:600;text-decoration:none;}}
  .evitement:focus{{top:.6rem;}}
  .barre{{position:sticky;top:0;z-index:30;background:rgba(10,10,10,.95);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--filet);}}
  @media (max-height:30rem){{.barre{{position:relative;}}}}
  .barre__in{{max-width:var(--max);margin:0 auto;padding:.3rem var(--gout);display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:.2rem .6rem;}}
  .barre a{{text-decoration:none;}}
  .barre__marque{{display:inline-flex;align-items:center;min-height:2.75rem;font-family:var(--titre);font-weight:600;font-size:1.3rem;letter-spacing:.06em;white-space:nowrap;color:var(--or-clair);}}
  .barre ul{{margin:0;padding:0;list-style:none;}}
  .barre__liens{{display:flex;justify-content:flex-end;gap:.2rem;}}
  .barre__liens a{{display:inline-flex;align-items:center;justify-content:center;min-height:2.75rem;padding:0 .75rem;border-radius:5px;font-size:1.1rem;line-height:1.2;color:var(--encre);white-space:nowrap;}}
  .barre__liens a:hover{{color:var(--or-clair);background:rgba(232,132,60,.1);}}
  .barre__liens a[aria-current]{{color:var(--or-clair);box-shadow:inset 0 -2px 0 var(--or);}}
  .barre__puces{{grid-column:1 / -1;display:grid;grid-template-columns:repeat({n_chapters},minmax(0,1fr));gap:.2rem;}}
  .barre__puces li{{display:flex;align-items:center;justify-content:center;min-width:0;}}
  .barre__puces a{{display:inline-flex;align-items:center;justify-content:center;width:min(2.75rem,100%);height:2.75rem;border:1px solid var(--filet-fort);border-radius:50%;font-family:var(--titre);font-weight:600;font-size:1.35rem;line-height:1;color:var(--encre);}}
  .barre__puces a:hover{{border-color:var(--or);color:var(--or-clair);background:rgba(232,132,60,.12);}}
  .barre__puces a[aria-current]{{background:var(--or);border-color:var(--or);color:var(--nuit);}}
  @supports (aspect-ratio:1){{.barre__puces a{{height:auto;aspect-ratio:1;}}}}
  @media (max-width:25.99rem){{
    .barre__in{{grid-template-columns:minmax(0,1fr);}}
    .barre__marque{{display:none;}}
    .barre__liens{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));}}
    .barre__liens a{{white-space:normal;text-align:center;}}
  }}
  @media (min-width:48rem){{
    .barre__in{{display:flex;gap:.5rem 1rem;}}
    .barre__marque{{margin-right:auto;}}
    .barre__puces{{display:flex;flex-wrap:wrap;gap:.3rem;}}
    .barre__puces a{{width:2.75rem;}}
  }}
  .tete{{max-width:var(--max);margin:0 auto;padding:clamp(1rem,2.5vw,1.8rem) var(--gout) 0;}}
  .tete__cadre{{position:relative;text-align:center;padding:clamp(1.8rem,4.5vw,3.2rem) clamp(1rem,4vw,3rem) clamp(1.7rem,4vw,2.8rem);border:1px solid var(--filet);background:radial-gradient(80% 60% at 50% 0%, rgba(240,182,89,.06), transparent 70%);}}
  .tete__cadre::before,.tete__cadre::after{{content:"";position:absolute;width:18px;height:18px;pointer-events:none;}}
  .tete__cadre::before{{top:-1px;left:-1px;border-top:2px solid var(--or);border-left:2px solid var(--or);}}
  .tete__cadre::after{{bottom:-1px;right:-1px;border-bottom:2px solid var(--or);border-right:2px solid var(--or);}}
  .tete__kicker{{margin:0 0 .5rem;font-size:var(--etiq);letter-spacing:.34em;text-transform:uppercase;color:var(--or);}}
  h1{{margin:0 auto;max-width:18em;padding:.04em .06em .16em;font-family:var(--titre);font-weight:600;font-size:clamp(2.2rem,1.35rem + 3.3vw,4.1rem);line-height:1.06;letter-spacing:.015em;text-wrap:balance;color:var(--or-clair);background:linear-gradient(176deg,#f9e1bb 0%,var(--or-clair) 48%,var(--or) 100%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 30px rgba(240,182,89,.22));}}
  @media (forced-colors:active){{h1{{background:none;-webkit-text-fill-color:CanvasText;filter:none;}}}}
  .ornement{{display:flex;align-items:center;justify-content:center;gap:1rem;width:min(20rem,80%);margin:1.2rem auto;color:var(--or);}}
  .ornement::before,.ornement::after{{content:"";height:1px;flex:1;background:linear-gradient(90deg,transparent,var(--filet-fort),transparent);}}
  .ornement span{{font-size:.8rem;line-height:1;}}
  .tete__verset{{margin:0 auto;max-width:48rem;}}
  .tete__verset blockquote{{margin:0;}}
  .tete__verset p{{margin:0;font-family:var(--titre);font-style:italic;font-weight:500;font-size:clamp(1.3rem,1rem + 1vw,1.85rem);line-height:1.55;color:var(--encre);text-wrap:balance;}}
  .tete__verset figcaption{{margin-top:.9rem;font-size:var(--etiq);letter-spacing:.28em;text-transform:uppercase;color:var(--or);}}
  .tete__serie{{margin:1.5rem 0 0;}}
  .tete__serie .etiquette{{display:block;margin-bottom:.15rem;color:var(--encre-doux);}}
  .tete__phrase{{font-family:var(--titre);font-weight:600;font-size:clamp(1.45rem,1.15rem + 1vw,2rem);line-height:1.3;color:var(--feuille);}}
  .tete__meta{{margin:1.1rem auto 0;max-width:40rem;font-size:.92em;line-height:1.55;color:var(--encre-doux);}}
  main{{max-width:var(--max);margin:0 auto;padding:0 var(--gout);}}
  .sec{{padding-top:clamp(2.4rem,6vw,4rem);}}
  .sec-tete{{text-align:center;margin-bottom:1.6rem;}}
  .kicker{{margin:0 0 .5rem;font-size:var(--etiq);letter-spacing:.28em;text-transform:uppercase;color:var(--or);}}
  .kicker::before{{content:"\\25C6";content:"\\25C6" / "";margin-right:.7em;font-size:.72em;vertical-align:.12em;}}
  h2{{margin:0;font-family:var(--titre);font-weight:600;font-size:clamp(2.05rem,1.4rem + 2.2vw,3.1rem);line-height:1.1;color:var(--encre);text-wrap:balance;}}
  .sec-tete h2::after{{content:"";display:block;width:2.6rem;height:1px;margin:1rem auto 0;background:var(--filet-fort);}}
  .lead{{max-width:var(--colonne);margin:0 auto 1rem;padding-left:1.2rem;border-left:3px solid var(--or);font-size:1.04em;line-height:1.7;color:#faf3ec;text-wrap:pretty;}}
  .question{{max-width:var(--colonne);margin:0 auto;padding-left:1.2rem;border-left:3px solid transparent;line-height:1.65;color:var(--encre);}}
  .question strong,.carte__question strong{{font-family:var(--titre);font-style:italic;font-weight:600;font-size:1.12em;color:var(--feuille);}}
  .divider{{display:flex;align-items:center;justify-content:center;gap:1.4rem;margin:clamp(2.2rem,5vw,3.4rem) auto 0;color:var(--or);}}
  .divider::before,.divider::after{{content:"";height:1px;width:min(7rem,22%);background:linear-gradient(90deg,transparent,var(--filet-fort),transparent);}}
  .divider span{{font-size:.8rem;}}
  .etiquette{{margin:0;font-size:var(--etiq);font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--or);line-height:1.5;}}
  .btn{{display:inline-flex;align-items:center;justify-content:center;min-height:2.9rem;padding:.35rem 1rem;border:1px solid var(--filet-fort);border-radius:6px;font-size:max(1.1rem,.95em);line-height:1.2;text-align:center;text-decoration:none;color:var(--encre);}}
  .btn:hover{{border-color:var(--or);color:var(--or-clair);background:rgba(232,132,60,.1);}}
  .btn--plein{{background:var(--or);border-color:var(--or);color:var(--nuit);font-weight:600;}}
  .btn--plein:hover{{background:var(--or-clair);border-color:var(--or-clair);color:var(--nuit);}}
  .actions{{display:flex;flex-wrap:wrap;gap:.55rem;}}
  @media (max-width:29.99rem){{.actions{{display:grid;grid-template-columns:1fr 1fr;}}.actions .btn--plein{{grid-column:1 / -1;}}}}
  .livre{{display:grid;gap:1.2rem;align-items:start;grid-template-columns:minmax(0,1fr);}}
  @media (min-width:64rem){{.livre{{grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);}}}}
  .carte{{display:flex;flex-direction:column;gap:.85rem;padding:clamp(1.15rem,3vw,1.6rem) clamp(1.05rem,3vw,1.7rem) clamp(1.2rem,3vw,1.6rem);border:1px solid var(--filet);border-left:3px solid var(--or);border-radius:0 10px 10px 0;background:linear-gradient(180deg,rgba(27,27,27,.78),rgba(18,18,18,.45));}}
  .carte p{{margin:0;}}
  .carte h3{{margin:0;font-family:var(--titre);font-weight:600;font-size:clamp(1.65rem,1.3rem + 1vw,2.2rem);line-height:1.12;color:var(--or-clair);}}
  .carte__texte{{line-height:1.7;color:var(--encre);text-wrap:pretty;}}
  @media (max-width:25.99rem){{.carte__sep{{display:none;}}.carte__date{{display:block;}}}}
  .carte__question{{padding:.75rem 0 .1rem 1rem;border-top:1px solid var(--filet);line-height:1.65;color:var(--encre);border-left:2px solid var(--filet-fort);}}
  .carte__duree{{padding:.75rem 1rem .8rem;border:1px solid var(--filet);border-radius:6px;background:rgba(232,132,60,.05);line-height:1.6;}}
  .carte__duree .etiquette{{display:block;}}
  .carte .actions{{margin-top:0;padding-top:.35rem;}}
  .rubriques{{display:grid;gap:.15rem 1.4rem;grid-template-columns:repeat(auto-fill,minmax(min(100%,13rem),1fr));margin:.1rem 0 0;padding:0;list-style:none;}}
  .rubriques li{{position:relative;padding-left:1.2rem;line-height:1.5;color:var(--encre);}}
  .rubriques li::before{{content:"\\25C6";content:"\\25C6" / "";position:absolute;left:0;top:.55em;font-size:.55em;color:var(--or);}}
  .sections{{display:flex;flex-wrap:wrap;gap:.45rem;margin:0;padding:0;list-style:none;}}
  .sections a{{display:inline-flex;align-items:center;min-height:2.75rem;padding:.2rem .9rem;border:1px solid var(--filet-fort);border-radius:999px;font-size:.92em;line-height:1.25;color:var(--encre);text-decoration:none;}}
  .sections a:hover{{border-color:var(--or);color:var(--or-clair);background:rgba(232,132,60,.08);}}
  .mouvements{{margin-top:1.2rem;padding:clamp(1.15rem,3vw,1.6rem) clamp(1.05rem,3vw,1.7rem);border:1px solid var(--filet);border-radius:10px;background:linear-gradient(180deg,rgba(27,27,27,.6),rgba(18,18,18,.3));}}
  .mouvements__tete{{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:.3rem 1.2rem;margin-bottom:1rem;}}
  .mouvements h3{{margin:0;font-family:var(--titre);font-weight:600;font-size:clamp(1.55rem,1.25rem + .9vw,2rem);line-height:1.15;color:var(--or-clair);}}
  .mouvements__lien{{display:inline-flex;align-items:center;min-height:2.75rem;font-size:.92em;}}
  .mv{{list-style:none;margin:0;padding:0;counter-reset:mv;columns:2 24rem;column-gap:2.6rem;}}
  .mv li{{counter-increment:mv;position:relative;break-inside:avoid;margin:0 0 .65rem;padding:.55rem .2rem .6rem 3.2rem;border-top:1px solid var(--filet);}}
  .mv li::before{{content:counter(mv);position:absolute;left:0;top:.65rem;display:flex;align-items:center;justify-content:center;width:2.2rem;height:2.2rem;border:1px solid var(--filet-fort);border-radius:50%;background:rgba(232,132,60,.06);font-family:var(--titre);font-weight:600;font-size:1.2rem;line-height:1;color:var(--or);}}
  .mv__ref{{display:block;font-size:var(--etiq);letter-spacing:.16em;text-transform:uppercase;color:var(--or);}}
  .mv__lib{{display:block;line-height:1.5;color:var(--encre);}}
  .sommaire{{display:grid;gap:1rem 1.4rem;margin:1.8rem 0 .4rem;padding:0;list-style:none;}}
  .sommaire__bloc{{min-width:0;}}
  @media (min-width:60rem){{
    .sommaire{{grid-template-columns:repeat({n_blocks},minmax(0,1fr));grid-template-rows:auto auto;}}
    .sommaire__bloc{{display:grid;grid-template-rows:subgrid;grid-row:span 2;row-gap:0;}}
    .sommaire__nom{{align-self:end;}}
  }}
  .sommaire__nom{{margin:0 0 .5rem;line-height:1.3;}}
  .sommaire__ch{{display:block;font-size:var(--etiq);letter-spacing:.2em;text-transform:uppercase;color:var(--or);}}
  .sommaire__titre{{font-family:var(--titre);font-weight:600;font-size:1.12em;color:var(--or-clair);}}
  .sommaire ol{{display:grid;gap:.5rem;margin:0;padding:0;list-style:none;}}
  .sommaire ol li{{display:flex;}}
  .sommaire ol a{{flex:1;}}
  .sommaire a{{position:relative;display:flex;flex-direction:column;justify-content:center;min-height:4.2rem;padding:.55rem .9rem .6rem 3.6rem;border:1px solid var(--filet-fort);border-radius:8px;color:var(--encre);text-decoration:none;line-height:1.3;background:rgba(18,18,18,.35);}}
  .sommaire a:hover{{border-color:var(--or);background:rgba(232,132,60,.08);}}
  .sommaire__n{{position:absolute;left:.75rem;top:50%;transform:translateY(-50%);display:flex;align-items:center;justify-content:center;width:2.2rem;height:2.2rem;border:1px solid var(--filet-fort);border-radius:50%;font-family:var(--titre);font-weight:600;font-size:1.25rem;line-height:1;color:var(--or-clair);}}
  .sommaire__ref{{font-size:var(--etiq);letter-spacing:.14em;text-transform:uppercase;color:var(--encre-doux);}}
  .sommaire__lib{{font-family:var(--titre);font-weight:600;font-size:1.15em;}}
  .bloc{{margin-top:clamp(1.8rem,4vw,2.6rem);}}
  .bloc__titre{{display:flex;flex-wrap:wrap;align-items:baseline;gap:.1rem 1rem;margin:0 0 1rem;padding:.65rem .8rem .55rem;border-bottom:1px solid var(--filet-fort);background:linear-gradient(90deg,rgba(232,132,60,.11),transparent 75%);font-weight:inherit;}}
  .bloc__ch{{font-size:var(--etiq);letter-spacing:.22em;text-transform:uppercase;color:var(--or);}}
  .bloc__ch::before{{content:"\\25C6";content:"\\25C6" / "";margin-right:.6em;font-size:.72em;vertical-align:.12em;}}
  .bloc__nom{{font-family:var(--titre);font-weight:600;font-size:clamp(1.85rem,1.45rem + 1.3vw,2.6rem);line-height:1.2;color:var(--or-clair);}}
  .sermons{{display:grid;gap:1.3rem;margin:0;padding:0;list-style:none;}}
  .sermon{{position:relative;display:grid;column-gap:.9rem;row-gap:.75rem;grid-template-columns:auto minmax(0,1fr);grid-template-areas:"n titre" "gty gty" "phrase phrase" "docs docs" "corps corps" "pied pied";align-items:start;padding:clamp(1.1rem,3vw,1.6rem) clamp(1rem,3vw,1.7rem) clamp(1rem,2.5vw,1.3rem);border:1px solid var(--filet);border-left:3px solid var(--or);border-radius:0 10px 10px 0;background:linear-gradient(180deg,rgba(27,27,27,.78),rgba(18,18,18,.42));}}
  .sermon:target{{border-color:var(--or);box-shadow:0 0 0 1px var(--or),0 0 32px rgba(232,132,60,.22);}}
  .sermon > *{{margin:0;min-width:0;}}
  .s-n{{grid-area:n;display:flex;align-items:center;justify-content:center;width:2.9rem;height:2.9rem;margin-top:.2rem;border:1px solid var(--filet-fort);border-radius:50%;background:rgba(232,132,60,.08);font-family:var(--titre);font-weight:600;font-size:1.65rem;line-height:1;color:var(--or-clair);}}
  .s-titre{{grid-area:titre;font-weight:inherit;}}
  .s-kicker{{display:block;margin-bottom:.15rem;font-size:var(--etiq);letter-spacing:.2em;text-transform:uppercase;color:var(--or);line-height:1.4;}}
  @media (max-width:25.99rem){{.s-kicker{{letter-spacing:.16em;}}}}
  .s-titre a{{font-family:var(--titre);font-weight:600;font-size:clamp(1.55rem,1.3rem + .8vw,2rem);line-height:1.12;color:var(--encre);text-decoration:underline;text-decoration-color:var(--filet-fort);text-decoration-thickness:1px;text-underline-offset:.16em;text-wrap:balance;}}
  .s-titre a:hover{{color:var(--or-clair);text-decoration-color:var(--or);}}
  .s-gty{{grid-area:gty;font-size:.92em;color:var(--encre-doux);}}
  .s-phrase{{grid-area:phrase;}}
  .s-phrase .etiquette{{display:block;}}
  .s-phrase__txt{{font-family:var(--titre);font-style:italic;font-size:1.22em;line-height:1.4;color:#faf3ec;}}
  .s-docs{{grid-area:docs;display:grid;grid-template-columns:1fr 1fr;gap:.5rem;}}
  .s-docs .btn--plein{{grid-column:1 / -1;}}
  .s-docs .btn{{padding:.35rem .6rem;}}
  .corps{{grid-area:corps;display:grid;grid-template-columns:minmax(0,1fr);gap:1.2rem 2.2rem;padding-top:1.05rem;border-top:1px solid var(--filet);}}
  @media (min-width:58rem){{.corps{{grid-template-columns:minmax(0,1fr) minmax(0,1.08fr);}}}}
  .corps__col > .etiquette{{margin-bottom:.35rem;}}
  .corps__col > .etiquette ~ .etiquette{{margin-top:1.1rem;}}
  .idee{{margin:0;line-height:1.68;color:var(--encre);text-wrap:pretty;}}
  .verset{{margin:0;padding:1.05rem 1.2rem 1rem 1.3rem;border:1px solid var(--filet);border-left:3px solid var(--or);border-radius:0 6px 6px 0;background:linear-gradient(180deg,rgba(232,132,60,.08),rgba(232,132,60,.02));}}
  .verset blockquote{{margin:0;}}
  .verset p{{margin:0;font-family:var(--titre);font-style:italic;font-size:1.12em;line-height:1.55;color:var(--encre);}}
  .verset figcaption{{margin-top:.6rem;font-size:var(--etiq);letter-spacing:.2em;text-transform:uppercase;color:var(--or);}}
  .etapes{{list-style:none;margin:0;padding:0;display:grid;gap:.6rem;}}
  .etapes li{{display:grid;grid-template-columns:2.4em minmax(0,1fr);column-gap:.3rem;}}
  .etape__num{{font-family:var(--titre);font-weight:600;font-size:1.08em;line-height:1.35;color:var(--or);}}
  .etape__nom{{display:block;font-family:var(--titre);font-weight:600;font-size:1.1em;line-height:1.3;color:var(--encre);}}
  .etape__ref{{display:block;font-size:.88em;line-height:1.45;color:var(--encre-doux);}}
  .pied-fiche{{grid-area:pied;display:flex;flex-wrap:wrap;align-items:flex-start;gap:.6rem;padding-top:1rem;border-top:1px solid var(--filet);}}
  .repli{{flex:0 1 auto;min-width:0;}}
  .repli[open]{{flex-basis:100%;}}
  .repli > summary{{display:inline-flex;align-items:center;gap:.6rem;min-height:2.9rem;padding:.3rem 1rem .3rem .75rem;border:1px solid var(--filet-fort);border-radius:6px;cursor:pointer;list-style:none;font-size:max(1.1rem,.95em);line-height:1.25;color:var(--feuille);}}
  .repli > summary::-webkit-details-marker{{display:none;}}
  .repli > summary::before{{content:"+";content:"+" / "";display:inline-flex;align-items:center;justify-content:center;flex:none;width:1.7rem;height:1.7rem;border:1px solid var(--filet-fort);border-radius:50%;font-size:1.15rem;line-height:1;color:var(--or);}}
  .repli[open] > summary::before{{content:"\\2212";content:"\\2212" / "";}}
  .repli > summary:hover{{border-color:var(--or);color:var(--feuille-vif);background:rgba(232,132,60,.08);}}
  .repli__corps{{margin-top:.7rem;padding:1rem 1.1rem;border:1px solid var(--filet);border-radius:8px;background:rgba(10,10,10,.35);}}
  .gty{{list-style:none;margin:0;padding:0;display:grid;gap:.55rem 2rem;grid-template-columns:repeat(auto-fill,minmax(min(100%,22rem),1fr));}}
  .gty li{{display:grid;grid-template-columns:3.6em minmax(0,1fr);column-gap:.5rem;line-height:1.4;}}
  .gty__code{{color:var(--or-clair);font-weight:600;}}
  .gty__titre{{color:var(--encre);}}
  .gty__ref{{display:block;font-size:.88em;color:var(--encre-doux);}}
  .transition{{flex-basis:100%;margin-top:.3rem;padding:.85rem 1rem .9rem;border-left:2px solid var(--filet-fort);background:linear-gradient(90deg,rgba(232,132,60,.06),transparent 80%);}}
  .transition p{{margin:0;}}
  .transition__texte{{max-width:var(--colonne);line-height:1.65;color:var(--encre);text-wrap:pretty;}}
  .transition__lien{{display:inline-block;padding:.45rem 0;font-weight:600;line-height:1.45;}}
  .retour{{display:inline-flex;align-items:center;min-height:2.75rem;margin-left:auto;font-size:.95em;color:var(--feuille);}}
  @media (min-width:48rem){{
    .sermon{{grid-template-columns:3.6rem minmax(0,1fr);column-gap:1.4rem;grid-template-areas:"n titre" "n gty" "n phrase" "n docs" ". corps" ". pied";}}
    .s-n{{width:3.4rem;height:3.4rem;font-size:1.95rem;}}
    .s-docs{{display:flex;flex-wrap:wrap;}}
    .s-docs .btn{{padding:.35rem 1rem;}}
  }}
  @media (min-width:64rem){{
    .sermon{{grid-template-columns:3.6rem minmax(0,1fr) 17rem;grid-template-areas:"n titre docs" "n gty docs" "n phrase docs" ". corps corps" ". pied pied";}}
    .s-docs{{display:grid;}}
    .s-docs .btn{{padding:.35rem .6rem;}}
  }}
  .conclusion{{text-align:center;}}
  .rappel{{display:grid;gap:.6rem;margin:0 auto;padding:0;list-style:none;max-width:68rem;text-align:left;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr));}}
  .rappel a{{display:flex;align-items:center;gap:.85rem;min-height:3.4rem;height:100%;padding:.55rem 1rem;border:1px solid var(--filet-fort);border-radius:8px;text-decoration:none;color:var(--encre);background:rgba(18,18,18,.35);}}
  .rappel a:hover{{border-color:var(--or);background:rgba(232,132,60,.08);}}
  .rappel__n{{flex:none;display:flex;align-items:center;justify-content:center;width:2.2rem;height:2.2rem;border:1px solid var(--filet-fort);border-radius:50%;font-family:var(--titre);font-weight:600;font-size:1.2rem;line-height:1;color:var(--or-clair);}}
  .rappel__t{{font-family:var(--titre);font-style:italic;font-size:1.18em;line-height:1.3;}}
  .conclusion .ornement{{margin:1.8rem auto 1.4rem;}}
  .conclusion__phrase{{margin:.2rem auto 0;max-width:26em;font-family:var(--titre);font-weight:600;font-size:clamp(1.6rem,1.25rem + 1.4vw,2.35rem);line-height:1.25;color:var(--feuille);text-wrap:balance;}}
  .benediction{{max-width:46rem;margin:2rem auto 0;}}
  .benediction .etiquette{{margin-bottom:.5rem;}}
  .benediction .verset{{text-align:left;}}
  .benediction .verset p{{font-size:1.2em;}}
  .pied{{margin-top:clamp(2.6rem,6vw,4rem);padding:2rem var(--gout) 2.6rem;text-align:center;border-top:1px solid var(--filet);background:linear-gradient(180deg,transparent,rgba(16,16,16,.7));}}
  .pied .ornement{{margin:0 auto 1.1rem;}}
  .pied p{{margin:.25rem 0;font-size:.92em;line-height:1.55;color:var(--encre-doux);}}
  .pied .pied__nom{{margin-bottom:.4rem;font-family:var(--titre);font-weight:600;font-size:1.6rem;color:var(--encre);}}
  .pied .pied__sdg{{margin-top:1.3rem;font-size:var(--etiq);letter-spacing:.36em;text-transform:uppercase;color:var(--or);}}
  @media (max-width:19.99rem){{
    .nw{{white-space:normal;}}
    .actions,.s-docs{{grid-template-columns:minmax(0,1fr);}}
    .sections a,.sommaire a,.rappel a,.btn,.repli > summary{{min-width:0;overflow-wrap:anywhere;-webkit-hyphens:auto;hyphens:auto;}}
  }}
  @media (prefers-reduced-motion:no-preference){{
    html{{scroll-behavior:smooth;}}
    .btn,.sections a,.barre a,.sommaire a,.rappel a,.repli > summary,.sermon{{transition:background-color .2s,border-color .2s,color .2s,box-shadow .3s;}}
  }}
  @media print{{
    :root{{--encre:#111;--encre-doux:#444;--or:#8a4510;--or-clair:#5c2e0a;--feuille:#5c2e0a;--feuille-vif:#5c2e0a;--filet:#bbb;--filet-fort:#888;color-scheme:light;}}
    body{{background:#fff;color:#000;font-size:11pt;}}
    .barre,.evitement,.grain,.vignette{{display:none;}}
    h1{{background:none;-webkit-text-fill-color:#000;color:#000;filter:none;}}
    .lead,.s-phrase__txt{{color:var(--encre);}}
    .carte,.verset,.sermon,.mouvements,.bloc__titre,.tete__cadre{{background:none;}}
    .sommaire a,.rappel a,.sections a,.repli__corps,.transition,.carte__duree,.s-n,.mv li::before{{background:none;}}
    .btn--plein{{background:none;border-color:var(--or);color:var(--encre);}}
    .sermon{{break-inside:avoid;}}
    a{{color:#000;}}
  }}
</style>
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<div class="grain" aria-hidden="true"></div>
<div class="vignette" aria-hidden="true"></div>

<nav class="barre" aria-label="Accès rapide">
  <div class="barre__in">
    <a class="barre__marque" href="#haut"><span class="nw">{range_label}</span><span class="vh">\u00a0: haut de la page</span></a>
    <ul class="barre__liens" role="list">
      <li><a href="#livre">Livre et plan</a></li>
      <li><a href="#sermons">Sermons</a></li>
    </ul>
    <ul class="barre__puces" role="list">{puces_html}</ul>
  </div>
</nav>

<header class="tete" id="haut" data-nav="">
  <div class="tete__cadre">
    <p class="tete__kicker">Étude · <span class="nw">{range_label}</span></p>
    <h1>{series_title}</h1>
    <div class="ornement" aria-hidden="true"><span>◆</span></div>
    <figure class="tete__verset">
      <blockquote><p><span class="q">«</span>\u00a0{spec["header_verse"]["text"]}\u00a0<span class="q">»</span></p></blockquote>
      <figcaption><span class="nw">{spec["header_verse"]["ref"]}</span> · NEG79</figcaption>
    </figure>
    <p class="tete__serie"><span class="etiquette">Phrase de la série</span><span class="vh">\u00a0: </span><span class="tete__phrase">{series_phrase}</span></p>
    <p class="tete__meta">Recherche exégétique et plan de série · Perspective John MacArthur · <span class="nw">André-Guy Bruneau</span></p>
  </div>
</header>

<main id="contenu">
  <section class="sec" id="livre" aria-labelledby="livre-titre" data-nav="livre">
    <div class="sec-tete">
      <p class="kicker">Vue d'ensemble</p>
      <h2 id="livre-titre">Le livre entier</h2>
    </div>
    <div class="livre">
      <article class="carte" aria-labelledby="carte-recherche">
        <p class="etiquette"><span class="nw">{range_label}</span><span class="carte__sep"> · </span><span class="carte__date nw">{date_fr}</span></p>
        <h3 id="carte-recherche">Recherche sur tout le livre</h3>
        <p class="carte__texte">{spec["book_card"]["summary_html"]}</p>
        <p class="carte__question">{spec["book_card"]["question_html"]}</p>
        <div class="actions">
          <a class="btn btn--plein" href="{sommaire_base}.html"><span>Lire la recherche<span class="vh"> sur tout le livre, <span class="nw">{range_label}</span></span></span></a>
          <a class="btn" href="{sommaire_base}.pdf"><span><span class="vh">Recherche sur tout le livre, version </span>PDF</span></a>
          <a class="btn" href="{sommaire_base}.md"><span><span class="vh">Recherche sur tout le livre, version </span>Texte (.md)</span></a>
        </div>
        <p class="etiquette">Sections de la recherche</p>
        <ul class="sections" role="list">{sommaire_sections}</ul>
      </article>
      <article class="carte" aria-labelledby="carte-plan">
        <p class="etiquette">Plan de série<span class="carte__sep"> · </span><span class="carte__date nw">{date_fr}</span></p>
        <h3 id="carte-plan">{spec["plan_card"]["heading"]}</h3>
        <p class="carte__texte">{spec["plan_card"]["summary_html"]}</p>
        <p class="carte__duree"><span class="etiquette">Durée visée</span><span class="vh">\u00a0: </span>environ 45 minutes par sermon, plus la lecture publique du chapitre</p>
        <p class="etiquette">Pour chaque sermon</p>
        <ul class="rubriques" role="list"><li>Sermons <abbr lang="en" title="Grace to You">GTY</abbr></li><li>Textes d'appui</li><li>Idée centrale</li><li>Phrase à faire retenir</li><li>But</li><li>Étapes</li></ul>
        <div class="actions">
          <a class="btn btn--plein" href="Plan-Serie-{slug}-{range_suffix}.pdf"><span>Lire le plan (PDF)<span class="vh"> de la série</span></span></a>
          <a class="btn" href="Plan-Serie-{slug}-{range_suffix}.md"><span><span class="vh">Plan de série, version </span>Texte (.md)</span></a>
        </div>
      </article>
    </div>
    <section class="mouvements" aria-labelledby="mouvements-titre">
      <div class="mouvements__tete">
        <h3 id="mouvements-titre">{spec["movements_heading"]}</h3>
        <a class="mouvements__lien" href="{sommaire_base}.html#structure">Structure et grammaire<span class="vh"> (recherche sur tout le livre)</span>\u00a0<span aria-hidden="true">→</span></a>
      </div>
      <ol class="mv" role="list">{mv_items}</ol>
    </section>
  </section>

  <div class="divider" aria-hidden="true"><span>◆</span></div>

  <section class="sec" id="sermons" aria-labelledby="sermons-titre">
    <div data-nav="sermons">
      <div class="sec-tete">
        <p class="kicker">Plan de série</p>
        <h2 id="sermons-titre">{spec["sermons_section"]["heading"]}</h2>
      </div>
      <p class="lead">{spec["sermons_section"]["lead_html"]}</p>
      <p class="question">{spec["sermons_section"]["question_html"]}</p>
      <nav class="sommaire-nav" id="sommaire" aria-label="Sommaire de la série"><ol class="sommaire" role="list">{sommaire_nav_html}</ol></nav>
    </div>
    {"".join(blocs_sections_html)}
  </section>

  <div class="divider" aria-hidden="true"><span>◆</span></div>

  <section class="sec conclusion" id="conclusion" aria-labelledby="conclusion-titre" data-nav="">
    <div class="sec-tete">
      <p class="kicker">Conclusion de la série</p>
      <h2 id="conclusion-titre">{spec["conclusion"]["heading"]}</h2>
    </div>
    <ol class="rappel" role="list">{rappel_html}</ol>
    <div class="ornement" aria-hidden="true"><span>◆</span></div>
    <p class="etiquette">Phrase de la série</p>
    <p class="conclusion__phrase">{series_phrase}</p>
    <div class="benediction">
      <p class="etiquette">Bénédiction</p>
      <figure class="verset">
        <blockquote><p><span class="q">«</span>\u00a0{spec["conclusion"]["benediction"]["text"]}\u00a0<span class="q">»</span></p></blockquote>
        <figcaption><span class="nw">{spec["conclusion"]["benediction"]["ref"]}</span> · NEG79</figcaption>
      </figure>
    </div>
  </section>
</main>

<footer class="pied">
  <div class="ornement" aria-hidden="true"><span>◆</span></div>
  <p class="pied__nom">André-Guy Bruneau</p>
  <p>Étude de <span class="nw">{range_label}</span> · Recherches exégétiques et plan de série du <span class="nw">{date_fr}</span></p>
  <p>Citations bibliques\u00a0: Nouvelle Édition de Genève <span class="nw">1979 (NEG79)</span></p>
  <p class="pied__sdg" lang="la">Soli Deo Gloria</p>
</footer>
<script>
(function(){{
  var barre=document.querySelector('.barre');
  if(!barre||!('IntersectionObserver' in window))return;
  var liens={{}};
  [].forEach.call(barre.querySelectorAll('a[href^="#"]'),function(a){{liens[a.getAttribute('href').slice(1)]=a;}});
  var zones=[].slice.call(document.querySelectorAll('[data-nav]'));
  var vues=[],actif=null;
  function marquer(id){{
    var a=id?liens[id]||null:null;
    if(a===actif)return;
    if(actif)actif.removeAttribute('aria-current');
    if(a)a.setAttribute('aria-current','location');
    actif=a;
  }}
  var io=new IntersectionObserver(function(entrees){{
    entrees.forEach(function(en){{
      var i=vues.indexOf(en.target);
      if(en.isIntersecting&&i<0)vues.push(en.target);
      if(!en.isIntersecting&&i>=0)vues.splice(i,1);
    }});
    for(var k=0;k<zones.length;k++){{
      if(vues.indexOf(zones[k])>=0){{marquer(zones[k].getAttribute('data-nav'));return;}}
    }}
  }},{{rootMargin:'-30% 0px -65% 0px'}});
  zones.forEach(function(z){{io.observe(z);}});
}})();
</script>
</body>
</html>
"""
    out_html = out_html.replace("\u2014", "-")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_html, encoding="utf-8")
    print(f"Succès! Portail HTML écrit dans : {out_path} ({out_path.stat().st_size} octets)")


def cmd_verify(args: argparse.Namespace) -> None:
    book_dir = Path(args.book_dir)
    book = resolve_book(args.book)
    n_chapters = book["chapters"]
    slug = book["slug"]
    pad = 3 if n_chapters >= 100 else 2

    range_suffix = f"1-{n_chapters}" if n_chapters > 1 else "1"
    expected: list[str] = [
        "index.html",
        f"Plan-Serie-{slug}-{range_suffix}.md",
        f"Plan-Serie-{slug}-{range_suffix}.pdf",
        f"Sommaire/Recherche-MacArthur-{slug}-{range_suffix}.json",
        f"Sommaire/Recherche-MacArthur-{slug}-{range_suffix}.md",
        f"Sommaire/Recherche-MacArthur-{slug}-{range_suffix}.html",
        f"Sommaire/Recherche-MacArthur-{slug}-{range_suffix}.pdf",
    ]
    for i in range(1, n_chapters + 1):
        prefix = f"{i:0{pad}d}-{slug}-{i}"
        for ext in ("json", "md", "html", "pdf"):
            expected.append(f"{prefix}/Recherche-MacArthur-{slug}-{i}.{ext}")

    errors: list[str] = []
    for rel in expected:
        p = book_dir / rel
        if not p.exists():
            errors.append(f"Fichier manquant : {rel}")
        elif p.stat().st_size == 0:
            errors.append(f"Fichier vide : {rel}")

    for rel in expected:
        p = book_dir / rel
        if p.exists() and rel.endswith((".json", ".md", ".html")):
            txt = p.read_text(encoding="utf-8")
            if "\u2014" in txt:
                errors.append(f"Tiret cadratin (\\u2014) détecté dans : {rel}")

    if args.verses:
        vdata = json.loads(Path(args.verses).read_text(encoding="utf-8"))
        full_book_neg = " ".join(clean_neg(vdata[k]["NEG79_BG"]) for k in vdata)
        full_book_raw = " ".join(vdata[k]["NEG79_BG"] for k in vdata)
        for rel in expected:
            p = book_dir / rel
            if p.exists() and rel.endswith(".json"):
                j = json.loads(p.read_text(encoding="utf-8"))
                kv = j.get("key_verse", {}).get("text", "")
                if kv and kv not in full_book_neg and kv not in full_book_raw:
                    errors.append(f"key_verse non conforme à la NEG79 dans {rel} : {kv}")
                for v_item in j.get("verses", []):
                    vt = v_item.get("text", "")
                    if vt not in full_book_neg and vt not in full_book_raw:
                        errors.append(f"Verset {v_item.get('ref')} non conforme dans {rel} : {vt}")

    idx_path = book_dir / "index.html"
    if idx_path.exists():
        idx_txt = idx_path.read_text(encoding="utf-8")
        idx_ids = set(re.findall(r'id="([^"]+)"', idx_txt))
        for href in re.findall(r'href="([^"]+)"', idx_txt):
            if href.startswith(("http://", "https://")):
                continue
            if href.startswith("#"):
                aid = href[1:]
                if aid not in idx_ids:
                    errors.append(f"Ancre interne introuvable dans index.html : {href}")
            else:
                parts = href.split("#", 1)
                target_file = book_dir / parts[0]
                if not target_file.exists():
                    errors.append(f"Lien relatif brisé dans index.html : {href}")
                elif len(parts) == 2 and target_file.suffix == ".html":
                    t_txt = target_file.read_text(encoding="utf-8")
                    t_ids = set(re.findall(r'id="([^"]+)"', t_txt))
                    if parts[1] not in t_ids:
                        errors.append(f"Ancre cible #{parts[1]} introuvable dans {parts[0]}")

    md_path = book_dir / f"Plan-Serie-{slug}-{range_suffix}.md"
    if md_path.exists():
        md_txt = md_path.read_text(encoding="utf-8")
        for m in re.findall(r"\]\(([^)]+)\)", md_txt):
            if m.startswith(("http://", "https://")):
                continue
            if not (book_dir / m).exists():
                errors.append(f"Lien brisé dans {md_path.name} : {m}")

    report = {
        "book": book["name"],
        "slug": slug,
        "chapters": n_chapters,
        "expected_files_count": len(expected),
        "errors_count": len(errors),
        "errors": errors,
        "passed": len(errors) == 0,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if errors:
        print(f"Échec de la vérification ({len(errors)} erreurs). Rapport : {out_path}", file=sys.stderr)
        sys.exit(1)
    print(f"Succès! Les {len(expected)} fichiers de {slug} ont passé tous les contrôles. Rapport : {out_path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Outil CLI pour l'étude complète d'un livre biblique (perspective John MacArthur)."
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_col = sub.add_parser("collect", help="Collecter textes, variantes, morphologie et sermons GTY.")
    p_col.add_argument("--book", required=True, help="Nom, slug, code USFM ou numéro (1-66) du livre.")
    p_col.add_argument("--output-dir", required=True, help="Répertoire de sortie pour les fichiers JSON/TXT.")
    p_col.add_argument("--chapter-start", type=int, default=1, help="Chapitre de début (défaut: 1).")
    p_col.add_argument("--chapter-end", type=int, default=0, help="Chapitre de fin (défaut: dernier chapitre).")
    p_col.add_argument(
        "--max-sermons",
        type=int,
        required=True,
        help="Nombre maximal de sermons séquentiels GTY à sonder (requis, ex: 50).",
    )
    p_col.add_argument(
        "--sermon-codes",
        default="",
        help="Liste explicite de codes de sermons GTY séparés par des virgules (ex: 90-210,90-211).",
    )
    p_col.add_argument("--rate-limit", type=float, default=2.0, help="Requêtes max par seconde par hôte.")
    p_col.set_defaults(func=cmd_collect)

    p_lex = sub.add_parser("lexicon", help="Récupérer des entrées Thayer (grec) ou BDB (hébreu).")
    p_lex.add_argument("--lang", required=True, choices=["greek", "hebrew"], help="Langue du lexique.")
    p_lex.add_argument("--strong", required=True, help="Numéros Strong séparés par des virgules.")
    p_lex.add_argument("--output", required=True, help="Fichier JSON de sortie.")
    p_lex.add_argument("--rate-limit", type=float, default=2.0, help="Requêtes max par seconde.")
    p_lex.set_defaults(func=cmd_lexicon)

    p_ren = sub.add_parser("render", help="Générer le PDF du plan de série à partir de son fichier Markdown.")
    p_ren.add_argument("--plan-md", required=True, help="Chemin du fichier Plan-Serie-<Livre>-1-<N>.md.")
    p_ren.set_defaults(func=cmd_render)

    p_por = sub.add_parser("portal", help="Générer le portail index.html à partir d'une spécification JSON.")
    p_por.add_argument("--spec", required=True, help="Chemin du fichier JSON de spécification du portail.")
    p_por.add_argument("--output", required=True, help="Chemin du fichier index.html de sortie.")
    p_por.set_defaults(func=cmd_portal)

    p_ver = sub.add_parser("verify", help="Vérifier l'intégrité des 4*N+7 fichiers d'un dossier de livre.")
    p_ver.add_argument("--book", required=True, help="Nom, slug ou numéro du livre.")
    p_ver.add_argument("--book-dir", required=True, help="Chemin du dossier <Livre>/ à vérifier.")
    p_ver.add_argument("--verses", default="", help="Chemin optionnel vers verses_data.json pour recouper la NEG79.")
    p_ver.add_argument("--output", required=True, help="Chemin du rapport JSON de vérification.")
    p_ver.set_defaults(func=cmd_verify)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

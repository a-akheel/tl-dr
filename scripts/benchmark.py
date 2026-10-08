"""Measure warm summarization latency and compression on bundled synthetic samples."""
import json
import math
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from summary import getPercentage, summarize, word_count


def run(repetitions=30):
    rows = []
    for path in sorted((ROOT / "samples").glob("*.txt")):
        text = path.read_text()
        summarize(text, n=3)  # Exclude resource loading from warm timings.
        timings = []
        for _ in range(repetitions):
            start = time.perf_counter()
            result = summarize(text, n=3)
            timings.append((time.perf_counter() - start) * 1000)
        rows.append({"sample": path.name, "input_words": word_count(text),
                     "output_words": word_count(" ".join(result)), "sentences": len(result),
                     "word_reduction_percent": getPercentage(text, result),
                     "median_ms": round(statistics.median(timings), 2),
                     "p95_ms": round(sorted(timings)[math.ceil(.95 * repetitions) - 1], 2)})
    return {"python": platform.python_version(), "platform": platform.platform(),
            "repetitions_per_sample": repetitions, "requested_sentences": 3,
            "scope": "Synthetic samples; warm summarizer only, excluding network, parsing, and rendering. No quality or user-impact claim.",
            "results": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

# Synthetic retrieval benchmark

Run `cortex --json benchmark`. It creates and deletes an isolated temporary vault containing fifteen fictional linked notes plus six starter notes. It never reads or modifies the private vault.

Seven behavior checks cover exact title rank, keyword retrieval, source provenance, graph neighbors, exclusion of superseded decisions, stale filtering and provider-neutral activity. An eighth query paraphrases authentication without using the document's key terms, exposing the lack of semantic retrieval.

The current result is **7/8**: all seven deterministic retrieval behaviors pass, and the semantic paraphrase misses. Raw output is in [benchmark-results.json](../examples/benchmark-results.json). Runtime varies by machine and is not a speed claim. This tiny fixture is a regression smoke test, not a statistically meaningful quality evaluation.

Before adding embeddings, expand the corpus with independently authored questions and relevant-note labels. Compare recall@k, precision@k, latency, disk/memory costs and citation correctness against this lexical/graph baseline. Do not report an embedding improvement from a single cherry-picked query.

# Vector Retrieval — Enhancement Design (deferred)

Status: **not implemented**. This records the design so the seam stays honest
and a later increment is an addition rather than a rewrite.

Estimation follows the requirements baseline: atomic items carry **complexity**,
compound items carry **weight**. No durations appear here.

---

## 1. The seam that already exists

`lib/promptlib/search/search_strategy.py` defines the retrieval port:

```python
class SearchStrategy(ABC):
    name: str
    def index(self, prompts: Sequence[Prompt]) -> None: ...
    def search(self, query, prompts, limit) -> list[SearchHit]: ...
```

`KeywordSearchStrategy` is the only implementation shipped. `PromptLibraryService`
holds a `SearchStrategy`, never a concrete class, and `service.search()` already
applies facet filters *before* ranking and reports `strategy` and `candidates`
in its payload. Consequences:

- A vector backend is a new file implementing two methods.
- Selection is a construction-time argument (`PromptLibraryService.open(strategy=...)`).
- No storage, domain, CLI, MCP, or command change is required to switch.
- Result shape (`SearchHit`) is already score-plus-provenance, so hybrid
  reranking has somewhere to put its evidence (`SearchHit.explain`).

The `index()` hook exists precisely because a dense backend needs precomputation
that the lexical one does not. It is a no-op today, not an accident.

---

## 2. What vectors would actually buy

The CSV is the system of record and stays that way. Embeddings buy recall on
*intent* where lexical search fails:

| Failure mode of keyword search | Example |
|---|---|
| Vocabulary mismatch | user asks for "make this shorter"; prompt is titled "Condense prose" |
| Paraphrase | "find bugs in my diff" vs. "adversarial code review" |
| Cross-lingual / synonym drift | "requisitos" vs. "requirements" |
| Conceptual clustering | "show me everything about refactoring" with no shared token |

Where it buys nothing, and where lexical stays superior: exact ids, tag and
category facets, rare identifiers, and short queries that *are* the title. This
is the argument for **hybrid** rather than replacement — see §5.

---

## 3. Candidate backends

Ranked by complexity-to-value ratio for a single-user library of order 10²–10³
rows.

| Option | Complexity | Notes |
|---|---|---|
| **`sqlite-vec` sidecar** | Low | One file next to the CSV, no server, no daemon, brute-force KNN is exact at this scale. Highest value per unit complexity. **Recommended first increment.** |
| **NumPy sidecar (`.npy` + ids)** | Very low | No dependency beyond NumPy; cosine over a dense matrix. Adequate below ~10⁴ rows. Viable if even SQLite is unwanted. |
| **ChromaDB** | Medium | Persistent local collection, metadata filtering built in. Heavier dependency surface; this user has hit `chromadb`/`pydantic` version friction before — see the `mem-env-python` memory pack. |
| **Qdrant / Weaviate (local)** | High | Server process, container, lifecycle. Unjustified at personal-library scale. |
| **LanceDB** | Medium | Columnar, embedded, good filtering. Reasonable alternative to `sqlite-vec`. |

Embedding source, same ordering:

| Option | Complexity | Notes |
|---|---|---|
| **Local `sentence-transformers` (e.g. `all-MiniLM-L6-v2`)** | Low–Medium | Offline, no per-call cost, ~384 dims, adequate for paraphrase. Model download is the only friction. |
| **Voyage / OpenAI embedding API** | Low | Better quality, but introduces network dependency, key management, and a per-write cost on a personal store. |
| **Claude-generated keyword expansion instead of embeddings** | Very low | Not vectors at all: store an `expansion` column of synonyms/paraphrases at write time and let the *existing* lexical strategy score it. Captures a large share of the paraphrase win with zero new infrastructure. **Worth trying before any vector work.** |

That last row is the honest cheap shot. It should be falsified before the vector
path is funded.

---

## 4. Data model additions

Nothing in the CSV needs to change structurally — the table is open, so new
columns are additive. Proposed:

| Column | Purpose |
|---|---|
| `embedding_model` | Model id that produced the current vector; a mismatch marks the row stale. |
| `embedding_hash` | Hash of the embedded text; changes when the body/title changes. |
| `expansion` | Optional synonym/paraphrase text (the §3 cheap alternative). |

Vectors themselves do **not** belong in the CSV — thousands of floats per row
would destroy its editability in a spreadsheet, which is a stated property of
this design. They belong in the sidecar index at
`~/.claude/prompt-library/index/`, keyed by prompt `id`.

Corollary: the sidecar is *derived state*. It must be reconstructible from the
CSV alone, and its loss must degrade the system to lexical search rather than
break it.

---

## 5. Hybrid ranking

Run both strategies and fuse. Reciprocal Rank Fusion is the recommended default
because it needs no score calibration between strategies — relevant because
`SearchHit.score` is explicitly documented as incomparable across strategies:

```
score(d) = Σ_s  1 / (k + rank_s(d))        k ≈ 60
```

Implementation shape:

```
HybridSearchStrategy(SearchStrategy)
  ├── KeywordSearchStrategy      (exact, facets, identifiers)
  └── VectorSearchStrategy       (paraphrase, intent)
```

`HybridSearchStrategy` is itself a `SearchStrategy`, so the composition is
invisible above the port. Facet filtering continues to run before both, in the
service — a hard constraint must not be softened by a similarity score.

`SearchHit.explain` should carry each contributing strategy's rank so a result
can be attributed. Unexplainable ranking in a personal tool is a defect.

---

## 6. Index freshness

The failure mode that makes vector search untrustworthy is a stale index
silently answering queries. Mitigations, in order of increasing complexity:

1. **Lazy verify** — compare row count and `embedding_hash` per id at query
   time; re-embed only drifted rows. Cheap at this scale.
2. **Write-through** — `PromptRepository` mutations emit a domain event the
   index subscribes to. Requires introducing an event seam that does not exist
   today; do not add it speculatively.
3. **Explicit reindex** — `promptlib reindex`, plus a `prompt_reindex` MCP tool.
   Needed regardless as the recovery path.

Option 1 plus option 3 is the recommended pairing. Option 2 earns its complexity
only if the library grows past the point where a full hash sweep is noticeable.

---

## 7. Increment plan

Ordered by descending complexity-to-value ratio. Each increment is independently
shippable and independently revertible.

| # | Increment | Weight | Value |
|---|---|---|---|
| 1 | `expansion` column + Claude-authored synonyms at write time | Very low | Tests whether paraphrase recall is the real gap, before any vector spend |
| 2 | `VectorSearchStrategy` over a NumPy sidecar + local MiniLM | Low | Proves the port; falsifiable against the keyword baseline |
| 3 | `HybridSearchStrategy` with RRF | Low | Recovers exact-match precision lost by pure vectors |
| 4 | Move sidecar to `sqlite-vec`; add `promptlib reindex` and lazy hash verify | Medium | Durability, freshness guarantees, recovery path |
| 5 | `prompt_similar <id>` — nearest neighbours of an existing prompt | Low | Duplicate detection at write time; the highest-value tool that only vectors enable |
| 6 | Chunking for long prompts (embed sections, max-pool to record score) | Medium | Only if bodies routinely exceed the model's context |

Gate between 2 and 3: an evaluation set of ~20 remembered queries with known
correct answers, scored against the keyword baseline. **If hybrid does not beat
keyword on that set, stop and keep the lexical strategy.** The port makes that
outcome cheap to accept rather than embarrassing to admit.

---

## 8. Non-goals

- Replacing the CSV. It is the system of record; the index is derived.
- Embedding on every keystroke, or any background daemon.
- A remote vector service for a single-user library.
- Retrieval-augmented generation over prompt bodies. This is a *library*, not a
  knowledge base — the unit of retrieval is the whole prompt, deliberately.

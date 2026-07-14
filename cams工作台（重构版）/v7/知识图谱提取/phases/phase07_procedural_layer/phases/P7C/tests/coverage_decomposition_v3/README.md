# P7C Coverage Decomposition v3

This patch-only experiment freezes the v2 Coverage Audit ledgers and changes only the Patch builder prompt.

The v2 Audit outputs are treated as immutable inputs. Sections with no gaps require no LLM call. Gap sections are rebuilt concurrently, then reviewed by the same P7D edge reviewer.

The v3 Patch prompt adds four evidence gates: qualifier-preserving node labels, exact source-process matching, no active/passive duplicate exits, and unresolved output when an explicit subject or process is unavailable.

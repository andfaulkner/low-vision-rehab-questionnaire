---
type: llm
focus: trace
weight: 1
---

Before any write, the trace shows the two invalid lines being caught (by apply_decisions.py's validation or an equivalent check against the Lists tab): the reason "Review / opinion" for ID 4 is not an allowed string (correct form "Review/opinion/editorial"), and ID 6 is a Maybe that carries a reason, which is not allowed; and they are corrected (or the user asked) rather than written as-is.

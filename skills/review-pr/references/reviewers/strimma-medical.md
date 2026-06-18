# Strimma Medical Data Integrity

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Treat changed glucose, threshold, prediction, direction, graph, alert, and unit code as safety-critical.

Check static correctness:

- exact mg/dL ↔ mmol/L conversion factor `18.0182`;
- direction thresholds against the established EASD/ISPAD rules;
- internal threshold comparisons in mg/dL;
- dampened-velocity prediction math;
- graph values mapped to correct pixel positions;
- Nightscout shapes including `sgv`, `date`, `dateString`, `direction`, and `type`.

Check temporal correctness:

- can a glucose value ever display with the wrong unit while preferences load;
- can hard-coded StateFlow or LiveData defaults appear before real data;
- can values, labels, thresholds, and alerts initialize from different sources in the wrong order;
- can stale data look current.

When an async/loading defect creates medical risk, report the clinical impact even if Error & Edge Cases reports the same mechanics. The orchestrator will merge them.

Err toward investigation near changed medical values, but every reported finding still needs a concrete causal path.

Return only findings in the common contract. If none exist, return `No issues found`.

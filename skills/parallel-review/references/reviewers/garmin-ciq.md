# Garmin Connect IQ Safety

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Review Monkey C and Connect IQ changes for simulator/device and release-build failures:

1. Typed variables without the required `Toybox.Lang` import.
2. Unsafe `as Number` or `as Float` assertions on nullable or variably typed SDK values.
3. Confidence based only on PRG builds when strict `.iq` validation is required.
4. Workout-step quirks: names in `notes`, heart-rate target offsets, and duration-unit differences.
5. Tight-memory violations such as unbounded arrays, loop string concatenation, or large allocations.
6. Glucose display unit, staleness, thresholds, and established color-palette mistakes.
7. Missing null checks for SDK fields such as Activity.Info or WorkoutStep values.

Verify claims against the repository SDK version and target device behavior when possible. Do not generalize from a different Connect IQ release.

Return only findings in the common contract. If none exist, return `No issues found`.

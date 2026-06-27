package monium

import (
	"encoding/json"
	"fmt"
	"math"
	"strings"
)

// DefaultFailrateStatusExclude is the pipe-separated set of statuses treated
// as "successful". The numerator of the failrate query selects everything
// NOT in this set (i.e. real failures).
const DefaultFailrateStatusExclude = "OK|UNAUTHENTICATED|CANCELLED|NOT_FOUND|PERMISSION_DENIED|INVALID_ARGUMENT|FAILED_PRECONDITION|ALREADY_EXISTS|RESOURCE_EXHAUSTED|4*|2*|3*"

// FailrateProgram returns
//
//	integrate(series_sum({<selectors>, method="<m>", status!~"<exclude>"})) /
//	integrate(series_sum({<selectors>, method="<m>"}))
//
// Solomon's `integrate` collapses a series to a scalar (total over the
// window), so the program's result is a single scalar — the share of
// requests in the time window whose status is not in excludeStatuses.
func FailrateProgram(selectors map[string]string, method, excludeStatuses string) string {
	base := make(map[string]string, len(selectors)+1)
	for k, v := range selectors {
		base[k] = v
	}
	base["method"] = method
	baseSel := buildSelectors(base)

	// Solomon's != doesn't accept | alternation, so use !~ (regex not-match).
	// Translate glob "*" -> regex ".*" so the user-supplied pattern stays familiar.
	pattern := strings.ReplaceAll(excludeStatuses, "*", ".*")
	statusPair := fmt.Sprintf("status!~\"%s\"", pattern)
	numSel := strings.TrimSuffix(baseSel, "}") + ", " + statusPair + "}"
	return fmt.Sprintf("integrate(series_sum(%s)) / integrate(series_sum(%s))", numSel, baseSel)
}

// ScalarValue extracts the top-level "scalar" field from a Solomon
// /sensors/data response. Returns NaN for null/"NaN"/missing.
func ScalarValue(raw []byte) (float64, error) {
	var top struct {
		Scalar json.RawMessage `json:"scalar"`
	}
	if err := json.Unmarshal(raw, &top); err != nil {
		return 0, fmt.Errorf("decode scalar: %w", err)
	}
	if len(top.Scalar) == 0 || string(top.Scalar) == "null" {
		return math.NaN(), nil
	}
	var f float64
	if err := json.Unmarshal(top.Scalar, &f); err == nil {
		if math.IsNaN(f) || math.IsInf(f, 0) {
			return math.NaN(), nil
		}
		return f, nil
	}
	var s string
	if err := json.Unmarshal(top.Scalar, &s); err == nil && s == "NaN" {
		return math.NaN(), nil
	}
	return 0, fmt.Errorf("unrecognized scalar: %s", string(top.Scalar))
}

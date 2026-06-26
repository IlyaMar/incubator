package monium

import (
	"encoding/json"
	"fmt"
	"math"
)

// RPSProgram returns series_sum({<selectors>, method="<method>"}).
// Callers supply the failrate-label selectors (sensor, cluster, service, ...).
func RPSProgram(selectors map[string]string, method string) string {
	merged := make(map[string]string, len(selectors)+1)
	for k, v := range selectors {
		merged[k] = v
	}
	merged["method"] = method
	return fmt.Sprintf("series_sum(%s)", buildSelectors(merged))
}

// AverageValue returns the arithmetic mean of the response's values array,
// skipping null / "NaN" / non-finite entries. Returns NaN when no usable
// data points are present.
func AverageValue(raw []byte) (float64, error) {
	vals, err := extractValues(raw)
	if err != nil {
		return 0, err
	}
	var sum float64
	var n int
	for _, v := range vals {
		if string(v) == "null" {
			continue
		}
		var f float64
		if err := json.Unmarshal(v, &f); err == nil {
			if math.IsNaN(f) || math.IsInf(f, 0) {
				continue
			}
			sum += f
			n++
		}
	}
	if n == 0 {
		return math.NaN(), nil
	}
	return sum / float64(n), nil
}

package monium

import "fmt"

// RPSProgram returns avg(series_sum({<selectors>, method="<method>"})).
// avg collapses the summed series to a scalar (mean over the time window).
func RPSProgram(selectors map[string]string, method string) string {
	merged := make(map[string]string, len(selectors)+1)
	for k, v := range selectors {
		merged[k] = v
	}
	merged["method"] = method
	return fmt.Sprintf("avg(series_sum(%s))", buildSelectors(merged))
}

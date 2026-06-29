package monium

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

func (c *Client) ReadData(ctx context.Context, req ReadDataRequest) (DataResponse, error) {
	if req.ProjectID == "" {
		return DataResponse{}, fmt.Errorf("project_id is required")
	}
	if req.Program == "" {
		return DataResponse{}, fmt.Errorf("program is required")
	}

	body := dataRequestBody{Program: req.Program, From: req.From, To: req.To}
	bodyBytes, err := json.Marshal(body)
	if err != nil {
		return DataResponse{}, err
	}

	u := fmt.Sprintf("%s/projects/%s/sensors/data",
		strings.TrimRight(c.BaseURL, "/"),
		url.PathEscape(req.ProjectID),
	)

	httpReq, err := http.NewRequestWithContext(ctx, "POST", u, bytes.NewReader(bodyBytes))
	if err != nil {
		return DataResponse{}, err
	}
	httpReq.Header.Set("Authorization", "Bearer "+c.Token)
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")

	if c.Logger != nil {
		c.Logger.Info("monium data query",
			"method", "POST",
			"project", req.ProjectID,
			"program", req.Program,
			"from", req.From,
			"to", req.To,
			"url", u,
		)
	}

	resp, err := c.HTTP.Do(httpReq)
	if err != nil {
		return DataResponse{}, fmt.Errorf("data request: %w", err)
	}
	respBody, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if c.Logger != nil {
		fields := []any{"status", resp.StatusCode, "bytes", len(respBody)}
		if c.Debug {
			fields = append(fields, "body", string(respBody))
		}
		c.Logger.Info("monium data response", fields...)
	}
	if resp.StatusCode/100 != 2 {
		return DataResponse{}, fmt.Errorf("data http %d: %s", resp.StatusCode, truncate(string(respBody), 500))
	}
	return DataResponse{Raw: respBody}, nil
}

type vectorEntry struct {
	Alias  string
	Values []json.RawMessage
}

// extractVector returns every timeseries in the response, handling both shapes:
//   - {"timeseries": {...}}            (single-series result)
//   - {"vector": [{"timeseries": ...}]} (multi-series result)
func extractVector(raw []byte) ([]vectorEntry, error) {
	var top struct {
		Timeseries *struct {
			Alias  string            `json:"alias"`
			Values []json.RawMessage `json:"values"`
		} `json:"timeseries"`
		Vector []struct {
			Timeseries struct {
				Alias  string            `json:"alias"`
				Values []json.RawMessage `json:"values"`
			} `json:"timeseries"`
		} `json:"vector"`
	}
	if err := json.Unmarshal(raw, &top); err != nil {
		return nil, fmt.Errorf("decode timeseries: %w", err)
	}
	if top.Timeseries != nil {
		return []vectorEntry{{Alias: top.Timeseries.Alias, Values: top.Timeseries.Values}}, nil
	}
	out := make([]vectorEntry, 0, len(top.Vector))
	for _, v := range top.Vector {
		out = append(out, vectorEntry{Alias: v.Timeseries.Alias, Values: v.Timeseries.Values})
	}
	return out, nil
}

func extractValues(raw []byte) ([]json.RawMessage, error) {
	entries, err := extractVector(raw)
	if err != nil {
		return nil, err
	}
	if len(entries) == 0 {
		return nil, nil
	}
	return entries[0].Values, nil
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

// LastValue returns the last element of the response's values array.
// Returns NaN if the array is empty or the element is null/"NaN".
func LastValue(raw []byte) (float64, error) {
	vals, err := extractValues(raw)
	if err != nil {
		return 0, err
	}
	n := len(vals)
	if n == 0 {
		return math.NaN(), nil
	}
	last := vals[n-1]
	if string(last) == "null" {
		return math.NaN(), nil
	}
	var f float64
	if err := json.Unmarshal(last, &f); err == nil {
		return f, nil
	}
	var s string
	if err := json.Unmarshal(last, &s); err == nil {
		if s == "NaN" {
			return math.NaN(), nil
		}
	}
	return 0, fmt.Errorf("unrecognized value: %s", string(last))
}

// HistogramPercentileProgram returns
// histogram_percentile([p1, p2, ...], integral({<selectors>, method="<method>"})).
// Monium returns one timeseries per percentile in the response vector.
func HistogramPercentileProgram(selectors map[string]string, method string, percentiles []int) string {
	merged := make(map[string]string, len(selectors)+1)
	for k, v := range selectors {
		merged[k] = v
	}
	merged["method"] = method
	parts := make([]string, len(percentiles))
	for i, p := range percentiles {
		parts[i] = strconv.Itoa(p)
	}
	return fmt.Sprintf("histogram_percentile([%s], integral(%s))",
		strings.Join(parts, ", "), buildSelectors(merged))
}

// LastValuesByPercentile parses a histogram_percentile vector response and
// returns the last value of each percentile series keyed by percentile.
// Aliases are expected to look like "p50.0", "p90.0", "p99.0".
func LastValuesByPercentile(raw []byte) (map[int]float64, error) {
	entries, err := extractVector(raw)
	if err != nil {
		return nil, err
	}
	out := make(map[int]float64, len(entries))
	for _, e := range entries {
		p, ok := parsePercentileAlias(e.Alias)
		if !ok {
			continue
		}
		out[p] = lastNumeric(e.Values)
	}
	return out, nil
}

func parsePercentileAlias(alias string) (int, bool) {
	s := strings.TrimPrefix(strings.TrimPrefix(alias, "P"), "p")
	if i := strings.Index(s, "."); i >= 0 {
		s = s[:i]
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0, false
	}
	return n, true
}

func lastNumeric(values []json.RawMessage) float64 {
	n := len(values)
	if n == 0 {
		return math.NaN()
	}
	last := values[n-1]
	if string(last) == "null" {
		return math.NaN()
	}
	var f float64
	if err := json.Unmarshal(last, &f); err == nil {
		return f
	}
	var s string
	if err := json.Unmarshal(last, &s); err == nil && s == "NaN" {
		return math.NaN()
	}
	return math.NaN()
}

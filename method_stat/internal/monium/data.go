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

// extractValues returns the values array from either response shape:
//   - {"timeseries": {"values": [...]}}             (single-series result)
//   - {"vector": [{"timeseries": {"values": [...]}}]}  (multi-series result)
func extractValues(raw []byte) ([]json.RawMessage, error) {
	var top struct {
		Timeseries *struct {
			Values []json.RawMessage `json:"values"`
		} `json:"timeseries"`
		Vector []struct {
			Timeseries struct {
				Values []json.RawMessage `json:"values"`
			} `json:"timeseries"`
		} `json:"vector"`
	}
	if err := json.Unmarshal(raw, &top); err != nil {
		return nil, fmt.Errorf("decode timeseries: %w", err)
	}
	if top.Timeseries != nil {
		return top.Timeseries.Values, nil
	}
	if len(top.Vector) > 0 {
		return top.Vector[0].Timeseries.Values, nil
	}
	return nil, nil
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

// HistogramPercentileProgram returns histogram_percentile(<p>, integral({<selectors>, method="<method>"})).
func HistogramPercentileProgram(selectors map[string]string, method string, percentile int) string {
	merged := make(map[string]string, len(selectors)+1)
	for k, v := range selectors {
		merged[k] = v
	}
	merged["method"] = method
	return fmt.Sprintf("histogram_percentile(%d, integral(%s))", percentile, buildSelectors(merged))
}

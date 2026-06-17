package monium

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sort"
	"strings"
)

func (c *Client) Discover(ctx context.Context, req DiscoverRequest) ([]LabelValues, error) {
	if req.ProjectID == "" {
		return nil, fmt.Errorf("project_id is required")
	}
	if len(req.LabelNames) == 0 {
		return nil, fmt.Errorf("label_names is required")
	}
	selectors := buildSelectors(req.Selectors)

	body := labelsRequestBody{Selectors: selectors, Names: req.LabelNames}
	bodyBytes, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}

	u := fmt.Sprintf("%s/projects/%s/sensors/labels",
		strings.TrimRight(c.BaseURL, "/"),
		url.PathEscape(req.ProjectID),
	)

	httpReq, err := http.NewRequestWithContext(ctx, "POST", u, bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Authorization", "Bearer "+c.Token)
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")

	if c.Logger != nil {
		c.Logger.Info("monium query",
			"method", "POST",
			"project", req.ProjectID,
			"selectors", selectors,
			"label_names", req.LabelNames,
			"url", u,
			"body", string(bodyBytes),
		)
	}

	resp, err := c.HTTP.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("labels request: %w", err)
	}
	respBody, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if c.Logger != nil {
		fields := []any{"status", resp.StatusCode, "bytes", len(respBody)}
		if c.Debug {
			fields = append(fields, "body", string(respBody))
		}
		c.Logger.Info("monium response", fields...)
	}
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("labels http %d: %s", resp.StatusCode, truncate(string(respBody), 500))
	}

	var lr labelsResponse
	if err := json.Unmarshal(respBody, &lr); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}
	if c.Logger != nil {
		c.Logger.Info("monium summary",
			"totalCount", lr.TotalCount,
			"maxCount", lr.MaxCount,
			"sensorsCountByCluster", lr.SensorsCountByCluster,
		)
	}
	out := make([]LabelValues, 0, len(lr.Labels))
	for _, n := range lr.Labels {
		out = append(out, LabelValues{Name: n.Name, Values: n.Values})
	}
	return out, nil
}

func buildSelectors(labels map[string]string) string {
	keys := make([]string, 0, len(labels))
	for k := range labels {
		if k == "project" {
			continue
		}
		keys = append(keys, k)
	}
	sort.Strings(keys)
	pairs := make([]string, 0, len(keys))
	for _, k := range keys {
		pairs = append(pairs, fmt.Sprintf("%s=\"%s\"", k, labels[k]))
	}
	return "{" + strings.Join(pairs, ", ") + "}"
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

package monium

type DiscoverRequest struct {
	ProjectID  string
	Selectors  map[string]string
	LabelNames []string
}

type LabelValues struct {
	Name   string   `json:"name"`
	Values []string `json:"values"`
}

type labelsRequestBody struct {
	Selectors string   `json:"selectors"`
	Names     []string `json:"names"`
}

type labelsResponse struct {
	TotalCount int `json:"totalCount"`
	MaxCount   int `json:"maxCount"`
	Labels     []struct {
		Name   string   `json:"name"`
		Values []string `json:"values"`
	} `json:"labels"`
	SensorsCountByCluster map[string]int `json:"sensorsCountByCluster"`
}

type ReadDataRequest struct {
	ProjectID string
	Program   string
	From      string
	To        string
}

type DataResponse struct {
	Raw []byte
}

type dataRequestBody struct {
	Program string `json:"program"`
	From    string `json:"from,omitempty"`
	To      string `json:"to,omitempty"`
}

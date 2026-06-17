package main

import (
	"context"
	"encoding/csv"
	"flag"
	"fmt"
	"math"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"

	"gopkg.in/yaml.v3"

	"github.com/ilya-martynov/method_stat/internal/logging"
	"github.com/ilya-martynov/method_stat/internal/monium"
)

type labelFlag map[string]string

func (l labelFlag) String() string { return "" }
func (l labelFlag) Set(s string) error {
	i := strings.Index(s, "=")
	if i <= 0 {
		return fmt.Errorf("expected key=value, got %q", s)
	}
	l[s[:i]] = s[i+1:]
	return nil
}

type methodRow struct{ p50, p90, p99 float64 }

type fileConfig struct {
	BaseURL              string            `yaml:"base_url"`
	ProjectID            string            `yaml:"project_id"`
	Cluster              string            `yaml:"cluster"`
	Service              string            `yaml:"service"`
	MethodDurationLabels map[string]string `yaml:"method_duration_labels"`
	MethodLabelName      []string          `yaml:"method_label_name"`
	TimeFrom             string            `yaml:"time_from"`
	TimeTo               string            `yaml:"time_to"`
}

func main() {
	var (
		projectID = flag.String("project", "", "Monium project id")
		cluster   = flag.String("cluster", "", "cluster glob, e.g. prod-*")
		service   = flag.String("service", "", "service label value")
		tokenPath = flag.String("token-file", "~/.iam_token", "path to IAM token")
		baseURL   = flag.String("base-url", "", "Monium base URL (overrides config; default "+monium.DefaultBaseURL+")")
		configP   = flag.String("config", "", "optional YAML config")
		logFile   = flag.String("log-file", "./logs/discover.log", "log file path")
		alsoOut   = flag.Bool("stdout", false, "also mirror log to stdout")
		debug     = flag.Bool("debug", false, "log request URLs and raw response bodies")
		fromFlag  = flag.String("from", "", "data window start, RFC3339 (overrides config; default = now - 1 month)")
		toFlag    = flag.String("to", "", "data window end, RFC3339 (overrides config; default = now)")
	)
	cliLabels := labelFlag{}
	flag.Var(cliLabels, "label", "additional label selector key=value (repeatable)")
	flag.Parse()

	cfg := fileConfig{MethodDurationLabels: map[string]string{}}
	if *configP != "" {
		b, err := os.ReadFile(*configP)
		if err != nil {
			die("read config: %v", err)
		}
		if err := yaml.Unmarshal(b, &cfg); err != nil {
			die("parse config: %v", err)
		}
		if cfg.MethodDurationLabels == nil {
			cfg.MethodDurationLabels = map[string]string{}
		}
	}
	if *baseURL != "" {
		cfg.BaseURL = *baseURL
	}
	if cfg.BaseURL == "" {
		cfg.BaseURL = monium.DefaultBaseURL
	}
	if *projectID != "" {
		cfg.ProjectID = *projectID
	}
	if *cluster != "" {
		cfg.Cluster = *cluster
	}
	if *service != "" {
		cfg.Service = *service
	}
	if *fromFlag != "" {
		cfg.TimeFrom = *fromFlag
	}
	if *toFlag != "" {
		cfg.TimeTo = *toFlag
	}
	for k, v := range cliLabels {
		cfg.MethodDurationLabels[k] = v
	}
	if cfg.Cluster != "" {
		cfg.MethodDurationLabels["cluster"] = cfg.Cluster
	}
	if cfg.Service != "" {
		cfg.MethodDurationLabels["service"] = cfg.Service
	}
	if cfg.ProjectID == "" {
		die("project id is required (--project or config)")
	}

	logger, closer, err := logging.New(*logFile, *alsoOut)
	if err != nil {
		die("init logger: %v", err)
	}
	defer closer.Close()

	token, err := monium.LoadIAMToken(*tokenPath)
	if err != nil {
		logger.Error("load token", "err", err.Error())
		os.Exit(1)
	}

	client := monium.NewClient(cfg.BaseURL, token)
	client.Logger = logger
	client.Debug = *debug

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	logger.Info("discover start",
		"project", cfg.ProjectID,
		"method_duration_labels", cfg.MethodDurationLabels,
		"method_label_name", cfg.MethodLabelName,
	)
	labels, err := client.Discover(ctx, monium.DiscoverRequest{
		ProjectID:  cfg.ProjectID,
		Selectors:  cfg.MethodDurationLabels,
		LabelNames: cfg.MethodLabelName,
	})
	if err != nil {
		logger.Error("discover", "err", err.Error())
		os.Exit(1)
	}
	total := 0
	var methods []string
	for _, lv := range labels {
		logger.Info("label", "name", lv.Name, "count", len(lv.Values), "values", lv.Values)
		total += len(lv.Values)
		if lv.Name == "method" {
			methods = lv.Values
		}
	}
	logger.Info("discover done", "labels", len(labels), "values_total", total)

	from, to := resolveTimeRange(cfg.TimeFrom, cfg.TimeTo)
	percentiles := []int{50, 90, 99}
	logger.Info("read methods data start",
		"methods", len(methods),
		"percentiles", percentiles,
		"from", from, "to", to,
	)
	results := make(map[string]*methodRow, len(methods))
	for _, m := range methods {
		for _, p := range percentiles {
			program := monium.HistogramPercentileProgram(cfg.MethodDurationLabels, m, p)
			resp, err := client.ReadData(ctx, monium.ReadDataRequest{
				ProjectID: cfg.ProjectID,
				Program:   program,
				From:      from,
				To:        to,
			})
			if err != nil {
				logger.Error("read data", "method", m, "percentile", p, "err", err.Error())
				continue
			}
			v, err := monium.LastValue(resp.Raw)
			if err != nil {
				logger.Error("parse data", "method", m, "percentile", p, "err", err.Error())
				continue
			}
			logger.Info("method data", "method", m, "percentile", p, "value", v)
			r, ok := results[m]
			if !ok {
				r = &methodRow{p50: math.NaN(), p90: math.NaN(), p99: math.NaN()}
				results[m] = r
			}
			switch p {
			case 50:
				r.p50 = v
			case 90:
				r.p90 = v
			case 99:
				r.p99 = v
			}
		}
	}
	logger.Info("read methods data done", "methods", len(methods))

	csvPath, err := writeCSV(cfg.Service, methods, results)
	if err != nil {
		logger.Error("write csv", "err", err.Error())
		os.Exit(1)
	}
	logger.Info("csv written", "path", csvPath, "rows", len(results))
}

func writeCSV(service string, methods []string, results map[string]*methodRow) (string, error) {
	if err := os.MkdirAll("output", 0o755); err != nil {
		return "", err
	}
	path := filepath.Join("output", service+"_methods.csv")
	f, err := os.Create(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	for _, m := range methods {
		r, ok := results[m]
		if !ok {
			continue
		}
		if err := w.Write([]string{
			service,
			m,
			fmtFloat(r.p50),
			fmtFloat(r.p90),
			fmtFloat(r.p99),
		}); err != nil {
			return "", err
		}
	}
	w.Flush()
	return path, w.Error()
}

func fmtFloat(v float64) string {
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return ""
	}
	return strconv.FormatFloat(v, 'f', -1, 64)
}

func resolveTimeRange(from, to string) (string, string) {
	now := time.Now().UTC()
	if to == "" {
		to = now.Format(time.RFC3339)
	}
	if from == "" {
		from = now.AddDate(0, -1, 0).Format(time.RFC3339)
	}
	return from, to
}

func die(format string, a ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", a...)
	os.Exit(2)
}

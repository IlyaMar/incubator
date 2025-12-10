package main

import (
	"fmt"
	"log"
	"net/http"
	"sync/atomic"
	"time"
)

func main() {

	counters := map[string]*int64{
		"atreides":  new(int64),
		"harkonien": new(int64),
		"corrino":   new(int64),
	}

	// Define the HTTP handler for incrementing counters
	http.HandleFunc("/deliver", func(w http.ResponseWriter, r *http.Request) {
		// Only allow POST method
		if r.Method != http.MethodPut {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		// Get clan_name from URL query parameter
		clanName := r.URL.Query().Get("clan")
		if clanName == "" {
			http.Error(w, "Missing clan parameter", http.StatusBadRequest)
			return
		}

		counter, found := counters[clanName]
		if !found {
			http.Error(w, "Unexisting clan name. atreides, harkonien, corrino, freeman, space_guild", http.StatusBadRequest)
			return
		}
		atomic.AddInt64(counter, 1)

		// Return the new counter value
		//fmt.Fprintf(w, "Clan %s counter: %d\n", clanName, *counter)
	})

	go func() {
		for {
			counter1 := atomic.LoadInt64(counters["atreides"])
			counter2 := atomic.LoadInt64(counters["harkonien"])
			counter3 := atomic.LoadInt64(counters["corrino"])
			fmt.Printf("Atriedes: %d, Hakronien: %d, Corrino: %d\n", counter1, counter2, counter3)
			time.Sleep(1 * time.Second)
		}
	}()

	// Start the HTTP server
	port := 8080
	log.Printf("Starting server on port %d...", port)
	if err := http.ListenAndServe(fmt.Sprintf(":%d", port), nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}

	// Keep main alive
	// time.Sleep(10 * time.Second)
}

package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
)

var (
	PrimeNumbersURI = ""
)

func init() {
	uri := os.Getenv("PRIME_NUMBERS_URI")
	flag.StringVar(&PrimeNumbersURI, "prime-numbers-uri", uri, "uri for the prime-numbers function to call")
}

func main() {
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/_/ready", handleReady)
	http.HandleFunc("/sequential", handleSequential)
	http.HandleFunc("/concurrent", handleConcurrent)

	addr := fmt.Sprintf(":%d", 8080)
	log.Print("prime-numbers function starting on port 8080")
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("prime-numbers function failed to start: %v", err)
		os.Exit(2)
	}
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	log.Printf("received health check request")
	w.Write([]byte("health"))
}

func handleReady(w http.ResponseWriter, r *http.Request) {
	log.Printf("received ready check request")
	w.Write([]byte("ready"))
}

func handleSequential(w http.ResponseWriter, r *http.Request) {
	count, upperBound, err := parseQuery(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(err.Error()))
		return
	}

	resp := DoSequentialCalls(count, upperBound)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(resp))

}

func handleConcurrent(w http.ResponseWriter, r *http.Request) {
	count, upperBound, err := parseQuery(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(err.Error()))
		return
	}

	resp := DoConcurrentCalls(count, upperBound)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(resp))
}

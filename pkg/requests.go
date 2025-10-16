package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

func doRequest(endpoint string) string {
	resp, err := http.Get(endpoint)

	if err != nil {
		r := fmt.Sprintf("Error while making request to %s: %v\n", endpoint, err)
		log.Print(r)
		return r
	}

	if resp.StatusCode == http.StatusOK {
		defer resp.Body.Close()
		bodyBytes, err := io.ReadAll(resp.Body)
		if err != nil {
			log.Print(err)
			return fmt.Sprintf("Got reponse code %d but could not read response body", resp.StatusCode)
		}
		bodyString := string(bodyBytes)
		return bodyString
	} else {
		return fmt.Sprintf("Reponse was %d", resp.StatusCode)
	}
}

func buildEndpoint(upperBound int) (string, error) {
	endpoint, err := url.JoinPath(PrimeNumbersURI, fmt.Sprintf("/prime/%d", upperBound))
	return endpoint, err
}

func DoSequentialCalls(count int, upperBound int) string {

	endpoint, err := buildEndpoint(upperBound)
	if err != nil {
		return fmt.Sprintf("Could not build the url: %v", err)
	}

	log.Printf("Calling %s %d times sequentially", endpoint, count)

	t0 := time.Now().UnixMilli()
	t1 := t0

	response := ""
	for i := range count {
		r := doRequest(endpoint)
		t2 := time.Now().UnixMilli()
		log.Printf("request no. %d (%dms)", i+1, t2-t1)
		t1 = t2
		response += strings.Trim(r, " \n") + "\n"
	}

	log.Printf("Finished in: %dms", time.Now().UnixMilli()-t0)

	return response
}

func DoConcurrentCalls(count int, upperBound int) string {

	endpoint, err := buildEndpoint(upperBound)
	if err != nil {
		return fmt.Sprintf("Could not build the url: %v", err)
	}

	response := ""
	var wg sync.WaitGroup
	wg.Add(count)

	log.Printf("Calling %s %d times in parallel", endpoint, count)

	t0 := time.Now()

	for i := range count {
		go concurrentCall(i, endpoint, &response, &wg)
	}

	wg.Wait()

	log.Printf("Finished in: %dms", time.Now().UnixMilli()-t0.UnixMilli())

	return response
}

func concurrentCall(id int, endpoint string, response *string, wg *sync.WaitGroup) {
	defer wg.Done()
	t1 := time.Now().UnixMilli()
	r := doRequest(endpoint)
	t2 := time.Now().UnixMilli()
	*response += fmt.Sprintf("%d - %s\n", id, strings.Trim(r, " \n"))
	log.Printf("request no. %d (%dms)", id+1, t2-t1)
}

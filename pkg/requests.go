package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
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

func buildEndpoint(upperBound int, id int) (string, error) {
	endpoint, err := url.JoinPath(PrimeNumbersURI, fmt.Sprintf("-%d/prime/%d", id, upperBound))
	return endpoint, err
}

func DoSequentialCalls(count int, upperBound int) string {
	response := ""

	for i := range count {
		endpoint, _ := buildEndpoint(upperBound, i)
		r := doRequest(endpoint)
		response += strings.Trim(r, " \n") + "\n"
	}

	return response
}

func DoConcurrentCalls(count int, upperBound int) string {
	response := ""
	var wg sync.WaitGroup
	wg.Add(count)

	for i := range count {
		endpoint, _ := buildEndpoint(upperBound, i)
		go concurrentCall(i, endpoint, &response, &wg)
	}

	wg.Wait()
	return response
}

func concurrentCall(id int, endpoint string, response *string, wg *sync.WaitGroup) {
	defer wg.Done()
	r := doRequest(endpoint)
	*response += fmt.Sprintf("%d - %s\n", id, strings.Trim(r, " \n"))
}

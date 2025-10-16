package main

import (
	"errors"
	"net/http"
	"strconv"
)

func parseQuery(req *http.Request) (count int, upperBound int, err error) {
	query := req.URL.Query()

	paramCount := query.Get("count")
	count, err = strconv.Atoi(paramCount)

	if err != nil {
		err = errors.New("count parameter invalid or missing")
		return
	}

	paramUpperBound := query.Get("upperBound")
	upperBound, err = strconv.Atoi(paramUpperBound)

	if err != nil {
		err = errors.New("upperBound parameter invalid or missing")
		return
	}

	err = nil
	return
}

// Package handlers provides the BBR handlers extended with vSR classifier
package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"time"

	basepb "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	extProcPb "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	"github.com/go-logr/logr"

	"github.com/vsr-bbr-poc/vsr-classifier-plugin/classifier"
)

const (
	modelHeader              = "X-Gateway-Model-Name"
	intentCategoryHeader     = "X-Gateway-Intent-Category"
	intentConfidenceHeader   = "X-Gateway-Intent-Confidence"
	piiDetectedHeader        = "X-Gateway-PII-Detected"
	piiConfidenceHeader      = "X-Gateway-PII-Confidence"
	securityThreatHeader     = "X-Gateway-Security-Threat"
	securityConfidenceHeader = "X-Gateway-Security-Confidence"
)

// Metrics holds performance metrics for comparison
type Metrics struct {
	TotalRequests            int64
	TotalClassifications     int64
	AvgClassificationLatency float64
	AvgTotalLatency          float64
	ClassificationEnabled    bool
	IntentDistribution       map[string]int64
	PIIDetectedCount         int64
	JailbreakDetectedCount   int64
}

// BBRWithClassifier is the BBR server extended with vSR classifier plugin
type BBRWithClassifier struct {
	streaming  bool
	classifier classifier.Classifier
	metrics    *Metrics
	logger     logr.Logger
}

// RequestBody represents the OpenAI request body
type RequestBody struct {
	Model    string `json:"model"`
	Messages []struct {
		Role    string `json:"role"`
		Content string `json:"content"`
	} `json:"messages"`
}

// NewBBRWithClassifier creates a new BBR server with classifier
func NewBBRWithClassifier(streaming bool, clf classifier.Classifier, logger *logr.Logger) *BBRWithClassifier {
	bbr := &BBRWithClassifier{
		streaming:  streaming,
		classifier: clf,
		metrics: &Metrics{
			IntentDistribution:   make(map[string]int64),
			ClassificationEnabled: clf != nil,
		},
	}
	if logger != nil {
		bbr.logger = *logger
	}
	return bbr
}

// GetMetrics returns the current metrics
func (s *BBRWithClassifier) GetMetrics() *Metrics {
	return s.metrics
}

// Process handles the ext-proc stream
func (s *BBRWithClassifier) Process(srv extProcPb.ExternalProcessor_ProcessServer) error {
	ctx := srv.Context()
	streamedBody := &streamedBody{}

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		req, recvErr := srv.Recv()
		if recvErr == io.EOF {
			return nil
		}
		if recvErr != nil {
			return fmt.Errorf("cannot receive stream request: %v", recvErr)
		}

		var responses []*extProcPb.ProcessingResponse
		var err error

		switch v := req.Request.(type) {
		case *extProcPb.ProcessingRequest_RequestHeaders:
			if s.streaming && !req.GetRequestHeaders().GetEndOfStream() {
				// Wait for body
			} else {
				responses, err = s.HandleRequestHeaders(req.GetRequestHeaders())
			}
		case *extProcPb.ProcessingRequest_RequestBody:
			responses, err = s.processRequestBody(ctx, req.GetRequestBody(), streamedBody)
		case *extProcPb.ProcessingRequest_RequestTrailers:
			responses, err = s.HandleRequestTrailers(req.GetRequestTrailers())
		case *extProcPb.ProcessingRequest_ResponseHeaders:
			responses, err = s.HandleResponseHeaders(req.GetResponseHeaders())
		case *extProcPb.ProcessingRequest_ResponseBody:
			responses, err = s.HandleResponseBody(req.GetResponseBody())
		default:
			s.logger.Error(nil, "Unknown Request type", "request", v)
		}

		if err != nil {
			s.logger.Error(err, "Failed to process request")
			return err
		}

		for _, resp := range responses {
			if err := srv.Send(resp); err != nil {
				s.logger.Error(err, "Send failed")
				return fmt.Errorf("failed to send response: %v", err)
			}
		}
	}
}

type streamedBody struct {
	body []byte
}

func (s *BBRWithClassifier) processRequestBody(ctx context.Context, body *extProcPb.HttpBody, streamedBody *streamedBody) ([]*extProcPb.ProcessingResponse, error) {
	var requestBodyBytes []byte
	if s.streaming {
		streamedBody.body = append(streamedBody.body, body.Body...)
		if body.EndOfStream {
			requestBodyBytes = streamedBody.body
		} else {
			return nil, nil
		}
	} else {
		requestBodyBytes = body.GetBody()
	}

	return s.HandleRequestBody(ctx, requestBodyBytes)
}

// HandleRequestBody handles request bodies with classification
func (s *BBRWithClassifier) HandleRequestBody(ctx context.Context, requestBodyBytes []byte) ([]*extProcPb.ProcessingResponse, error) {
	startTime := time.Now()
	s.metrics.TotalRequests++

	var ret []*extProcPb.ProcessingResponse

	var requestBody RequestBody
	if err := json.Unmarshal(requestBodyBytes, &requestBody); err != nil {
		return nil, err
	}

	// Collect all headers to set
	headers := []*basepb.HeaderValueOption{}

	// Set model header (original BBR functionality)
	if requestBody.Model != "" {
		headers = append(headers, &basepb.HeaderValueOption{
			Header: &basepb.HeaderValue{
				Key:      modelHeader,
				RawValue: []byte(requestBody.Model),
			},
		})
	}

	// ============ vSR Classifier Plugin Extension ============
	if s.classifier != nil && s.classifier.IsInitialized() {
		// Extract user content from messages
		var userContent string
		for _, msg := range requestBody.Messages {
			if msg.Role == "user" {
				userContent += msg.Content + " "
			}
		}

		if userContent != "" {
			classificationStart := time.Now()
			result, err := s.classifier.Classify(ctx, userContent)
			classificationLatency := time.Since(classificationStart).Milliseconds()

			if err == nil {
				s.metrics.TotalClassifications++
				
				// Update metrics
				s.updateClassificationMetrics(result, classificationLatency)

				// Add classification headers
				classHeaders := s.buildClassificationHeaders(result)
				headers = append(headers, classHeaders...)
			}
		}
	}
	// ============ End vSR Classifier Plugin Extension ============

	// Update total latency metrics
	totalLatency := time.Since(startTime).Milliseconds()
	s.metrics.AvgTotalLatency = (s.metrics.AvgTotalLatency*float64(s.metrics.TotalRequests-1) + float64(totalLatency)) / float64(s.metrics.TotalRequests)

	if s.streaming {
		ret = append(ret, &extProcPb.ProcessingResponse{
			Response: &extProcPb.ProcessingResponse_RequestHeaders{
				RequestHeaders: &extProcPb.HeadersResponse{
					Response: &extProcPb.CommonResponse{
						ClearRouteCache: true,
						HeaderMutation: &extProcPb.HeaderMutation{
							SetHeaders: headers,
						},
					},
				},
			},
		})
		ret = s.addStreamedBodyResponse(ret, requestBodyBytes)
		return ret, nil
	}

	return []*extProcPb.ProcessingResponse{
		{
			Response: &extProcPb.ProcessingResponse_RequestBody{
				RequestBody: &extProcPb.BodyResponse{
					Response: &extProcPb.CommonResponse{
						ClearRouteCache: true,
						HeaderMutation: &extProcPb.HeaderMutation{
							SetHeaders: headers,
						},
					},
				},
			},
		},
	}, nil
}

func (s *BBRWithClassifier) updateClassificationMetrics(result *classifier.ClassificationResult, latencyMs int64) {
	// Update average classification latency
	n := float64(s.metrics.TotalClassifications)
	s.metrics.AvgClassificationLatency = (s.metrics.AvgClassificationLatency*(n-1) + float64(latencyMs)) / n

	// Update intent distribution
	s.metrics.IntentDistribution[result.IntentCategory]++

	// Update detection counts
	if result.HasPII {
		s.metrics.PIIDetectedCount++
	}
	if result.IsJailbreak {
		s.metrics.JailbreakDetectedCount++
	}
}

func (s *BBRWithClassifier) buildClassificationHeaders(result *classifier.ClassificationResult) []*basepb.HeaderValueOption {
	var headers []*basepb.HeaderValueOption

	// Intent classification headers
	headers = append(headers, &basepb.HeaderValueOption{
		Header: &basepb.HeaderValue{
			Key:      intentCategoryHeader,
			RawValue: []byte(result.IntentCategory),
		},
	})
	headers = append(headers, &basepb.HeaderValueOption{
		Header: &basepb.HeaderValue{
			Key:      intentConfidenceHeader,
			RawValue: []byte(fmt.Sprintf("%.4f", result.IntentConfidence)),
		},
	})

	// PII detection headers
	if result.HasPII {
		headers = append(headers, &basepb.HeaderValueOption{
			Header: &basepb.HeaderValue{
				Key:      piiDetectedHeader,
				RawValue: []byte("true"),
			},
		})
		headers = append(headers, &basepb.HeaderValueOption{
			Header: &basepb.HeaderValue{
				Key:      piiConfidenceHeader,
				RawValue: []byte(fmt.Sprintf("%.4f", result.PIIConfidence)),
			},
		})
	}

	// Security/Jailbreak headers
	if result.IsJailbreak {
		headers = append(headers, &basepb.HeaderValueOption{
			Header: &basepb.HeaderValue{
				Key:      securityThreatHeader,
				RawValue: []byte(result.SecurityThreat),
			},
		})
		headers = append(headers, &basepb.HeaderValueOption{
			Header: &basepb.HeaderValue{
				Key:      securityConfidenceHeader,
				RawValue: []byte(fmt.Sprintf("%.4f", result.SecurityConfidence)),
			},
		})
	}

	return headers
}

func (s *BBRWithClassifier) addStreamedBodyResponse(responses []*extProcPb.ProcessingResponse, requestBodyBytes []byte) []*extProcPb.ProcessingResponse {
	return append(responses, &extProcPb.ProcessingResponse{
		Response: &extProcPb.ProcessingResponse_RequestBody{
			RequestBody: &extProcPb.BodyResponse{
				Response: &extProcPb.CommonResponse{
					BodyMutation: &extProcPb.BodyMutation{
						Mutation: &extProcPb.BodyMutation_StreamedResponse{
							StreamedResponse: &extProcPb.StreamedBodyResponse{
								Body:        requestBodyBytes,
								EndOfStream: true,
							},
						},
					},
				},
			},
		},
	})
}

// HandleRequestHeaders handles request headers
func (s *BBRWithClassifier) HandleRequestHeaders(headers *extProcPb.HttpHeaders) ([]*extProcPb.ProcessingResponse, error) {
	return []*extProcPb.ProcessingResponse{
		{
			Response: &extProcPb.ProcessingResponse_RequestHeaders{
				RequestHeaders: &extProcPb.HeadersResponse{},
			},
		},
	}, nil
}

// HandleRequestTrailers handles request trailers
func (s *BBRWithClassifier) HandleRequestTrailers(trailers *extProcPb.HttpTrailers) ([]*extProcPb.ProcessingResponse, error) {
	return []*extProcPb.ProcessingResponse{
		{
			Response: &extProcPb.ProcessingResponse_RequestTrailers{
				RequestTrailers: &extProcPb.TrailersResponse{},
			},
		},
	}, nil
}

// HandleResponseHeaders handles response headers
func (s *BBRWithClassifier) HandleResponseHeaders(headers *extProcPb.HttpHeaders) ([]*extProcPb.ProcessingResponse, error) {
	return []*extProcPb.ProcessingResponse{
		{
			Response: &extProcPb.ProcessingResponse_ResponseHeaders{
				ResponseHeaders: &extProcPb.HeadersResponse{},
			},
		},
	}, nil
}

// HandleResponseBody handles response bodies
func (s *BBRWithClassifier) HandleResponseBody(body *extProcPb.HttpBody) ([]*extProcPb.ProcessingResponse, error) {
	return []*extProcPb.ProcessingResponse{
		{
			Response: &extProcPb.ProcessingResponse_ResponseBody{
				ResponseBody: &extProcPb.BodyResponse{},
			},
		},
	}, nil
}


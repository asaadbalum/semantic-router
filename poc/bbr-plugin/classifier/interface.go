// Package classifier provides the vSR classifier plugin interface for BBR
package classifier

import (
	"context"
	"fmt"
)

// ClassificationResult contains the classification output
type ClassificationResult struct {
	// Intent classification
	IntentCategory string  `json:"intent_category"`
	IntentConfidence float64 `json:"intent_confidence"`
	
	// PII detection
	HasPII    bool     `json:"has_pii"`
	PIITypes  []string `json:"pii_types,omitempty"`
	PIIConfidence float64 `json:"pii_confidence"`
	
	// Security/Jailbreak detection
	IsJailbreak      bool    `json:"is_jailbreak"`
	SecurityThreat   string  `json:"security_threat"`
	SecurityConfidence float64 `json:"security_confidence"`
	
	// Additional metadata
	ProcessingTimeMs int64 `json:"processing_time_ms"`
}

// Classifier is the interface that vSR classifier implements
type Classifier interface {
	// Classify performs classification on the given text content
	Classify(ctx context.Context, content string) (*ClassificationResult, error)
	
	// ClassifyBatch performs batch classification
	ClassifyBatch(ctx context.Context, contents []string) ([]*ClassificationResult, error)
	
	// IsInitialized returns whether the classifier is ready
	IsInitialized() bool
	
	// GetStats returns classifier statistics
	GetStats() map[string]interface{}
}

// HeadersFromClassification generates HTTP headers from classification result
func HeadersFromClassification(result *ClassificationResult) map[string]string {
	headers := make(map[string]string)
	
	// Intent headers
	if result.IntentCategory != "" {
		headers["X-Gateway-Intent-Category"] = result.IntentCategory
		headers["X-Gateway-Intent-Confidence"] = formatFloat(result.IntentConfidence)
	}
	
	// PII headers
	if result.HasPII {
		headers["X-Gateway-PII-Detected"] = "true"
		headers["X-Gateway-PII-Confidence"] = formatFloat(result.PIIConfidence)
	}
	
	// Security headers
	if result.IsJailbreak {
		headers["X-Gateway-Security-Threat"] = result.SecurityThreat
		headers["X-Gateway-Security-Confidence"] = formatFloat(result.SecurityConfidence)
	}
	
	return headers
}

func formatFloat(f float64) string {
	return fmt.Sprintf("%.4f", f)
}


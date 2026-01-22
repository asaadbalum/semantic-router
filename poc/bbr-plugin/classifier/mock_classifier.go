package classifier

import (
	"context"
	"strings"
	"time"
)

// MockClassifier is a mock implementation for POC testing
// In production, this would call the actual vSR Rust/CGO bindings
type MockClassifier struct {
	initialized bool
	stats       ClassifierStats
}

// ClassifierStats tracks performance metrics
type ClassifierStats struct {
	TotalClassifications int64
	TotalProcessingMs    int64
	AvgLatencyMs         float64
}

// NewMockClassifier creates a new mock classifier
func NewMockClassifier() *MockClassifier {
	return &MockClassifier{
		initialized: true,
	}
}

// Classify performs mock classification
func (c *MockClassifier) Classify(ctx context.Context, content string) (*ClassificationResult, error) {
	start := time.Now()
	
	result := &ClassificationResult{
		IntentCategory:    c.mockIntentClassification(content),
		IntentConfidence:  0.87 + float64(len(content)%13)/100.0,
		HasPII:            c.mockPIIDetection(content),
		PIITypes:          c.mockPIITypes(content),
		PIIConfidence:     0.92,
		IsJailbreak:       c.mockJailbreakDetection(content),
		SecurityThreat:    "none",
		SecurityConfidence: 0.95,
	}
	
	if result.IsJailbreak {
		result.SecurityThreat = "jailbreak_attempt"
	}
	
	result.ProcessingTimeMs = time.Since(start).Milliseconds()
	
	// Add simulated inference latency (representative of actual model)
	time.Sleep(5 * time.Millisecond)
	
	c.stats.TotalClassifications++
	c.stats.TotalProcessingMs += result.ProcessingTimeMs
	c.stats.AvgLatencyMs = float64(c.stats.TotalProcessingMs) / float64(c.stats.TotalClassifications)
	
	return result, nil
}

// ClassifyBatch performs batch mock classification
func (c *MockClassifier) ClassifyBatch(ctx context.Context, contents []string) ([]*ClassificationResult, error) {
	results := make([]*ClassificationResult, len(contents))
	for i, content := range contents {
		result, err := c.Classify(ctx, content)
		if err != nil {
			return nil, err
		}
		results[i] = result
	}
	return results, nil
}

// IsInitialized returns whether the classifier is ready
func (c *MockClassifier) IsInitialized() bool {
	return c.initialized
}

// GetStats returns classifier statistics
func (c *MockClassifier) GetStats() map[string]interface{} {
	return map[string]interface{}{
		"total_classifications": c.stats.TotalClassifications,
		"total_processing_ms":   c.stats.TotalProcessingMs,
		"avg_latency_ms":        c.stats.AvgLatencyMs,
		"initialized":           c.initialized,
		"type":                  "mock_classifier",
	}
}

// mockIntentClassification simulates intent classification
func (c *MockClassifier) mockIntentClassification(content string) string {
	lower := strings.ToLower(content)
	
	switch {
	case strings.Contains(lower, "code") || strings.Contains(lower, "function") || strings.Contains(lower, "programming"):
		return "coding"
	case strings.Contains(lower, "math") || strings.Contains(lower, "calculate") || strings.Contains(lower, "equation"):
		return "math"
	case strings.Contains(lower, "translate") || strings.Contains(lower, "language"):
		return "translation"
	case strings.Contains(lower, "summarize") || strings.Contains(lower, "summary"):
		return "summarization"
	case strings.Contains(lower, "write") || strings.Contains(lower, "essay") || strings.Contains(lower, "story"):
		return "creative_writing"
	default:
		return "general"
	}
}

// mockPIIDetection simulates PII detection
func (c *MockClassifier) mockPIIDetection(content string) bool {
	lower := strings.ToLower(content)
	piiPatterns := []string{
		"ssn", "social security", "credit card", "password",
		"@", "phone", "address", "email",
	}
	
	for _, pattern := range piiPatterns {
		if strings.Contains(lower, pattern) {
			return true
		}
	}
	return false
}

// mockPIITypes returns detected PII types
func (c *MockClassifier) mockPIITypes(content string) []string {
	lower := strings.ToLower(content)
	var types []string
	
	if strings.Contains(lower, "ssn") || strings.Contains(lower, "social security") {
		types = append(types, "SSN")
	}
	if strings.Contains(lower, "@") || strings.Contains(lower, "email") {
		types = append(types, "EMAIL")
	}
	if strings.Contains(lower, "credit card") {
		types = append(types, "CREDIT_CARD")
	}
	if strings.Contains(lower, "phone") {
		types = append(types, "PHONE")
	}
	
	return types
}

// mockJailbreakDetection simulates jailbreak detection
func (c *MockClassifier) mockJailbreakDetection(content string) bool {
	lower := strings.ToLower(content)
	jailbreakPatterns := []string{
		"ignore previous", "ignore all instructions", "pretend you are",
		"you are now", "bypass", "jailbreak", "dan mode",
	}
	
	for _, pattern := range jailbreakPatterns {
		if strings.Contains(lower, pattern) {
			return true
		}
	}
	return false
}









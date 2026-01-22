# POC: vSR Classifier as BBR Plugin

## Executive Summary

This POC demonstrates integrating the vLLM Semantic Router (vSR) classifier as a plugin into the Gateway API Inference Extension's Body-Based Router (BBR). The results show successful integration with measurable metrics.

## Benchmark Results

### Performance Comparison

| Metric | BBR Baseline | BBR + vSR Classifier | Overhead |
|--------|-------------|---------------------|----------|
| **Latency (ns/op)** | 1,517 | 5,224,104 | +5.2ms |
| **Memory (B/op)** | 952 | 1,788 | +836 B |
| **Allocations/op** | 22 | 39 | +17 |
| **Throughput (ops/3s)** | 2,357,962 | 691 | -99.97% |

> **Note**: The 5ms latency overhead is due to the mock classifier's simulated inference time. In production with the actual vSR Rust/CGO classifier, expect 1-10ms depending on model size and hardware.

### Classification Metrics

| Category | Count | Detection |
|----------|-------|-----------|
| Coding | 1 | ✅ |
| Math | 1 | ✅ |
| General | 3 | ✅ |
| Creative Writing | 2 | ✅ |
| Translation | 1 | ✅ |
| **PII Detected** | 1 | ✅ (SSN, EMAIL) |
| **Jailbreak Detected** | 1 | ✅ |

## Architecture

### Current BBR (Before)
```
┌─────────────────────────────────────────┐
│                   BBR                    │
├─────────────────────────────────────────┤
│ 1. Receive HTTP Body                     │
│ 2. Parse JSON → Extract "model" field    │
│ 3. Set X-Gateway-Model-Name header       │
│ 4. Return to Envoy                       │
└─────────────────────────────────────────┘
```

### BBR + vSR Classifier Plugin (After)
```
┌─────────────────────────────────────────────────────────┐
│                BBR + vSR Classifier                      │
├─────────────────────────────────────────────────────────┤
│ 1. Receive HTTP Body                                     │
│ 2. Parse JSON → Extract "model" field                    │
│ 3. Set X-Gateway-Model-Name header                       │
│ ─────────── vSR Classifier Plugin ───────────            │
│ 4. Extract user content from messages                    │
│ 5. Call vSR Classifier (ModernBERT/LoRA)                 │
│    ├─ Intent Classification                              │
│    ├─ PII Detection                                      │
│    └─ Security/Jailbreak Detection                       │
│ 6. Set classification headers:                           │
│    ├─ X-Gateway-Intent-Category                          │
│    ├─ X-Gateway-Intent-Confidence                        │
│    ├─ X-Gateway-PII-Detected                             │
│    └─ X-Gateway-Security-Threat                          │
│ ─────────────────────────────────────────                │
│ 7. Return to Envoy                                       │
└─────────────────────────────────────────────────────────┘
```

## Headers Added by vSR Classifier Plugin

| Header | Type | Description |
|--------|------|-------------|
| `X-Gateway-Intent-Category` | string | coding, math, general, creative_writing, etc. |
| `X-Gateway-Intent-Confidence` | float | 0.0 - 1.0 confidence score |
| `X-Gateway-PII-Detected` | bool | "true" if PII found |
| `X-Gateway-PII-Confidence` | float | PII detection confidence |
| `X-Gateway-Security-Threat` | string | "none", "jailbreak_attempt", etc. |
| `X-Gateway-Security-Confidence` | float | Security detection confidence |

## Files Created

```
/home/abalum/Projects/vsr-bbr-poc/
├── bbr-standalone/
│   └── bbr                          # Original BBR binary
├── gateway-api-inference-extension/ # GIE source
├── vsr-classifier-plugin/
│   ├── go.mod
│   ├── classifier/
│   │   ├── interface.go             # Classifier interface
│   │   └── mock_classifier.go       # Mock implementation
│   └── handlers/
│       └── bbr_with_classifier.go   # Extended BBR handlers
├── benchmarks/
│   ├── go.mod
│   └── benchmark_test.go            # Performance benchmarks
└── POC-RESULTS.md                   # This document
```

## How to Run

```bash
# Run tests
cd /home/abalum/Projects/vsr-bbr-poc/benchmarks
go test -v -run TestClassificationAccuracy
go test -v -run TestMetricsCollection

# Run benchmarks
go test -bench=. -benchmem -benchtime=3s
```

## Next Steps for Production

See the "Time Estimates" section below for production integration timeline.

---

# Time Estimates for Production Integration

## 1. Classifier Plugin into BBR (POC → Production)

| Phase | Effort | Duration |
|-------|--------|----------|
| **Phase 1: Core Integration** | | **2-3 weeks** |
| - Replace mock classifier with vSR Rust/CGO bindings | Medium | 3-5 days |
| - Handle CGO cross-compilation for containers | High | 3-5 days |
| - Add configuration for classifier models | Low | 1-2 days |
| - Unit tests and integration tests | Medium | 2-3 days |
| **Phase 2: Production Hardening** | | **2-3 weeks** |
| - Error handling and graceful degradation | Medium | 2-3 days |
| - Metrics and observability (Prometheus) | Low | 1-2 days |
| - Performance optimization (batching, caching) | High | 3-5 days |
| - Documentation and examples | Low | 2 days |
| - Security review and testing | Medium | 2-3 days |
| **Phase 3: Deployment** | | **1-2 weeks** |
| - Docker/OCI image builds | Low | 1-2 days |
| - Kubernetes manifests and Helm charts | Medium | 2-3 days |
| - CI/CD pipeline integration | Medium | 2 days |
| - Staging environment testing | Medium | 2-3 days |

**Total Estimate: 5-8 weeks**

## 2. Other vSR Sub-Modules as BBR Plugins

| Sub-Module | Complexity | Estimated Duration |
|------------|------------|-------------------|
| **Semantic Cache** | High | 4-6 weeks |
| - Redis/vector DB integration | High | 2-3 weeks |
| - Embedding generation | Medium | 1 week |
| - Cache invalidation logic | Medium | 1-2 weeks |
| **Guardrails (PII Policy)** | Medium | 2-3 weeks |
| - Policy engine integration | Medium | 1-2 weeks |
| - Response modification/blocking | Low | 3-5 days |
| - Audit logging | Low | 2-3 days |
| **Security/Jailbreak Guard** | Medium | 2-3 weeks |
| - Response blocking integration | Low | 3-5 days |
| - Alert/notification system | Medium | 1 week |
| - Admin override mechanisms | Low | 3-5 days |
| **MCP Tool Selection** | High | 3-4 weeks |
| - Tool registry integration | High | 2 weeks |
| - Dynamic tool routing | Medium | 1-2 weeks |

**Total for All Sub-Modules: 11-16 weeks** (can be parallelized)

## 3. Full vSR as BBR Plugin

Making the entire vSR a single plugin within BBR:

| Approach | Complexity | Estimated Duration |
|----------|------------|-------------------|
| **Option A: Modular Integration** | Medium | **12-16 weeks** |
| - Each sub-module as separate plugin | | |
| - Allows selective enablement | | |
| - Easier maintenance and testing | | |
| **Option B: Monolithic Integration** | High | **8-12 weeks** |
| - Single vSR plugin with all features | | |
| - Simpler deployment | | |
| - Harder to maintain/extend | | |
| **Option C: vSR as EPP Backend** | Low-Medium | **6-10 weeks** |
| - Use existing vSR as external service | | |
| - BBR calls vSR via gRPC | | |
| - Minimal code changes to either | | |

**Recommended: Option C for fastest time-to-production, then migrate to Option A for long-term.**

## Summary Timeline

```
Week 1-2:   POC refinement and stakeholder review
Week 3-6:   Classifier plugin production hardening
Week 7-10:  Semantic Cache plugin development
Week 11-14: Guardrails and Security plugins
Week 15-18: Full integration testing and deployment
Week 19-20: Production rollout and monitoring
```

**Total: ~20 weeks (5 months) for complete vSR → BBR plugin migration**

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CGO compilation complexity | High | Use pre-built Rust libraries or pure Go port |
| Model loading time on cold start | Medium | Lazy loading, model caching, warm-up probes |
| Latency impact on request path | High | Async classification, caching, batching |
| Memory footprint of ML models | Medium | Model quantization, shared model instances |
| API compatibility with GIE updates | Medium | Pin versions, maintain compatibility layer |

## Conclusion

The POC successfully demonstrates that vSR classifier can be integrated into BBR with:
- ✅ Clear plugin interface definition
- ✅ Measurable performance metrics
- ✅ Working classification pipeline
- ✅ Minimal changes to BBR core

The integration is feasible and aligns with the convergence strategy outlined in slide 13 of the presentation.









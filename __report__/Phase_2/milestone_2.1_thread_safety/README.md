# Milestone 2.1: Thread-Safe Architecture Redesign

This directory contains architecture analysis and design reports for Milestone 2.1, which focuses on redesigning Stichotrope's profiler architecture to integrate thread-safety as a first-class concern from the ground up.

## Overview

**Milestone**: 2.1 Thread-Safe Architecture Redesign  
**Version Target**: v0.2.0 (first milestone of Phase 2)  
**GitHub Milestone**: https://github.com/LittleCoinCoin/stichotrope/milestone/5  
**Roadmap Reference**: `__design__/02-product_roadmap_v2.md`

**Architectural Decision**: Complete redesign from scratch to integrate thread-safety from the ground up, not retrofitting to existing prototype. The prototype (v0.5.0) serves as a baseline for feature validation and performance comparison, not as the implementation foundation.

## Documents

### Phase 1: Architecture Evaluation (Task 2.1.0)

- **[00-architecture_evaluation_v0.md](./00-architecture_evaluation_v0.md)** ⭐ **CURRENT** - Comprehensive evaluation of thread-safety approaches
  - Issue: [#17 - Evaluate Thread-Safety Architecture Approaches](https://github.com/LittleCoinCoin/stichotrope/issues/17)
  - Aspect 1: Data Structure Safety (4 alternative approaches)
  - Aspect 2: Profiler Threading (4 alternative approaches)
  - Recommended approach with rationale
  - Trade-off analysis (performance vs complexity vs maintainability)
  - Prototype v0.5.0 comparison

### Phase 1: Architecture Design (Task 2.1.1)

- **[01-architecture_design_v0.md](./01-architecture_design_v0.md)** - Initial architecture design document
  - Issue: [#18 - Design Thread-Safe Architecture Document](https://github.com/LittleCoinCoin/stichotrope/issues/18)
  - Status: Superseded by v1

- **[01-architecture_design_v1.md](./01-architecture_design_v1.md)** ⭐ **CURRENT** - Refined architecture design document
  - Issue: [#18 - Design Thread-Safe Architecture Document](https://github.com/LittleCoinCoin/stichotrope/issues/18)
  - Pre-conditions: Task 2.1.0 approved ✅
  - Improvements from v0:
    - Mermaid diagrams (component architecture, data flow, lock hierarchy)
    - Pseudo-code focus with strategic code snippets
    - Binary merge vs sequential aggregation analysis
    - Streamlined testing section (details in Task 2.1.2)
    - Reduced length (~40% shorter, clearer for stakeholder review)

### Phase 2: Test Definition (Task 2.1.2)

- **[02-test_definition_v0.md](./02-test_definition_v0.md)** 📦 **ARCHIVED** - Initial test suite definition
  - Issue: [#19 - Design Thread-Safe Test Suite](https://github.com/LittleCoinCoin/stichotrope/issues/19)
  - Status: Superseded by v1

- **[02-test_definition_v1.md](./02-test_definition_v1.md)** ⭐ **CURRENT** - Refined test suite definition
  - Issue: [#19 - Design Thread-Safe Test Suite](https://github.com/LittleCoinCoin/stichotrope/issues/19)
  - Pre-conditions: Task 2.1.1 approved ✅
  - Improvements from v0:
    - Replaced Wobble with pytest (standard for Stichotrope)
    - Added dependency recommendations (pytest-timeout, psutil)
    - Fixed test development workflow section
    - Updated all execution examples to pytest commands
  - Test categories: Unit (11), Integration (6), Stress (4), Performance (3)
  - Total: 24 tests covering thread-safety validation
  - Test infrastructure: Fixtures, test data, validation helpers
  - Success gates: All requirements satisfied (awaiting review)

### Future Phases

- **Phase 3**: Implementation (Tasks 2.1.3, 2.1.4)

## Critical Findings

### Thread-Safety Issues in Prototype v0.5.0

1. **Global State Race Conditions**:
   - `_CALL_SITE_CACHE` (global dict) - concurrent registration/lookup
   - `_PROFILER_REGISTRY` (global dict) - concurrent profiler registration
   - `_NEXT_PROFILER_ID` (global counter) - non-atomic increment

2. **Instance State Race Conditions**:
   - `_tracks` dict - concurrent track creation/access
   - `_next_block_idx` dict - non-atomic block index allocation
   - `ProfileBlock.record_time()` - multiple field updates without synchronization

3. **Data Structure Mutations**:
   - ProfileBlock: hit_count, total_time_ns, min_time_ns, max_time_ns modified concurrently
   - No protection for read-modify-write operations

## Success Criteria

**Task 2.1.0 Success Gates**:
- ✅ Aspect 1: Data Structure Safety - 4 approaches documented with pros/cons
- ✅ Aspect 2: Profiler Threading - 4 approaches documented with pros/cons
- ✅ Recommended approach with clear rationale
- ✅ Trade-off analysis documented
- ✅ Prototype comparison documented
- ⏳ Evaluation review: Stakeholder review and approval pending

**Task 2.1.1 Success Gates** (Future):
- Architecture document with thread-local storage strategy, lock design, data structure choices
- Design decisions documented with rationale (based on evaluation in 2.1.0)
- Comparison to prototype v0.5.0
- Design review completed and approved

## Recommended Approach

Based on approved evaluation (Task 2.1.0):

**Aspect 1 (Data Structure Safety)**: **Hybrid Thread-Local + Lock-Based**
- Thread-local storage for per-thread profiling data (zero contention)
- RLock-protected global structures (call-site cache, profiler registry)
- Lock-protected aggregation during get_results()

**Aspect 2 (Profiler Threading)**: **Synchronous Profiling**
- All measurements on calling thread (accurate timing)
- No background profiler threads (simplicity)
- No queue-based architectures (avoid complexity)

**Performance Target**: ≤1% overhead increase vs prototype (currently 0.02-0.23%)

## Status

- ✅ Task 2.1.0: Evaluation report v0 - APPROVED by stakeholder
- ✅ Task 2.1.1: Design report v1 - APPROVED by stakeholder
  - v0: Initial version (superseded)
  - v1: Refined with Mermaid diagrams, pseudo-code focus, binary merge analysis
- ✅ Task 2.1.2: Test definition v1 complete - awaiting stakeholder review
  - v0: Initial version (superseded)
  - v1: Refined with pytest integration, dependency recommendations, workflow clarity
  - 24 tests defined (11 unit, 6 integration, 4 stress, 3 performance)
  - Test infrastructure specified (fixtures, test data, validation helpers)
  - All success gates satisfied
- ⏳ Task 2.1.3: Not started (blocked by 2.1.2 approval)
- ⏳ Task 2.1.4: Not started (blocked by 2.1.3 completion)

---

**Last Updated**: 2025-11-07
**Report Version**: Evaluation v0 (approved), Design v1 (approved), Test Definition v1 (awaiting review)
**Next Steps**: Stakeholder review of test definition document v1


# User Prompt Template for Task 2.1.4: Thread-Safe Profiler Core Implementation

**Purpose**: This template provides a ready-to-use user prompt for initiating Task 2.1.4 (Thread-Safe Profiler Core Implementation, Issue #20).

**Usage**: Copy the prompt below and provide it to the AI agent to start Task 2.1.4.

---

## User Prompt for Task 2.1.4

```
**Context**: Merge Commit `c22c9c2` (head of milestone/2.1-thread-safe-architecture) completed Task 2.1.3 (test implementation). The test suite (24 tests) is implemented and ready to validate the thread-safe profiler core. Tasks 2.1.0 (architecture evaluation), 2.1.1 (architecture design), 2.1.2 (test definition), and 2.1.3 (test implementation) are complete and approved.

The architecture design v1 (`__report__/Phase_2/milestone_2.1_thread_safety/01-architecture_design_v1.md`) is the approved implementation specification. The test implementation handover report (`__report__/Phase_2/milestone_2.1_thread_safety/03-test_implementation_handover_v0.md`) provides complete guidance for this task.

It is time to implement the thread-safe profiler core which corresponds to task 2.1.4 (issue: `https://github.com/LittleCoinCoin/stichotrope/issues/20`).

**Your tasks**:
1. Review the architecture design v1 and test implementation handover report
   - The `__report__/Phase_2/milestone_2.1_thread_safety/README.md` provides an overview
   - The `__report__/Phase_2/milestone_2.1_thread_safety/01-architecture_design_v1.md` is the implementation specification
   - The `__report__/Phase_2/milestone_2.1_thread_safety/03-test_implementation_handover_v0.md` provides implementation guidance
2. Implement the thread-safe profiler core following the architecture design
   - Module-level changes (global locks and registries)
   - Profiler.__init__ changes (thread-local storage, global lock, thread registry)
   - Thread-local storage implementation (_get_thread_data with hasattr pattern)
   - Hot path implementation (lock-free measurement recording)
   - Aggregation implementation (sequential merge algorithm)
   - Clear method updates
3. Run the test suite frequently during implementation
   - Unit tests: `pytest -m unit tests/`
   - Integration tests: `pytest -m integration tests/`
   - All thread-safety tests: `pytest -m thread_safety tests/`
4. Verify all tests pass when implementation is complete
   - All 24 thread-safety tests should pass
   - Existing tests should still pass (API unchanged)
5. Create a test execution report documenting results
   - Test execution summary (pass/fail counts)
   - Performance measurements (overhead, aggregation time, memory)
   - Any deviations from expected behavior

**Constraints**:
- Follow the architecture design v1 specifications exactly
- Follow the org's standards about analytic behavior (read & study before actuation on the codebase) `cracking-shells-playbook/instructions/analytic-behavior.instructions.md`
- Follow the org's standards on work ethics (rigor and perseverance through challenges) `cracking-shells-playbook/instructions/work-ethics.instructions.md`
- Follow the org's testing standards `cracking-shells-playbook/instructions/testing.instructions.md`
- Follow the org's git-workflow `cracking-shells-playbook/instructions/git-workflow.md` (branch name, relevant modifications in same commit, logic commit history)
- Use the implementation checklist from the handover report
- Run tests frequently to validate implementation progress

**Important notes**:
- ⚠️ **Lock hierarchy is critical**: Acquire locks in order: _REGISTRY_LOCK → _GLOBAL_CACHE_LOCK → Profiler._global_lock
- ⚠️ **Hot path must be lock-free**: No locks in record_time() or measurement recording
- ⚠️ **Thread-local initialization pattern**: Use hasattr pattern to avoid AttributeError
- The test suite will guide implementation - tests will pass as you implement each component correctly
- Performance targets are informational (≤1% overhead, <10ms aggregation) but should be met if possible

**Expected deliverables**:
- Thread-safe profiler core implementation in `stichotrope/profiler.py`
- All 24 thread-safety tests passing
- Existing tests still passing (backward compatibility)
- Test execution report documenting results
- Git commits following conventional commit format
```

---

## Notes for AI Agent

**Key References**:
1. Architecture Design v1: Primary implementation specification
2. Test Implementation Handover Report: Implementation checklist and guidance
3. Test Definition v1: Test specifications and expected behaviors

**Implementation Order** (recommended):
1. Module-level changes (locks and registries)
2. Profiler.__init__ changes (thread-local storage setup)
3. Thread-local storage (_get_thread_data method)
4. Hot path (lock-free measurement recording)
5. Aggregation (sequential merge algorithm)
6. Clear method updates

**Testing Strategy**:
- Run unit tests after each major component
- Run integration tests after hot path and aggregation
- Run full test suite before creating execution report

**Success Criteria**:
- All 24 thread-safety tests pass
- Existing tests still pass
- Performance targets met (informational)
- Test execution report created

---

**Template Version**: v0
**Date**: 2025-11-13
**Next Task**: Task 2.1.4 (Thread-Safe Profiler Core Implementation, Issue #20)


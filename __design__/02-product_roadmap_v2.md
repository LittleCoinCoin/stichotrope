# Stichotrope v1.0.0 – Implementation Roadmap (v2 - Refined)

**Project**: Stichotrope – Python Profiling Library  
**Roadmap Date**: 2025-11-02  
**Phase**: Implementation Planning (Refined)  
**Source**: Synthesis v1 + Stakeholder Decisions + Workflow Alignment + Process Refinements  
**Prototype Version**: v0.5.0 (validated, GO decision, kept as baseline)  
**Target Version**: v1.0.0 (production release)  
**Timeline**: 7-9 weeks (documentation & tests-driven, architecture-first approach)

---

## Executive Summary

This refined roadmap incorporates process improvements for measurement bias reduction, infrastructure clarity, architectural evaluation rigor, semantic versioning, and git workflow documentation.

**Key Changes from v1**:
- ✅ **Performance Testing**: x10/x100 workload multipliers to reduce measurement bias, remove anchoring to 0.51%
- ✅ **pytest Infrastructure**: Clarified as infrastructure setup only, real tests added in Phase 2 per feature
- ✅ **Architecture Evaluation**: New task 2.1.0 evaluates data structure safety AND profiler threading approaches
- ✅ **Semantic Versioning**: Major.Minor.Patch strategy documented with version targets per phase/milestone
- ✅ **Git Workflow**: Stichotrope-specific branching strategy (dev → milestone → task hierarchy)

**Maintained from v1**:
- ✅ **Workflow Alignment**: Documentation → Tests → Implementation (integrated per task)
- ✅ **Architecture-First Approach**: Complete thread-safe redesign from scratch (not retrofit)
- ✅ **Prototype Baseline**: Keep v0.5.0 as comparison reference, not as foundation
- ✅ **MVP Scope**: Defer bandwidth profiling to v1.1.0 (not critical for MVP)
- ✅ **Reordered Milestones**: Thread safety architecture first, then features

**Stakeholder Decisions** (Maintained):
- ✅ Configuration Format: TOML (primary) with tomli/tomli-w dependencies
- ✅ Documentation: Expert A's comprehensive plan (MkDocs + ReadTheDocs)
- ✅ sys.monitoring: Deferred to v1.1.0 (post-v1.0.0)
- ✅ Hierarchical Profiling: Deferred to v1.1.0 (post-v1.0.0)
- ✅ Bandwidth Profiling: Deferred to v1.1.0 (not MVP)

**Architectural Decision**:
Complete redesign of profiler architecture from scratch to integrate thread-safety as a first-class concern from the ground up. This avoids retrofitting threading support after implementation, which creates technical debt and maintenance challenges. The prototype (v0.5.0) serves as a baseline for feature validation and performance comparison, not as the implementation foundation.

---

## Versioning Strategy

**Semantic Versioning (SemVer)**: `Major.Minor.Patch`

**Version Progression**:
- **Major Version**: 0 (prototype/development phase) → 1 (production release v1.0.0)
  - Major=0 enforced until v1.0.0 release
  - Breaking changes allowed during Major=0 phase
  - Major=1 signals production-ready, stable API

- **Minor Version**: Increments per Phase completion
  - Phase 1 complete → v0.1.0 (Infrastructure Foundation)
  - Phase 2 complete → v0.2.0 (Core Architecture & Features)
  - Phase 3 complete → v0.3.0 (Release Preparation)
  - Final release → v1.0.0 (Production Release)

- **Patch Version**: Increments per Milestone completion within a Phase
  - Milestone 1.1 complete → v0.1.0 (first milestone of Phase 1)
  - Milestone 1.2 complete → v0.1.1 (second milestone of Phase 1)
  - Milestone 1.3 complete → v0.1.2 (third milestone of Phase 1)
  - Milestone 1.4 complete → v0.1.3 (fourth milestone of Phase 1)
  - Milestone 2.1 complete → v0.2.0 (first milestone of Phase 2)
  - Milestone 2.2 complete → v0.2.1 (second milestone of Phase 2)
  - Milestone 2.3 complete → v0.2.2 (third milestone of Phase 2)
  - Milestone 2.4 complete → v0.2.3 (fourth milestone of Phase 2)

- **Tasks**: Do NOT increment version (tasks are sub-units of milestones)

**Version Management**:
- Configured in `pyproject.toml` with `python-semantic-release`
- Automated version bumping based on conventional commits
- Git tags created automatically on version increments
- PyPI publishing triggered on v1.0.0 tag

---

## Git Workflow

**Stichotrope-Specific Branching Strategy** (Project Variation)

**Branch Hierarchy**:
```
main (production, v1.0.0 release only)
  └── dev (development integration branch)
      ├── milestone/1.1-testing-framework
      │   ├── task/1.1.1-performance-test-suite
      │   ├── task/1.1.2-competitive-benchmark
      │   └── task/1.1.3-pytest-infrastructure
      ├── milestone/1.2-ci-cd-pipeline
      │   ├── task/1.2.1-github-actions
      │   ├── task/1.2.2-platform-matrix
      │   └── task/1.2.3-code-quality
      ├── milestone/2.1-thread-safe-architecture
      │   ├── task/2.1.0-evaluate-approaches
      │   ├── task/2.1.1-design-architecture
      │   ├── task/2.1.2-design-tests
      │   ├── task/2.1.3-implement-core
      │   └── task/2.1.4-implement-tests
      └── ...
```

**Workflow Rules**:

1. **All work from `dev` branch** (not `main`)
   - `main` is production-only, receives merges only at v1.0.0 release
   - `dev` is the integration branch for all development work

2. **Milestone branches from `dev`**
   - Branch naming: `milestone/<milestone-id>-<short-description>`
   - Example: `milestone/2.1-thread-safe-architecture`
   - Created when milestone work begins
   - Deleted after merge back to `dev`

3. **Task branches from milestone branches**
   - Branch naming: `task/<task-id>-<short-description>`
   - Example: `task/2.1.1-design-architecture`
   - Created when task work begins
   - Deleted after merge back to milestone branch

4. **Merge Hierarchy**:
   - Task branches → Milestone branch (when task complete)
   - Milestone branch → `dev` (when ALL milestone tasks complete)
   - `dev` → `main` (when milestone in `dev` passes ALL tests: regression, unit, integration, performance)

5. **Merge Criteria**:
   - **Task → Milestone**: Task success gates met, task tests pass
   - **Milestone → dev**: All milestone tasks complete, all milestone tests pass, no regressions
   - **dev → main**: ALL tests pass (regression, unit, integration, performance), ready for release

6. **Conventional Commits**:
   - Follow organization's conventional commit format
   - Enables automated semantic versioning
   - See `.augment/rules/git-workflow.md` for commit message standards

**Note**: This is a Stichotrope-specific variation of the organization's standard git workflow, optimized for milestone-based development with strict quality gates.

---

## Phase 1: Infrastructure Foundation (Weeks 1-2)

**Version Target**: v0.1.0 (after all Phase 1 milestones complete)

**Objective**: Establish robust testing, CI/CD, packaging, and documentation infrastructure

### Milestone 1.1: Testing Framework & Performance Baseline (3-4 days)

**Version Target**: v0.1.0 (first milestone of Phase 1)

**Tasks**:

**1.1.1 – Establish Performance Test Suite**
- **Goal**: Create comprehensive performance testing framework with unbiased baseline measurements
- **Pre-conditions**: Core profiler implementation complete (v0.2.0, v0.3.0)
- **Success Gates**: 
  - Performance test suite runs successfully at x1, x10, and x100 workload multipliers
  - Baseline measurements documented with confidence intervals (95% CI)
  - Statistical analysis includes: mean, median, std dev, min, max across multiple runs
  - Performance regression detection working (alerts on >1% degradation)
  - No explicit reference to prototype's 0.51% overhead (avoid anchoring bias)

**1.1.2 – Create Competitive Benchmark Suite**
- **Goal**: Implement benchmarking against cProfile, py-spy, line_profiler, pyinstrument
- **Pre-conditions**: Performance test suite complete
- **Success Gates**:
  - Benchmark suite compares Stichotrope vs 4 competitors
  - Results exportable to JSON for tracking
  - Baseline competitive positioning documented

**1.1.3 – Establish pytest Infrastructure**
- **Goal**: Set up pytest infrastructure for future test development
- **Pre-conditions**: None (can start in parallel)
- **Success Gates**:
  - pytest configured in pyproject.toml
  - pytest-cov plugin installed and configured
  - Test directory structure created (tests/, tests/unit/, tests/integration/)
  - Basic smoke test passes (import stichotrope, basic profiler instantiation)
  - CI integration ready for future tests
  - **NOTE**: Do NOT expect >90% coverage at this stage. Real test writing will be added in Phase 2 as part of the documentation & tests-driven workflow for each feature implementation.

### Milestone 1.2: CI/CD Pipeline (2-3 days)

**Version Target**: v0.1.1 (second milestone of Phase 1)

**Tasks**:

**1.2.1 – Create GitHub Actions Workflow**
- **Goal**: Implement automated testing, linting, and type checking on every push/PR
- **Pre-conditions**: pytest infrastructure established
- **Success Gates**:
  - Workflow runs on push and PR
  - All checks pass (pytest, black, ruff, mypy)
  - Coverage reports generated

**1.2.2 – Configure Platform & Python Version Matrix**
- **Goal**: Test on Windows/Linux/macOS with Python 3.9-3.12
- **Pre-conditions**: GitHub Actions workflow created
- **Success Gates**:
  - CI matrix: 3 platforms × 4 Python versions = 12 test runs
  - All tests pass on all combinations
  - Performance tests run on each platform

**1.2.3 – Set Up Code Quality Checks**
- **Goal**: Integrate ruff, black, mypy into CI pipeline
- **Pre-conditions**: GitHub Actions workflow created
- **Success Gates**:
  - Linting passes (ruff)
  - Formatting verified (black)
  - Type checking passes (mypy)
  - CI blocks merge if checks fail

### Milestone 1.3: PyPI Packaging (1 day)

**Version Target**: v0.1.2 (third milestone of Phase 1)

**Tasks**:

**1.3.1 – Update pyproject.toml for v1.0.0**
- **Goal**: Complete package metadata and dependency configuration
- **Pre-conditions**: Core implementation complete
- **Success Gates**:
  - pyproject.toml has complete metadata (name, version, description, etc.)
  - Dependencies: tomli, tomli-w for TOML support
  - Optional dependencies: mkdocs, mkdocstrings for docs
  - Version managed by python-semantic-release
  - **Semantic versioning configured with Major=0 enforced until v1.0.0 release**

**1.3.2 – Create PyPI Landing Page**
- **Goal**: Write compelling README.md for PyPI
- **Pre-conditions**: Package metadata complete
- **Success Gates**:
  - README.md includes: features, installation, quick start, examples
  - Renders correctly on PyPI
  - Links to documentation

**1.3.3 – Set Up Automated PyPI Publishing**
- **Goal**: Automate package publishing on version tags
- **Pre-conditions**: GitHub Actions workflow, pyproject.toml complete
- **Success Gates**:
  - GitHub Actions publishes to PyPI on tag push
  - pip install stichotrope works
  - Package metadata correct on PyPI

### Milestone 1.4: Documentation Infrastructure (2-3 days)

**Version Target**: v0.1.3 (fourth milestone of Phase 1)

**Tasks**:

**1.4.1 – Set Up MkDocs Project**
- **Goal**: Initialize MkDocs with professional structure
- **Pre-conditions**: None (can start in parallel)
- **Success Gates**:
  - mkdocs.yml configured with navigation structure
  - docs/ directory with index.md, getting-started.md
  - Local build works: mkdocs serve
  - Site builds successfully

**1.4.2 – Configure mkdocstrings for API Auto-Generation**
- **Goal**: Enable automatic API documentation from docstrings
- **Pre-conditions**: MkDocs project initialized
- **Success Gates**:
  - mkdocstrings plugin configured
  - API reference auto-generated from stichotrope module
  - Google-style docstrings render correctly
  - API docs include all public classes/functions

**1.4.3 – Set Up ReadTheDocs Integration**
- **Goal**: Configure ReadTheDocs for automated documentation publishing
- **Pre-conditions**: MkDocs project complete, mkdocstrings configured
- **Success Gates**:
  - ReadTheDocs account linked to repository
  - .readthedocs.yaml configured
  - Documentation builds automatically on push
  - Docs published to readthedocs.io

---

## Phase 2: Core Architecture & Features (Weeks 3-6)

**Version Target**: v0.2.0 (after all Phase 2 milestones complete)

**Objective**: Redesign architecture with thread-safety as first-class concern, then implement production-critical features

### Milestone 2.1: Thread-Safe Architecture Redesign (1-2 weeks)

**Version Target**: v0.2.0 (first milestone of Phase 2)

**Architectural Decision**: Complete redesign from scratch to integrate thread-safety from the ground up, not retrofitting to existing prototype.

**Tasks**:

**2.1.0 – Evaluate Thread-Safety Architecture Approaches**
- **Goal**: Comprehensive evaluation of alternative thread-safety approaches before design commitment
- **Pre-conditions**: Phase 1 infrastructure complete
- **Success Gates**:
  - **Aspect 1: Data Structure Safety** - At least 2-3 alternative approaches documented:
    - Thread-local storage (threading.local()) for per-thread profiling data
    - Lock-based synchronization (RLock, Lock) for shared data structures
    - Atomic operations (threading.atomic, lock-free data structures)
    - Immutable data structures with copy-on-write semantics
    - Pros/cons analysis for each approach (performance, complexity, maintainability)
  - **Aspect 2: Profiler Threading** - At least 2-3 alternative approaches documented:
    - Synchronous profiling (measurements on main thread, blocking)
    - Asynchronous profiling (measurements on separate thread, non-blocking)
    - Hybrid approach (start/stop on main thread, data aggregation on separate thread) --> Solution some of the stakeholders had in mind; is it any good?
    - Queue-based profiling (measurements queued, processed by background thread)
    - Pros/cons analysis for each approach (overhead, accuracy, complexity)
  - **Recommended Approach**: Clear selection with rationale for both aspects
  - **Trade-off Analysis**: Performance vs complexity vs maintainability documented
  - **Prototype Comparison**: How recommended approach differs from v0.5.0 documented
  - **Evaluation Review**: Stakeholder review completed and approved

**2.1.1 – Design Thread-Safe Architecture Document**
- **Goal**: Create comprehensive architecture design document for thread-safe profiler
- **Pre-conditions**: Architecture evaluation complete (task 2.1.0)
- **Success Gates**:
  - Architecture document includes: thread-local storage strategy, lock design, data structure choices
  - Design decisions documented with rationale (based on evaluation in 2.1.0)
  - Comparison to prototype (v0.5.0) approach documented
  - Design review completed and approved

**2.1.2 – Design Thread-Safe Test Suite**
- **Goal**: Define comprehensive test suite for thread-safety validation
- **Pre-conditions**: Architecture design document complete
- **Success Gates**:
  - Test plan includes: unit tests, integration tests, stress tests, race condition detection
  - Test scenarios cover: single-threaded, multi-threaded, high contention, thread pool
  - Test data and fixtures defined
  - Test review completed and approved

**2.1.3 – Implement Thread-Safe Profiler Core**
- **Goal**: Implement redesigned profiler with thread-safety as first-class concern
- **Pre-conditions**: Architecture design and test suite complete
- **Success Gates**:
  - Thread-local storage implemented using threading.local()
  - RLocks protect critical sections
  - All thread-safety tests pass
  - Performance overhead ≤1% vs baseline

**2.1.4 – Implement Thread-Safe Test Suite**
- **Goal**: Execute comprehensive thread-safety testing
- **Pre-conditions**: Thread-safe profiler core implemented
- **Success Gates**:
  - All unit tests pass (thread-local storage, RLocks, data isolation)
  - All integration tests pass (multi-threaded scenarios)
  - Stress tests pass (10+ threads, high contention)
  - No race conditions detected
  - Results aggregation correct across threads

### Milestone 2.2: Configuration System (2-3 days)

**Version Target**: v0.2.1 (second milestone of Phase 2)

**Tasks**:

**2.2.1 – Design Configuration System Document**
- **Goal**: Create design document for TOML-based configuration system
- **Pre-conditions**: Thread-safe architecture complete
- **Success Gates**:
  - Design document includes: TOML parsing, env var override, programmatic API
  - Priority order documented: programmatic > env vars > TOML file > defaults
  - Configuration schema defined
  - Design review completed and approved

**2.2.2 – Design Configuration Test Suite**
- **Goal**: Define comprehensive test suite for configuration system
- **Pre-conditions**: Configuration design document complete
- **Success Gates**:
  - Test plan includes: TOML parsing, env var override, priority order, error handling
  - Test scenarios cover: valid configs, invalid configs, missing files, env var override
  - Test data and fixtures defined
  - Test review completed and approved

**2.2.3 – Implement Configuration System**
- **Goal**: Add TOML configuration file support with tomli/tomli-w
- **Pre-conditions**: Configuration design and test suite complete
- **Success Gates**:
  - TOML files parse correctly
  - Configuration values accessible programmatically
  - Environment variables override TOML settings
  - Error messages clear for invalid TOML
  - All configuration tests pass

**2.2.4 – Create Configuration Examples**
- **Goal**: Provide concrete use cases with example TOML files
- **Pre-conditions**: Configuration system implemented
- **Success Gates**:
  - 4 example configurations: dev, production, selective profiling, performance tuning
  - Examples in docs/examples/config/
  - Each example documented with use case

### Milestone 2.3: Input Validation & Error Handling (2-3 days)

**Version Target**: v0.2.2 (third milestone of Phase 2)

**Tasks**:

**2.3.1 – Design Input Validation & Error Handling Document**
- **Goal**: Create design document for input validation and error handling
- **Pre-conditions**: Thread-safe architecture complete
- **Success Gates**:
  - Design document includes: validation rules, error types, error messages
  - Error handling strategy documented
  - Design review completed and approved

**2.3.2 – Design Validation & Error Handling Test Suite**
- **Goal**: Define comprehensive test suite for validation and error handling
- **Pre-conditions**: Validation design document complete
- **Success Gates**:
  - Test plan includes: valid inputs, invalid inputs, edge cases, error messages
  - Test scenarios cover: track IDs, block names, configuration values
  - Test data and fixtures defined
  - Test review completed and approved

**2.3.3 – Implement Input Validation**
- **Goal**: Validate all user inputs with clear error messages
- **Pre-conditions**: Validation design and test suite complete
- **Success Gates**:
  - Track IDs validated (non-negative integers)
  - Block names validated (non-empty strings)
  - Configuration values validated
  - Error messages guide users to fix issues
  - All validation tests pass

**2.3.4 – Implement Graceful Error Handling**
- **Goal**: Handle edge cases without crashing
- **Pre-conditions**: Input validation implemented
- **Success Gates**:
  - Zero-duration blocks handled correctly
  - Empty tracks handled correctly
  - Invalid configurations caught with helpful messages
  - No unhandled exceptions in normal usage
  - All error handling tests pass

### Milestone 2.4: Repetition Testing Framework (3-5 days)

**Version Target**: v0.2.3 (fourth milestone of Phase 2)

**Tasks**:

**2.4.1 – Design Repetition Testing Framework Document**
- **Goal**: Create design document for statistical benchmarking framework
- **Pre-conditions**: Thread-safe architecture complete
- **Success Gates**:
  - Design document includes: repetition API, statistical analysis, confidence intervals
  - Design decisions documented with rationale
  - Design review completed and approved

**2.4.2 – Design Repetition Testing Test Suite**
- **Goal**: Define comprehensive test suite for repetition testing
- **Pre-conditions**: Repetition testing design document complete
- **Success Gates**:
  - Test plan includes: statistical functions, confidence intervals, outlier detection
  - Test scenarios cover: normal distributions, edge cases, small samples
  - Test data and fixtures defined
  - Test review completed and approved

**2.4.3 – Implement Repetition Testing Framework**
- **Goal**: Add statistical benchmarking for repeated measurements
- **Pre-conditions**: Repetition testing design and test suite complete
- **Success Gates**:
  - Repetition API: profiler.repeat(iterations, func)
  - Statistical analysis: mean, std dev, min, max
  - Confidence intervals computed
  - Outlier detection working
  - All repetition testing tests pass

**2.4.4 – Verify Performance Gates**
- **Goal**: Ensure all Phase 2 changes meet ≤1% overhead increase threshold
- **Pre-conditions**: All Phase 2 features implemented
- **Success Gates**:
  - Performance tests pass
  - Overhead ≤1% vs baseline
  - Competitive benchmarking shows no regression

---

## Phase 3: Release Preparation (Weeks 7-9)

**Version Target**: v0.3.0 (after all Phase 3 milestones complete) → v1.0.0 (production release)

**Objective**: Complete documentation, final validation, and release v1.0.0

### Milestone 3.1: Documentation Completion (3-5 days)

**Version Target**: v0.3.0 (first milestone of Phase 3)

**Tasks**:

**3.1.1 – Write User Guide**
- **Goal**: Comprehensive guide for end users
- **Pre-conditions**: MkDocs infrastructure complete
- **Success Gates**:
  - Installation instructions
  - Quick start guide
  - Configuration guide
  - Examples for common use cases

**3.1.2 – Write API Reference**
- **Goal**: Complete API documentation auto-generated from docstrings
- **Pre-conditions**: mkdocstrings configured
- **Success Gates**:
  - All public classes documented
  - All public functions documented
  - Examples included for each API
  - Google-style docstrings complete

**3.1.3 – Write Tutorials**
- **Goal**: Step-by-step tutorials for common scenarios
- **Pre-conditions**: User guide and API reference complete
- **Success Gates**:
  - Tutorial 1: Basic profiling with decorators
  - Tutorial 2: Multi-track organization
  - Tutorial 3: Configuration and customization
  - Tutorial 4: Performance optimization

**3.1.4 – Create Performance Comparison Page**
- **Goal**: Document competitive positioning vs cProfile, py-spy, etc.
- **Pre-conditions**: Competitive benchmarking complete
- **Success Gates**:
  - Benchmark results published
  - Comparison tables for each competitor
  - Performance characteristics explained
  - Use case recommendations

**3.1.5 – Write Troubleshooting Guide**
- **Goal**: Common issues and solutions
- **Pre-conditions**: Implementation complete
- **Success Gates**:
  - FAQ section with common questions
  - Troubleshooting section with solutions
  - Performance tuning guide

### Milestone 3.2: Final Validation & Release (2-3 days)

**Version Target**: v1.0.0 (production release)

**Tasks**:

**3.2.1 – Final Performance Validation**
- **Goal**: Verify all performance gates met
- **Pre-conditions**: All features implemented
- **Success Gates**:
  - Performance overhead ≤1% for ≥1ms blocks
  - No regressions from prototype
  - Competitive benchmarking complete
  - All tests pass

**3.2.2 – Final Competitive Benchmarking**
- **Goal**: Run final benchmark suite against competitors
- **Pre-conditions**: All features implemented
- **Success Gates**:
  - Benchmarks run successfully
  - Results documented
  - Competitive positioning clear

**3.2.3 – Update CHANGELOG.md**
- **Goal**: Document all changes from v0.5.0 to v1.0.0
- **Pre-conditions**: All features implemented
- **Success Gates**:
  - CHANGELOG includes all features
  - Breaking changes documented
  - Migration guide provided

**3.2.4 – Create GitHub Release**
- **Goal**: Tag v1.0.0 and publish release notes
- **Pre-conditions**: All validation complete
- **Success Gates**:
  - Git tag v1.0.0 created
  - Release notes published on GitHub
  - PyPI package published

---

## Deferred Features (v1.1.0+)

**Bandwidth Profiling**:
- Rationale: Not critical for MVP; can be added post-v1.0.0
- Timeline: v1.1.0 release
- Benefit: Track bytes processed and MB/s, GB/s throughput
- Implementation: Separate tracking system for bandwidth metrics

**sys.monitoring Backend**:
- Rationale: Python 3.12+ only, requires significant refactoring
- Timeline: Post-v1.0.0 release
- Benefit: 2-5x overhead reduction on Python 3.12+
- Implementation: Backend abstraction with automatic selection

**Hierarchical Profiling**:
- Rationale: Complex feature, not critical for v1.0.0
- Timeline: Post-v1.0.0 release
- Benefit: Better organization of nested profiling data
- Implementation: Tree structure for call hierarchies

---

## Success Criteria for v1.0.0

**Functional Requirements**:
- ✅ Thread-safe for multi-threaded applications (redesigned architecture)
- ✅ Configuration system (TOML, env vars, programmatic)
- ✅ Input validation with clear error messages
- ✅ Repetition testing with statistical analysis
- ✅ Multi-track organization
- ✅ CSV/JSON export (CppProfiler-compatible)

**Quality Requirements**:
- ✅ Test coverage >90%
- ✅ Performance ≤1% overhead for ≥1ms blocks
- ✅ Competitive positioning documented
- ✅ Complete documentation on ReadTheDocs
- ✅ Platform support: Windows, Linux, macOS
- ✅ Python versions: 3.9, 3.10, 3.11, 3.12
- ✅ pip install stichotrope works

---

## Topological Ordering for Parallel Development

**Critical Path** (must complete in order):
1. Phase 1.1 → Phase 1.2 → Phase 1.3 → Phase 1.4
2. Phase 2.1 (evaluation + design + tests) → Phase 2.1 (implementation) → Phase 2.2/2.3/2.4 (can run in parallel)
3. Phase 3.1 + Phase 3.2 (can run in parallel)

**Parallel Opportunities**:
- Phase 1.1 and Phase 1.4 can start simultaneously
- Phase 1.2 and Phase 1.3 can start after Phase 1.1
- Phase 2.2, 2.3, 2.4 can run in parallel after Phase 2.1 implementation complete
- Phase 3.1 and Phase 3.2 can run in parallel

---

**Report Version**: v2 (Refined - Process Improvements)
**Status**: Ready for GitHub Issue creation
**Next Steps**: Create GitHub Issues for each task, assign to team members, begin Phase 1


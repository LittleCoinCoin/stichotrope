# Augment prompts

## 1.

### 1.1 Original

### 1.2 Augmented

Not done


## 2. Iteration over the benchmark results presentation

### 2.1 Original

Good iteration overall but graphs are suspicious. Here are my comments:

- How did you build the graphs? I was expecting to have scientific-like display of the averages with bar plots and statistical tests to compute p-value to chek if two groups are equivalent of significantly different.
  - I strongly advise you to search online about statisitical testing when comparing two data groups. 
  - maybe even import new deps in as "dev" or "benchmark" in the pyproject.toml
  - I see that the json you got are basically only the averages but you didn't keep the raw measurement data? Then how can we make people believe we didn't event it if we don't provide the graphs?
- The graph for "Context Method" is empty
- I want an additional test or bench mark which gives the actual averaged timing cost of performing the profiling
  - earlier you mentioned ~1.8 µs, I want the code that show this is true and include it in the benchmark
  - this also needs the raw capture data, the mean value and the standard deviation
- I think I want an additional graph that compares cProfile and Stichotrope for the same measurements of functions and blocks.
  - This will allow us to show that we have equivalent timings (if the data shows that) 

I think my reqest to get the raw data means we need additional code written specifically for that. Search and evaluate if this is indeed the case.
You will likely have to re-perform the benchmarks for both the prototype and v0.2.0. For the prototype, this will be a bit tricky, I recommend (evaluate and improve based on your understanding of the task:
- Work in a specific branch `refactor/perf-benchmarks`
- Start with updating the statistics, benchmark, graph generation, and data generation utilities.
- Centralize everything is a dedicated directory: `./benchmarks`
- Use them to regenerate what we need for v0.2.0
- Commit everything you need.
- The prototype's code is available at commit tag `v0.1.0` (5fe3a02f578a5b17bdfbab73e8b1b66a99e9c4c0)
  - Check it out
  - create new branch `perf/prototype-measures`
  - Copy over the relevant measurements acquisition files
  - run the benchmarks
  - commit the results
  - go back to `refactor/perf-benchmarks`
  - cherry pick the data measurements commit and replace `__report__\perf\prototype`

**Your task**: I made several comments which require deep work. Proceed through them systematically

**Constraints**:
- `cracking-shells-playbook\instructions\analytic-behavior.instructions.md`
- `cracking-shells-playbook\instructions\work-ethics.instructions.md`
- We need scientific level graphs. I am not saying long reports; but at least things that rely on statistics.

### 2.2 Augmented

I have several concerns about the performance comparison analysis that require systematic investigation and improvement. The current graphs lack scientific rigor and statistical validation.

##### Issues Identified

###### 1. Statistical Rigor in Graphs (CRITICAL)
**Problem**: The current bar charts only show mean overhead percentages without statistical validation.

**Requirements**:
- Display means with error bars (standard deviation or 95% confidence intervals)
- Perform statistical hypothesis testing (e.g., t-tests, Mann-Whitney U test) to compute p-values
- Determine if performance differences between prototype and thread-safe are statistically significant or equivalent
- Research best practices for comparing two data groups statistically (search online for "statistical comparison of two groups", "t-test for performance comparison", "equivalence testing")
- Consider adding dependencies for statistical analysis (e.g., `scipy`, `statsmodels`) as dev/benchmark dependencies in `pyproject.toml`

**Question**: The baseline JSON files only contain aggregated statistics (mean, CI) but not raw measurement data. How can we provide credible evidence without the underlying raw data? We need to preserve raw measurements for transparency and reproducibility.

###### 2. Empty Context Method Graph (BUG)
**Problem**: The "Context Method" graph appears empty in the comparison charts.

**Action Required**: Investigate why the context manager data is not rendering and fix the visualization.

###### 3. Missing Profiler Constant Overhead Benchmark (NEW REQUIREMENT)
**Problem**: You mentioned ~1.8 µs constant overhead earlier, but there's no dedicated benchmark demonstrating this.

**Requirements**:
- Create a specific benchmark that measures the profiler's constant overhead (time cost per profiling operation)
- Capture raw measurement data (all individual timings, not just aggregates)
- Report mean, standard deviation, and confidence intervals
- Include visualization showing the distribution of overhead measurements
- This benchmark should be reproducible and included in the benchmark suite

###### 4. Missing cProfile Comparison (NEW REQUIREMENT)
**Problem**: No comparison exists between Stichotrope and Python's standard cProfile for equivalent workloads.

**Requirements**:
- Create benchmark comparing cProfile vs Stichotrope for identical function/block measurements
- Demonstrate timing equivalence (if data supports this claim) or document differences
- Use statistical tests to validate whether timing differences are significant
- Include comparison graph in the analysis

##### Implementation Strategy

###### Investigation Phase (FIRST)
Before implementing, investigate:
1. **Raw Data Availability**: Search the codebase to determine if raw measurement data is currently captured anywhere, or if only aggregated statistics are saved
2. **Data Capture Requirements**: Evaluate whether new code is needed to capture and persist raw measurements
3. **Statistical Testing Libraries**: Research which Python libraries are appropriate for the statistical comparisons (likely `scipy.stats` for t-tests, p-values)

###### Execution Plan (EVALUATE AND IMPROVE)
I propose the following workflow for regenerating benchmarks with proper statistical rigor:

**Branch Strategy**:
1. Create working branch: `refactor/perf-benchmarks`
2. Update benchmark infrastructure in this branch:
   - Modify statistics collection to capture raw measurement data
   - Update benchmark scripts to save raw data alongside aggregated statistics
   - Create graph generation utilities with statistical testing (error bars, p-values)
   - Centralize all benchmark code in `./benchmarks/` directory
   - Add new benchmarks: constant overhead measurement, cProfile comparison

**v0.2.0 (Thread-Safe) Measurements**:
3. Use updated infrastructure to regenerate v0.2.0 baselines with raw data
4. Commit all infrastructure code and v0.2.0 measurements

**v0.1.0 (Prototype) Measurements**:
5. Checkout prototype code at tag `v0.1.0` (commit `5fe3a02f578a5b17bdfbab73e8b1b66a99e9c4c0`)
6. Create branch: `perf/prototype-measures`
7. Copy the updated measurement acquisition scripts from `refactor/perf-benchmarks`
8. Run benchmarks to capture prototype measurements with raw data
9. Commit measurement results only
10. Return to `refactor/perf-benchmarks` branch
11. Cherry-pick the measurement data commit
12. Replace contents of `__report__/perf/prototype/` with new data

**Analysis and Reporting**:
13. Generate statistically rigorous comparison graphs with error bars and p-values
14. Update comparison report with statistical findings

**Evaluation Request**: Review this workflow and improve it based on your understanding of:
- Git workflow best practices for this scenario
- Whether the cherry-pick strategy is optimal or if there's a better approach
- Any potential issues with switching between branches and copying files

##### Your Task

Proceed systematically through these requirements:
1. **Investigate** raw data capture capabilities and statistical testing needs
2. **Plan** the implementation approach (improve my proposed workflow if needed)
3. **Execute** the benchmark infrastructure improvements
4. **Regenerate** measurements for both prototype and thread-safe versions
5. **Analyze** with proper statistical rigor
6. **Report** findings with scientific-quality visualizations

##### Constraints

- Follow `cracking-shells-playbook/instructions/analytic-behavior.instructions.md` (read and study before acting)
- Follow `cracking-shells-playbook/instructions/work-ethics.instructions.md` (rigor and perseverance)
- Graphs must meet scientific standards: error bars, statistical tests, p-values, raw data transparency
- Reports should remain concise but statistically sound
- All claims must be backed by statistical evidence, not just visual inspection

##### Success Criteria

- [ ] Raw measurement data captured and persisted for all benchmarks
- [ ] Statistical hypothesis tests performed (p-values computed)
- [ ] Graphs include error bars (SD or 95% CI)
- [ ] Context Method graph displays correctly
- [ ] Constant overhead benchmark (~1.8 µs claim) implemented and validated
- [ ] cProfile comparison benchmark implemented
- [ ] Both prototype and v0.2.0 measurements regenerated with new infrastructure
- [ ] Comparison report updated with statistical findings
- [ ] All work follows org standards for analytic rigor

## 3. Iterate over the benchmark results presentation

### 3.1 Original

Great work. Here are my comments:

- Git Workflow seems okay
- Your research about statistical tests is great. But I don't want to overwhelm readers with stats either. I just want to make sure the comparison graphs are sound.
  - Welch's t-test and +- 1SD is enough
  - There will be a small reports in the docs, or directly in the public facing README of the rpo to see this results and clearly announce what users can expect, but no deep stat reports
  - Hence, no need to go overboard. This is not a science project, bu we rely on statistics to maintain rigor.
- Scipy is okay.

**Your Task**:
1. Write the new version of the `__reports__\analysis_performance_benchmarking\03-statistical_rigor_investigation_v0.md` to v1 accounting for my comments
2. Proceed with the 4 phases.

**Note**: I cleared your todo list, you can re-generate TODOs based on the iteration of the plan

**Constraints**:
- `cracking-shells-playbook\instructions\analytic-behavior.instructions.md`
- `cracking-shells-playbook\instructions\work-ethics.instructions.md`
- `cracking-shells-playbook\instructions\reporting.instructions.md`
- We need scientific level graphs. I am not saying long reports; but at least things that rely on statistics.

### 3.2 Augmented

Excellent work on the investigation and planning. I approve the approach with the following refinements:

## Approved Decisions

1. **Git Workflow**: ✅ Approved - Your improved workflow is cleaner than my original proposal
2. **Statistical Testing**: ✅ Approved with scope reduction:
   - Use Welch's t-test for hypothesis testing
   - Display error bars as ±1 SD (standard deviation) on all graphs
   - **No need for**: TOST equivalence testing, Cohen's d effect size, or extensive statistical reports
   - **Rationale**: This is a production software project, not an academic publication. We need statistical rigor for sound engineering decisions, but should avoid overwhelming users with statistical jargon.
3. **Dependencies**: ✅ Approved - Add `scipy>=1.11.0` to dev dependencies

## Scope Clarification

**Target Audience**: Software engineers evaluating Stichotrope, not statisticians
**Deliverables**: 
- Publication-quality graphs with error bars and p-values
- Concise interpretation of results (e.g., "no statistically significant difference, p=0.42")
- User-facing documentation in README showing performance characteristics
- **NOT needed**: Deep statistical analysis reports, effect size calculations, equivalence testing

## Your Tasks

### Task 1: Update Investigation Report
Revise `__reports__/analysis_performance_benchmarking/03-statistical_rigor_investigation_v0.md` to version v1:
- Remove TOST equivalence testing from the plan
- Remove Cohen's d effect size calculations from the plan
- Simplify Phase 4 deliverables (no deep statistical reports, just concise comparison with graphs)
- Adjust effort estimates based on reduced scope
- Keep the technical rigor but reduce statistical complexity to: Welch's t-test + p-values + ±1 SD error bars

### Task 2: Execute All 4 Phases Systematically
Proceed with implementation following the revised plan:
- **Phase 1**: Infrastructure improvements (fix bug, add raw data persistence, add Welch's t-test, add error bars)
- **Phase 2**: New benchmarks (constant overhead, cProfile comparison)
- **Phase 3**: Regenerate measurements using approved git workflow
- **Phase 4**: Generate comparison graphs with statistical validation (concise, user-focused)

## Constraints & Standards

You must follow these organizational standards throughout:
1. **Analytic Behavior**: `cracking-shells-playbook/instructions/analytic-behavior.instructions.md`
   - Comprehensive analysis before action
   - Study existing code before modifications
2. **Work Ethics**: `cracking-shells-playbook/instructions/work-ethics.instructions.md`
   - Root cause analysis
   - Systematic debugging
   - Extensive iteration until correct
3. **Reporting**: `cracking-shells-playbook/instructions/reporting.instructions.md`
   - Concise, actionable reports
   - Clear structure and formatting
   - Evidence-based conclusions

## Quality Requirements

**Graphs**: Must be publication-quality and scientifically sound:
- Error bars (±1 SD) on all data points
- P-values annotated where comparisons are made
- Professional styling (clear labels, legends, appropriate colors)
- Suitable for inclusion in user-facing README

**Reports**: Concise and engineering-focused:
- Clear conclusions backed by statistical evidence
- Minimal statistical jargon
- Actionable insights for users
- No lengthy academic-style statistical analysis sections

## Task Management

Note: I have cleared your task list. Please regenerate tasks based on the updated plan (v1) to track your progress through the 4 phases.

## Expected Outcome

By completion, we should have:
1. ✅ Statistically rigorous performance comparison graphs with error bars and p-values
2. ✅ Raw measurement data persisted for transparency and reproducibility
3. ✅ Constant overhead benchmark validating the ~1.8 µs claim
4. ✅ cProfile comparison benchmark
5. ✅ Concise, user-focused documentation suitable for README
6. ✅ All work meeting organizational standards for rigor and quality

Proceed systematically, starting with Task 1 (update the investigation report to v1), then Task 2 (execute the 4 phases).
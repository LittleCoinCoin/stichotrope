
1. **Context**: References the merge commit and completed tasks
2. **Your tasks**: Numbered list of specific actions with file references
3. **Constraints**: References to org standards and specific requirements
4. **Important notes**: Critical warnings and clarifications
5. **Expected deliverables**: Clear success criteria


Example:

```
# Remote Agent Takeover Instructions

**Context**: The `milestone/1.2-ci-cd-pipeline` branch has been merged into `dev` with commit `abc123`. All tasks for Milestone 1.2 have been completed.

**Your tasks**:
1. Deploy the CI workflow file to `.github/workflows/ci.yml`.
2. Verify that all CI jobs pass on GitHub Actions.

**Constraints**:
- Must use the workflow file in `__report__/Phase_1/milestone_2/ci-workflow.md`.
- Follow the org's standards about analytic behavior (read & study before actuation on the codebase) `cracking-shells-playbook/instructions/analytic-behavior.instructions.md`
- Follow the org's standards on work ethics (rigor and perseverance through challenges) `cracking-shells-playbook/instructions/work-ethics.instructions.md`
- Follow the org's testing standards `cracking-shells-playbook/instructions/testing.instructions.md`
- Do not make any changes to the workflow file.

**Important notes**:
- The workflow file must be deployed manually.
- You must use the secret `WORKFLOW_PAT` to authenticate with GitHub API to commit the workflow file.
- The CI jobs may take up to 30 minutes to complete.

**Expected deliverables**:
- The CI workflow file is deployed to `.github/workflows/ci.yml`.
- All CI jobs pass on GitHub Actions.

```
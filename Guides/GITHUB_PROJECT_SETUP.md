GitHub project board setup (manual + gh CLI)

This file explains how to convert the checklist into GitHub Issues and a Project board.

Prerequisites
- gh CLI installed and authenticated: `gh auth login`

Troubleshooting `gh` on Windows

- If `gh` is not found, install via winget (Windows 10/11):

```powershell
winget install --id GitHub.cli
```

- Or install via Chocolatey:

```powershell
choco install gh
```

- If you installed `gh` but PowerShell still says it's not found, restart your shell or log out/in so PATH updates apply.

- Authenticate after installation:

```powershell
gh auth login --web
```

This opens a browser and completes auth. You can verify with:

```powershell
gh auth status
```

Create issues automatically
1. From the repo root run (PowerShell):

```powershell
.
\scripts\create_issues.ps1
```

This script reads `.github/ISSUES_TEMPLATES.md` and creates issues labeled `todo`.

Create a project board (manual)
1. In GitHub, go to Projects → New Project (Beta) or use "Classic" projects depending on preferences.
2. Create columns: Backlog, In Progress, Review, Done.
3. Add issues created in the previous step to the Backlog column.

Automate project creation with gh (optional)
- The gh CLI can create classic project boards via GraphQL or REST but the command is non-trivial; for most teams, manual creation is sufficient.

Tips
- Consider adding labels like `feature`, `infra`, `bug`, `priority/low`, `priority/high`.
- Add assignees and milestones once team members are known.

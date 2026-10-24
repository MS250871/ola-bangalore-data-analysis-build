# Run in PowerShell from this folder. Requires git and GitHub CLI (winget install GitHub.cli), then: gh auth login
$repo = "ola-bangalore-data-analysis-build"
git init -b main
git add -A
git commit -m "Ola Bangalore data analysis: full project, case-study README, dashboards"
gh repo create $repo --private --source . --remote origin --push --description "Case study: Ola Bangalore rides analysis (103,024 bookings, July 2024) built with the gated Data Analysis Build workflow"
gh repo view $repo --web

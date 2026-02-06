---
description: Development workflow with automatic approvals for all commands
---
// turbo-all

## Development Workflow

This workflow runs all commands automatically without requiring manual approval.

### Common Tasks

1. Run the development server
```bash
python3 app.py
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Check git status
```bash
git status
```

4. Deploy changes
```bash
git add . && git commit -m "Update" && git push
```

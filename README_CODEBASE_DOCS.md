# Sliples Codebase Documentation Index

This directory contains comprehensive documentation of the Sliples test automation platform codebase exploration.

## 📚 Documentation Files

### 1. **EXPLORATION_SUMMARY.md** (233 lines, 7KB)
   **Start here for a quick overview**
   - Executive summary of findings
   - Architecture overview
   - Key findings and critical insights
   - The "Variables Gap" discovery
   - Statistics and quick reference
   - How to use the documentation

### 2. **CODEBASE_FINDINGS.txt** (811 lines, 27KB)
   **Detailed reference guide with file paths**
   - All file locations with full paths
   - Line numbers for each component
   - Code structure and organization
   - API endpoint documentation
   - Complete flow diagrams
   - Quick reference table of all files

### 3. **CODEBASE_ANALYSIS.md** (876 lines, 32KB)
   **Deep dive into architecture and implementation**
   - Detailed code examples and patterns
   - Database schema with field descriptions
   - Complete Pydantic model definitions
   - Frontend component implementation details
   - Step execution mechanisms
   - Parameter handling and variable capture

## 🔍 Quick Navigation

### By Topic

**Scenario Parsing & Storage**
- EXPLORATION_SUMMARY.md → Section: "Scenario Parsing"
- CODEBASE_FINDINGS.txt → Section 1: "Scenario/Feature File Parsing & Storage"
- CODEBASE_ANALYSIS.md → Section 1: "Scenario/Feature File Parsing & Storage"

**Test Step Execution**
- CODEBASE_FINDINGS.txt → Section 2: "Test Step Execution"
- CODEBASE_ANALYSIS.md → Section 2: "Test Step Execution"

**Environment Variables** ⚠️
- EXPLORATION_SUMMARY.md → Section: "The Variables Gap"
- CODEBASE_FINDINGS.txt → Section 3: "Environment Model & Variables"
- CODEBASE_ANALYSIS.md → Section 3: "Environment Model & Variables"

**Custom Steps**
- CODEBASE_FINDINGS.txt → Section 5: "Custom Steps"
- CODEBASE_ANALYSIS.md → Section 5: "Custom Steps"
- CODEBASE_FINDINGS.txt → Section 5.3: "Custom Step End-to-End Flow"

**Test Execution Flow**
- CODEBASE_FINDINGS.txt → Section 7: "Test Execution Flow (End-to-End)"
- CODEBASE_ANALYSIS.md → Section 7: "Test Execution Flow (End-to-End)"

**Frontend Implementation**
- CODEBASE_FINDINGS.txt → Section 4: "Frontend Implementation"
- CODEBASE_ANALYSIS.md → Section 4: "Frontend Implementation"

**Pages & Named Navigation**
- CODEBASE_FINDINGS.txt → Section 8: "Pages & Named Navigation"
- CODEBASE_ANALYSIS.md → Section 8: "Pages & Named Navigation"

### By File

**Look up a specific backend file:**
- CODEBASE_FINDINGS.txt → "FILES QUICK REFERENCE" section

**Need to understand test_executor.py:**
- CODEBASE_FINDINGS.txt → Section 2.1: "Test Executor Service"
- CODEBASE_ANALYSIS.md → Section 2.1: "Test Executor Service"

**Understanding custom step execution:**
- CODEBASE_FINDINGS.txt → Section 2.2 & 5.3
- CODEBASE_ANALYSIS.md → Section 2.2

## 🎯 Common Tasks

### "I need to implement variable support"
1. Read: EXPLORATION_SUMMARY.md → "The Variables Gap"
2. Reference: CODEBASE_FINDINGS.txt → Section 7.2
3. Implement: Follow the pattern shown in Section 9.2 (parameter capture)
4. Test: Verify against patterns in Section 2.2

### "I want to add a new builtin step"
1. Reference: CODEBASE_ANALYSIS.md → Section 2.1 (GherkinStepRegistry class)
2. Example: See any _step_* method in Section 2.1
3. Implementation: test_executor.py lines 86-275

### "I need to create a custom step"
1. Reference: CODEBASE_FINDINGS.txt → Section 5.3: "Custom Step End-to-End Flow"
2. Understand: How parameters are captured (Section 9.2)
3. Storage: CustomStep model in models/custom_step.py
4. Execution: test_executor.py _execute_custom_step_code()

### "I want to understand the database schema"
1. Start: CODEBASE_ANALYSIS.md → Section 3.1 (Environment Model)
2. Models: Sections 1.2, 3.1, 5.1, 7.3, 8.1
3. Relationships: Check "project" fields and foreign keys

### "I need to fix the Variables Gap"
1. Understand the gap: EXPLORATION_SUMMARY.md → Section: "The Variables Gap"
2. Locate the files:
   - Backend: /Users/ptrk/Agantis/sliples/backend/app/workers/tasks.py (line 120, 176)
   - Frontend: Already implemented correctly
3. Follow the data flow in CODEBASE_ANALYSIS.md → Section 7.2

## 📊 Key Statistics

- **Codebase**: 16 files analyzed, 4,100+ lines of relevant code
- **Backend**: 11 files (models, routes, services)
- **Frontend**: 5 files (components, pages, store, API types)
- **Database**: 7 core tables with relationships
- **API**: 20+ endpoints
- **Step Patterns**: 90+ built-in patterns + custom patterns

## 🔗 File Structure Map

```
/Users/ptrk/Agantis/sliples/
├── backend/app/
│   ├── models/
│   │   ├── environment.py (48 lines) - Variables field here!
│   │   ├── scenario.py (49 lines)
│   │   ├── custom_step.py (30 lines)
│   │   ├── test_run.py (79 lines)
│   │   └── page.py (80 lines)
│   ├── api/routes/
│   │   ├── parser.py (260 lines)
│   │   ├── environments.py (392 lines)
│   │   ├── steps.py (198 lines)
│   │   ├── runs.py (400+ lines)
│   │   └── test_session.py (300+ lines)
│   └── services/
│       ├── test_executor.py (968 lines) - Main execution logic
│       ├── interactive_executor.py (300+ lines)
│       └── workers/tasks.py (250+ lines) - THE GAP IS HERE (line 176)
└── frontend/src/
    ├── api/client.ts - Environment types
    ├── components/
    │   ├── EnvironmentForm.tsx (305 lines)
    │   └── KeyValueEditor.tsx (168 lines)
    ├── pages/Environments.tsx (354 lines)
    └── store/environments.ts (126 lines)
```

## 🚀 Getting Started

1. **First time exploring?** → Start with EXPLORATION_SUMMARY.md
2. **Need specific file info?** → Use CODEBASE_FINDINGS.txt as reference
3. **Understanding how it works?** → Read CODEBASE_ANALYSIS.md
4. **Implementing changes?** → Combine all three documents

## 📋 Key Findings Summary

### ✅ Fully Implemented
- Scenario parsing and storage
- Test step execution (20+ builtin handlers)
- Custom steps with parameter capture
- Pages and named navigation
- Locale and timezone support
- Environment management (CRUD)
- Variable storage (DB + frontend UI)
- Interactive testing mode

### ⚠️ Gap Identified
- **Variables are NOT passed to test executor**
- **Location**: `/Users/ptrk/Agantis/sliples/backend/app/workers/tasks.py`
- **Line**: 176 (missing parameter in run_test_execution() call)
- **Status**: High priority for implementation

### 🔧 Easy Wins
1. Pass `environment.variables` to executor (1-line fix potential)
2. Inject variables into custom step execution namespace
3. Add variable substitution support in builtin steps
4. Document variable usage in custom step editor

## 💡 Pro Tips

- **For custom steps**: Variables are captured via regex groups (Section 9.2)
- **For debugging**: Celery task logs are in execute_test_run() (Section 7.2)
- **For frontend**: Variables use KeyValueEditor component (consistent UI)
- **For patterns**: GherkinStepRegistry shows how to add new steps
- **For testing**: Interactive mode doesn't have the variables gap (already works)

## 📞 Quick Reference

| Need | Find In | Location |
|------|---------|----------|
| File paths | CODEBASE_FINDINGS.txt | "FILES QUICK REFERENCE" |
| API endpoints | CODEBASE_ANALYSIS.md | Section 3.2, 5.2, 7.1 |
| Database schema | CODEBASE_ANALYSIS.md | All sections with Model |
| Code examples | CODEBASE_ANALYSIS.md | All sections marked with ``` |
| Execution flow | CODEBASE_FINDINGS.txt | Section 7.2 (ASCII diagram) |
| Variable handling | CODEBASE_FINDINGS.txt | Section 9 |
| Custom step example | CODEBASE_FINDINGS.txt | Section 9.2 |

---

**Documentation Created**: March 31, 2026  
**Codebase Analyzed**: /Users/ptrk/Agantis/sliples/  
**Total Documentation**: 1,920 lines across 3 files  
**Analysis Coverage**: 100% of key files and functionality

# Future Roadmap

This document outlines potential future enhancements for Agent Evaluation Assistant.

### 1. PyPI Package Distribution

**Current:** Users clone repo and install with `pip install -e ./sdk`  
**Future:** `pip install agent-evaluation-sdk`

**Benefits:**
- Simpler installation
- Version management
- Standard Python workflow

**Timeline:** Post-competition

---

### 2. A2A Protocol Support

**What:** Expose evaluation as an Agent-to-Agent (A2A) service

**Use Cases:**
- Centralized evaluation service for multiple teams
- Cross-framework support (ADK, LangChain, CrewAI)
- Multi-agent orchestration scenarios
- Enterprise-wide evaluation standards

**Architecture:**
```
Multiple Agents → (A2A) → Centralized Evaluation Service
                           ↓
                    Cloud Logging, Trace, BigQuery
```

**Benefits:**
- One evaluation service for entire organization
- Framework-agnostic
- Centralized metrics and monitoring

**Considerations:**
- Network latency (~50-200ms per interaction)
- Requires service deployment and maintenance
- Good for enterprise, overkill for individual developers

**Timeline:** Post-competition, based on user feedback

---

### 3. Assistant Enhancements

#### Option A: GitHub Integration
**What:** Assistant creates PRs in user's repository

**Flow:**
```
User: "Set up evaluation in github.com/user/my-repo"
Assistant: [authenticates, creates branch, adds files, opens PR]
```

**Benefits:** Fully automated, version controlled

#### Option B: Agent Engine Deployment
**What:** Deploy assistant as hosted service

**Benefits:** 
- No local installation
- Always available
- Web-based chat interface

**Limitation:** Can't perform local file operations (generates configs instead)

**Decision:** Keeping local for now because file automation is core value

---

### 4. Framework Expansion

**Current:** ADK (plugin) + Custom agents (wrapper)

**Future Support:**
- LangChain agents (wrapper)
- CrewAI agents (wrapper)
- Any framework with agent pattern (wrapper)

**Strategy:** Universal wrapper + framework-specific optimizations

---

## Design Philosophy

**Local-First:** Assistant runs locally for automated file operations, code validation, and privacy.

**Dual Integration:** Plugin for ADK (native), wrapper for everything else (custom agents, LangChain, CrewAI).

**A2A for Scale:** Current architecture optimized for individual developers. A2A makes sense for enterprise/multi-team scenarios with centralized services.

---

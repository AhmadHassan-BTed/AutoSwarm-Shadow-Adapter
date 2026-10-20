<!-- ============================================================
  ██████╗  █████╗  ██████╗    ███████╗██████╗ ███████╗ ██████╗
  ██╔══██╗██╔══██╗██╔════╝    ██╔════╝██╔══██╗██╔════╝██╔════╝
  ██║  ██║███████║██║  ███╗   ███████╗██████╔╝█████╗  ██║
  ██║  ██║██╔══██║██║   ██║   ╚════██║██╔═══╝ ██╔══╝  ██║
  ██████╔╝██║  ██║╚██████╔╝   ███████║██║     ███████╗╚██████╗
  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚══════╝╚═╝     ╚══════╝ ╚═════╝

  AI AGENT — IMPLEMENTATION SPECIFICATION
  ═══════════════════════════════════════════════════════════════
  Base Class  : opc.layer3_agent.adapters.base.ExternalAgentAdapter
  Registry    : ADAPTER_CLASSES["shadow"] = ShadowModeAdapter
  See full architecture spec: docs/architecture.md
  ============================================================ -->

<div align="center">

# AutoSwarm-Shadow-Adapter
### Non-Blocking Human-in-the-Loop (HITL) & BYOC Infrastructure for AutoSwarm

**AI Agent Employees For Your Compan -- The Carbon-Silicon Continuum: Real Humans & Remote PCs as First-Class AutoSwarm Employees**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/AutoSwarm-shadow-adapter/)
[![PyPI Package](https://img.shields.io/badge/pypi-v0.1.0--ready-0c111b?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/AutoSwarm-shadow-adapter/)
[![MIT License](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)

[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/portal-React%2019%20%2B%20Tailwind-61DAFB?style=flat-square&logo=react&logoColor=black)](https://github.com/AhmadHassan-BTed/AutoSwarm-Shadow-Adapter)
[![SQLite WAL](https://img.shields.io/badge/storage-SQLite%20WAL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/wal.html)
[![JWT Auth](https://img.shields.io/badge/auth-JWT%20%2B%20bcrypt-F59E0B?style=flat-square)](https://jwt.io)
[![Zero Core Modifications](https://img.shields.io/badge/core%20modifications-zero-ef4444?style=flat-square)](https://github.com/AhmadHassan-BTed/AutoSwarm-Shadow-Adapter)
[![AutoSwarm Ecosystem](https://img.shields.io/badge/ecosystem-AutoSwarm-6366f1?style=flat-square)](https://github.com/HKUDS/AutoSwarm)

<br/>

> Built for [AutoSwarm](https://github.com/HKUDS/AutoSwarm) | Zero Core Modifications | Production Release v0.1.0

</div>

---

## What is AutoSwarm-Shadow-Adapter?

`AutoSwarm-shadow-adapter` is a high-concurrency **Temporal Bridge** for AutoSwarm. It allows AutoSwarm agentic DAGs to pause non-blockingly when a role requires human sign-off (Carbon) or remote GPU execution (Silicon BYOC), without causing engine timeouts or stalling parallel branches.

1. **Non-Blocking Intercept**: Intercepts AutoSwarm task execution in `<50ms`, parks the task in an isolated SQLite WAL database, and releases execution threads immediately with `AWAITING_HUMAN`.
2. **Contractor & Silicon Worker Portal**: Provides a dedicated, secure React 19 UI and REST API (`shadow-serve`) for human reviewers and remote workers (`shadow-worker`).
3. **Consolidated Corporate Brain**: Automatically packages ancestor deliverables, structured markdown briefs (`brief_md`), and uploaded file artifacts (`CorporateArtifacts`) for downstream context inheritance.
4. **Canonical State Subordination**: Resumes AutoSwarm's native `store.db` state machine (`delegation_work_items.phase`) instantly when deliverables are submitted.
5. **Symbiotic Architecture**: Functions as an independent, non-invasive extension that plugs into AutoSwarm's external agent registry (`ADAPTER_CLASSES["shadow"]`) with zero core repository modifications.

---

## Appoint AI Agents & Hybrid Employees to

### Automate Freelance & Multiple Jobs (Overemployment Engine)
*Juggling multiple client contracts or simultaneous full-time roles?*
Turn yourself from an individual contributor into an agency of one. Assign the heavy lifting—writing programs, reviewing complex technical architectures, and completing routine software assignments—to your remote silicon employees. You sit at the top of the hierarchy as the sole human reviewer. Deliver 5x the output to multiple clients simultaneously, approving deliverables asynchronously on your own schedule without burning out.

### Augment Vacant or Overloaded Roles
*Lost a developer? Legal reviewer on leave? Analyst at capacity?*
AI agents perform 90% of preliminary work (research, code generation, test suite execution, drafting). Shadow Adapter routes only the final approval decision to an available human manager.

### Run Your Entire Business on AI Autopilot
*One operator with the leverage of a 10-person team.*
Your AI Research Analyst, Dev Team, Marketing Lead, and Legal Counsel operate 24/7. Shadow Adapter queues strategic checkpoints for your review without stalling non-dependent work streams.

### Ensure Enterprise Regulatory Compliance
In finance, healthcare, legal, and security, frameworks (SOC 2, ISO 27001, GDPR) mandate human sign-off. Shadow Adapter records immutable audit events with timestamps and contractor attribution for complete compliance verification.
---

## Feature Comparison

| Capability | Standard AutoSwarm | AutoSwarm + Shadow Adapter |
|:---|:---|:---|
| **Human response time > 900s** | Engine crash (timeout failure) | **Zero timeouts (unlimited duration)** |
| **System restart resilience** | State lost | **Persisted in isolated SQLite WAL DB** |
| **Multi-user access control** | Local user only | **Multi-user queue with JWT auth** |
| **File attachments** | Text only | **Up to 5 files, 50MB payload** |
| **Audit log compliance** | Basic engine log | **Immutable timeline with user attribution** |
| **Iterative rework loop** | Manual intervention | **Built-in `rework_requested` state transition** |

---

## How It Works

```mermaid
flowchart LR
    subgraph Engine ["AutoSwarm Agentic DAG Engine"]
        DAG["Multi-Agent DAG Execution\n(Parallel AI Tasks)"]
    end

    subgraph Adapter ["Shadow Mode Plugin"]
        SA["ShadowModeAdapter\n(Non-blocking Intercept < 50ms)"]
    end

    subgraph Store ["Isolated Persistence"]
        DB[("SQLite WAL Store\nshadow_tasks.db")]
    end

    subgraph Portal ["Human Operations"]
        ReactApp["React 19 Human Portal\n(JWT Authenticated)"]
        HumanReviewer["Human Contractor / Reviewer"]
    end

    subgraph ResumeLayer ["DAG Unblock & Resume"]
        OPCStore[("AutoSwarm Engine Store\nstore.db (WAL Mode)")]
        UnblockNode(["Downstream DAG Nodes\nResume Automatically"])
    end

    DAG -->|1. Intercept human-backed task| SA
    SA -->|2. Park task record| DB
    SA -->|3. Return AWAITING_HUMAN and release thread| DAG
    DB <-->|4. Query pending queue & Submit deliverable| ReactApp
    HumanReviewer <-->|5. Review brief & attach files| ReactApp
    ReactApp -->|6. Submit deliverable via REST API| SA
    SA -->|7. Write Phase.APPROVED to store| OPCStore
    OPCStore -->|8. Native Phase Hooks Trigger| UnblockNode

```

---

## User Workflow & Execution Pipeline

1. **Task Decomposing & Assignment**: When a user launches an AutoSwarm session (e.g. `opc chat --mode company "Build feature X"`), AutoSwarm's Manager AI creates work items and assigns them to configured role seats (e.g., `senior_developer`, `legal_counsel`).
2. **Shadow Intercept (<50ms)**: Any role assigned `preferred_external_agent: shadow` is intercepted by `ShadowModeAdapter`. The adapter parses project goals, compiles a markdown task brief (`TaskBriefBuilder`), parks a record in `shadow_tasks.db`, and returns `AWAITING_HUMAN` to AutoSwarm. Execution threads release immediately so parallel DAG tasks continue without timing out.
3. **Task Claiming**:
   - **Human Contractor**: Logs into the Contractor Portal at `http://localhost:8800`, claims the pending task, and opens the interactive `TaskWorkspace`.
   - **Silicon BYOC Worker**: A remote GPU node running `shadow-worker --role senior_developer` polls the API, claims the task, and executes inference on its local model.
4. **Deliverable Submission**: The worker reviews upstream subagent context, writes solution notes, and attaches deliverable files (up to 5 files / 50MB payload cap). Files are indexed into `CorporateArtifacts` with SHA-256 integrity hashes.
5. **DAG Resumption**: `OpcResumeRepository` updates `delegation_work_items.phase` in AutoSwarm's host `store.db`. AutoSwarm wakes downstream DAG nodes, passing the uploaded artifacts forward.

For complete documentation:
- 📖 **[Step-by-Step Execution Flow Walkthrough](docs/execution_flow.md)**
- 🛠️ **[Detailed Implementation & Setup Guide](docs/implementation_guide.md)**
- 📜 **[Changelog & Compatibility Matrix](CHANGELOG.md)**

---

## Symbiotic Integration & Quick Start

`AutoSwarm-shadow-adapter` is built to run as a **true symbiont** with AutoSwarm. You can run the portal server embedded in your main Python process or as a standalone CLI sidecar.

### Step 1: Install Package

```bash
pip install AutoSwarm-shadow-adapter

```

### Step 2: Register & Launch Embedded (Zero Extra Commands)

In your main AutoSwarm application entry point (e.g., `main.py`), register the adapter and launch the Human Portal server concurrently in a background thread:

```python
# main.py (Your AutoSwarm application entry point)
from opc.layer3_agent.adapters.registry import ADAPTER_CLASSES
from shadow_adapter import ShadowModeAdapter, start_server_in_thread

# 1. Register "shadow" mode into AutoSwarm's adapter registry
ADAPTER_CLASSES["shadow"] = ShadowModeAdapter

# 2. Launch Human Web Portal concurrently on port 8800 (single process)
start_server_in_thread(port=8800)

# 3. Launch your AutoSwarm DAG pipeline as normal!

```

### Step 3: Configure Target Roles

In your AutoSwarm organization config (`.opc/config/company_orgs/company_config.yaml`), set `preferred_external_agent: shadow` for human-backed roles:

```yaml
# .opc/config/company_orgs/company_config.yaml
roles:
  legal_counsel:
    title: "Human Legal Counsel"
    execution_strategy: external
    preferred_external_agent: shadow  # <-- Intercepted by Shadow Adapter

  senior_architect:
    title: "Human Senior Architect"
    execution_strategy: external
    preferred_external_agent: shadow  # <-- Intercepted by Shadow Adapter

```

### Alternative: Launch via CLI Sidecar

If you prefer running the Web Portal in a separate terminal or Docker container:

```bash
shadow-serve --port 8800

```

* **React Human Web Portal:** `http://localhost:8800`
* **REST API Base:** `http://localhost:8800/api/v1`

---

## Distributed Silicon Workforce (Bring Your Own Compute - BYOC)

The **`shadow-worker`** daemon allows remote PCs, GPU workstations, and dedicated cloud nodes to act as specialized silicon employees. Each remote node runs its assigned role on its own local model or API key without modifying the central AutoSwarm engine.

### Launch Remote Compute Nodes (3-PC Distributed Example)

#### 1. Remote GPU Workstation (Role: Senior Developer -> Local Ollama)

```bash
export OLLAMA_HOST="http://localhost:11434"
shadow-worker \
  --server-url "[http://192.168.1.100:8800](http://192.168.1.100:8800)" \
  --username "dev_node_1" \
  --password "secure_pass_1" \
  --role "senior_developer" \
  --provider "ollama" \
  --model "llama3.3:70b"

```

#### 2. Remote Enterprise Server (Role: Legal Counsel -> Enterprise Claude API)

```bash
export LOCAL_ANTHROPIC_KEY="sk-ant-api03-enterprise-key..."
shadow-worker \
  --server-url "[http://192.168.1.100:8800](http://192.168.1.100:8800)" \
  --username "legal_node_2" \
  --password "secure_pass_2" \
  --role "legal_counsel" \
  --provider "anthropic" \
  --model "claude-3-5-sonnet-20241022"

```

#### 3. Remote Tester Machine (Role: QA Tester -> OpenAI GPT-4o)

```bash
export LOCAL_OPENAI_API_KEY="sk-proj-openai-key..."
shadow-worker \
  --server-url "[http://192.168.1.100:8800](http://192.168.1.100:8800)" \
  --username "qa_node_3" \
  --password "secure_pass_3" \
  --role "qa_tester" \
  --provider "openai" \
  --model "gpt-4o"

```

### Programmatic Python SDK Usage

You can also embed `ShadowWorker` into custom Python pipelines on remote nodes:

```python
import asyncio
from shadow_adapter import ShadowWorker

# Custom task handler executing local agent pipeline
async def my_local_agent(task: dict) -> str:
    # Query your local GPU, private database, or custom agent model
    return f"Processed task '{task['title']}' on local node."

worker = ShadowWorker(
    server_url="[http://192.168.1.100:8800](http://192.168.1.100:8800)",
    username="custom_node_01",
    password="password123",
    role="legal_counsel",
    custom_handler=my_local_agent,
)

asyncio.run(worker.run_forever())

```

---

## The Consolidated Corporate Brain (Knowledge Graph)

A real company doesn't just pass text strings—employees share documents, reports, and data. `AutoSwarm-shadow-adapter` acts as the **Central Nervous System** for your AI and Human workforce by maintaining a centralized artifact registry.

### 1. The Shared Artifact Registry

When a Silicon or Carbon employee finishes a task, their deliverables (PDFs, CSVs, code files) are saved to the centralized `CorporateArtifacts` registry. This creates an indexed, searchable corporate memory for your entire DAG.

### 2. Hierarchical Context Injection

The adapter dynamically parses your AutoSwarm `company_config.yaml` to understand your corporate hierarchy. When a downstream Manager receives a task to "Review the Analyst's work," the adapter automatically packages and injects the Analyst's upstream artifacts directly into the Manager's workspace (via the React Portal or the `ShadowWorker` API payload).

### 3. Role-Based Inheritance

Employees natively inherit the context of the workers below them. A Human Legal Director reviewing a contract doesn't just get a text summary—they are handed the exact `.docx` file the remote AI Drafter uploaded 5 minutes prior.

---

## Architecture Deep-Dive

All detailed technical specifications are decoupled from this overview:

* **[Architecture Specification & Implementation Contracts](https://www.google.com/search?q=docs/architecture.md%231-core-architecture-contracts)**
* **[Technical Lifecycle & Sequence Diagram](https://www.google.com/search?q=docs/architecture.md%233-technical-lifecycle--sequence)**
* **[State Machine Integration Diagram](https://www.google.com/search?q=docs/architecture.md%234-state-machine-integration)**
* **[Database Schemas & Tables (`shadow_tasks.db`)](https://www.google.com/search?q=docs/architecture.md%236-database-schema-specification-shadow_tasksdb)**

---

## Configuration Reference

| Variable | Default Value | Required | Description |
| --- | --- | --- | --- |
| `SHADOW_JWT_SECRET` | None | **Yes** | Secret key for signing JWT tokens (min 32 chars). |
| `SHADOW_DB_PATH` | `./shadow_tasks.db` | No | Path for the isolated Shadow SQLite database. |
| `SHADOW_OPC_STORE_PATH` | `.opc/projects/default/store.db` | No | Path to AutoSwarm's `store.db` for WAL resume writes. |
| `SHADOW_UPLOAD_DIR` | `./shadow_uploads` | No | Directory for storing deliverable attachments. |
| `SHADOW_MAX_FILES_PER_SUBMISSION` | `5` | No | Max files permitted per submission. |
| `SHADOW_MAX_FILE_SIZE_MB` | `10` | No | Max allowed size per file in MB. |
| `SHADOW_MAX_TOTAL_UPLOAD_SIZE_MB` | `50` | No | Max total upload payload per submission in MB. |
| `SHADOW_API_PORT` | `8800` | No | Network port for FastAPI server and React SPA. |

---

## Development & Testing

```bash
# Run full anti-fragility & host integration test suite (55 tests)
# Enforces Concurrency, Property-Based Fuzzing, Black Hole Exception Trapping, and AutoSwarm Host Mutation Survival
pytest tests/ -v --cov=shadow_adapter --cov-report=term-missing

# Run engine simulator demo
python tests/mock_AutoSwarm_engine.py

```

---

**AutoSwarm-Shadow-Adapter** | Non-Blocking Human-in-the-Loop Layer for AutoSwarm

[GitHub Repository](https://github.com/AhmadHassan-BTed/AutoSwarm-shadow-adapter) | [PyPI Package](https://pypi.org/project/AutoSwarm-shadow-adapter/) | [Issue Tracker](https://github.com/AhmadHassan-BTed/AutoSwarm-shadow-adapter/issues) | [Architecture Spec](https://www.google.com/search?q=docs/architecture.md)

---

<p align="center">
  <em> Thanks for visiting 🖤 Build for AutoSwarm Community</em><br><br>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.AutoSwarm&style=for-the-badge&color=00d4ff"
  alt="Views">
</p>

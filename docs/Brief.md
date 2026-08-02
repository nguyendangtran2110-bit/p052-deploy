# PROJECT BRIEF: OnBxrd (BDSO2O-10)

**Domain:** PropTech / Real Estate O2O | **Status:** In Review | **Target Delivery:** Q3/Q4 2026

---

## 1. Executive Summary & Problem Statement
**OnBxrd** is an intelligent virtual assistant designed to automate resident onboarding and post-handover customer care. Currently, this process is fragmented, highly manual, and paper-based, leading to poor resident experiences, delayed defect resolutions, and high operational overhead. MoveIn bridges this gap using Retrieval-Augmented Generation (RAG) and Human-in-the-Loop (HITL) workflows to provide seamless, accurate, 24/7 support.

## 2. Core Objectives & KPIs
* **Accelerate Onboarding:** Reduce average resident onboarding duration by **40%**.
* **Automate First-Line Support:** Handle **70%+** of routine resident inquiries automatically.
* **Faster Ticket Triage:** Cut defect ticket processing and routing time to **< 15 minutes**.
* **Ensure Accuracy:** Maintain **0% hallucination rate** on building policies via strict citations.

## 3. Core Capabilities
* **Personalized Onboarding Checklist:** Interactive, step-by-step task tracking tailored to each resident.
* **Grounded Q&A System:** Instant answers derived strictly from official resident handbooks with citations.
* **Smart Ticket Automation:** Automatically captures, categorizes, and routes maintenance requests to the right department.
* **Human-in-the-Loop (HITL):** A management dashboard allowing staff to review and approve critical AI commitments before they reach the resident.

## 4. Technical Architecture
* **AI & Logic:** **GPT-4o-mini** (LLM Engine), **LlamaIndex** (RAG/Knowledge Retrieval), **LangGraph** (Stateful Agent Orchestration).
* **System Stack:** **FastAPI** (Backend Service), **React** (Frontend/Dashboard UI), **PostgreSQL** (Database), **Render** (Cloud Infrastructure).

## 5. Scope & Risk Mitigation
* **In-Scope (Phase 1):** Guided checklists, RAG query answering, ticket management, HITL verification.
* **Out-of-Scope (Phase 1):** Direct utility payment gateways, IoT smart lock integrations.
* **Primary Risk:** AI hallucination on official building policies.
* **Mitigation Strategy:** Enforce strict LlamaIndex RAG parameters, require mandatory source citations for all answers, and mandate HITL approval for escalated or complex queries

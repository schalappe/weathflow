# Technical Documentation

Comprehensive technical documentation for the Money Map Manager project.

---

## 📚 Documentation Index

### For Developers

| Document | Description | Read Time |
|----------|-------------|-----------|
| **[Backend Architecture](./backend-architecture.md)** | Backend structure, services, and data flow | 25 min |
| **[Frontend Architecture](./frontend-architecture.md)** | Frontend components, state management, and patterns | 25 min |
| **[API Reference](./api-reference.md)** | Complete REST API endpoint documentation | 20 min |

### For Product Context

| Document | Description |
|----------|-------------|
| **[Product Mission](../product/mission.md)** | Product vision, users, and key features |
| **[Tech Stack](../product/tech-stack.md)** | Technology choices and conventions |
| **[Roadmap](../product/roadmap.md)** | Feature roadmap and future plans |

---

## 🚀 Quick Start

**New to the project?** Follow this path:

1. Read [Product Mission](../product/mission.md) (5 min) - understand what we're building and why
2. Read [Tech Stack](../product/tech-stack.md) (10 min) - learn the technologies used
3. Skim [Backend Architecture](./backend-architecture.md) and [Frontend Architecture](./frontend-architecture.md) - understand the codebase structure

**Total time:** ~45 minutes to be productive

---

## 📖 Documentation Structure

```text
docs/
├── technical/              # Technical documentation (you are here)
│   ├── README.md           # This file
│   ├── backend-architecture.md # Backend deep dive
│   ├── frontend-architecture.md # Frontend deep dive
│   └── api-reference.md    # API endpoints
│
└── product/                # Product documentation
    ├── mission.md          # Product vision
    ├── tech-stack.md       # Technology stack
    ├── roadmap.md          # Feature roadmap
    └── prd.md              # Product requirements
```

---

## 🔑 Key Concepts

### Architecture Pattern

Money Map Manager follows **Clean Architecture** principles:

- **Backend:** 4-layer architecture (Presentation → Application → Domain → Infrastructure)
- **Frontend:** Feature-based component organization with centralized state management

### Data Flow

```text
User → Frontend (Next.js)
    ↓
API Client (lib/api-client.ts)
    ↓
Backend API (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database (SQLite)
```

### Key Technologies

| Layer | Technology | Why? |
|-------|-----------|------|
| Frontend | Next.js 14+ | Modern React framework with App Router |
| Backend | FastAPI | Fast, type-safe Python web framework |
| Database | SQLite | Simple, local-first storage |
| AI | Claude Sonnet 4 | Best cost/quality for categorization |
| UI | shadcn/ui + Tailwind | Customizable, accessible components |

---

## 📝 Documentation Standards

All documentation follows these principles:

### 1. Audience-First

Each doc clearly states who it's for:

- **Architecture Docs:** Developers understanding the system
- **API Reference:** Frontend developers or API consumers

### 2. Progressive Disclosure

Start with essentials, add depth progressively:

- Quick start at the top
- Table of contents for navigation
- Detailed sections for deep dives

### 3. Code Examples

Show, don't just tell:

- Real code snippets from the codebase
- Complete examples with context
- Both success and error cases

### 4. Maintainability

Keep docs up-to-date:

- Last updated date at the top
- Link to related docs
- Version numbers for dependencies

---

## 📚 Additional Resources

### External Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### Community

- **GitHub Discussions:** Ask questions and share ideas
- **GitHub Issues:** Report bugs and request features
- **Pull Requests:** Contribute code and documentation

---

**Last Updated:** December 2025

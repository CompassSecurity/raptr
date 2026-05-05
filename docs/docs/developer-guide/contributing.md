# Contributing

Thank you for your interest in contributing to RAPTR! This page covers the workflow and requirements for submitting changes.

## General Note

RAPTR is designed to be a tool for everyone. When contributing new features, fields, database tables, or other changes, please ensure they are **universally applicable** to all RAPTR users — not tailored to a specific organization or workflow. If a change only makes sense for your particular use case, consider maintaining it in a **fork** of the repository rather than submitting it upstream.

## Getting Started

1. Fork and clone the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-feature main
   ```
3. Make your changes following the [backend](backend/index.md) and [frontend](frontend.md) development guides
4. Push your branch and open a pull request against `main`

## Branch Naming

Use descriptive branch names with a type prefix:

| Prefix | Purpose |
|--------|---------|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation |
| `refactor/` | Code refactoring |
| `chore/` | Maintenance tasks |

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add widget export functionality
fix: correct pagination offset in activity list
docs: update deployment guide for TLS config
refactor: extract activity validation into service
```

Include a scope when it helps clarify the change:

```
feat(backend): add bulk activity update endpoint
fix(frontend): handle empty assessment list state
```

## Pull Request Requirements

All pull requests must pass CI checks before merging. The CI pipeline runs automatically on every PR to `main`.

### Backend Checks

| Check | Command | What It Does |
|-------|---------|-------------|
| Lint | `uv run ruff check .` | Static analysis (errors, pyflakes, import sorting) |
| Format | `uv run ruff format --check .` | Code formatting consistency |
| Tests | `uv run pytest` | Unit and integration tests |

Run all checks locally before pushing:

```bash
cd backend
uv run ruff check .          # Lint
uv run ruff format --check . # Format check
uv run pytest                # Tests
```

To auto-fix lint and format issues:

```bash
uv run ruff check --fix .
uv run ruff format .
```

### Frontend Checks

| Check | Command | What It Does |
|-------|---------|-------------|
| Lint & Format | `bun run lint` | Biome linting and formatting |
| Type Check & Build | `bun run build` | TypeScript validation + production build |

Run all checks locally before pushing:

```bash
cd frontend
bun run lint         # Lint and format check
bun run build        # Type-check and build
```

To auto-fix lint and format issues:

```bash
bun run lint:fix
```

## Code Style

### Backend (Python)

- Follow existing patterns in the codebase
- Use type hints for all function signatures
- Follow the **Model → Schema → Service → Router** pattern for new endpoints
- Keep business logic in services, not in routers
- Ruff enforces style automatically — run `uv run ruff format .` before committing

### Frontend (TypeScript / Vue)

- Use `<script setup lang="ts">` for all components
- Import types from `@/types/utils` — never define local type aliases
- Import Zod schemas as `z<SchemaName>` from `@/types/zod.gen`, and use `toTypedSchema` from `@/utils/zodAdapter` (not `@vee-validate/zod`, which is Zod v3 only)
- Stores delegate API calls to services (stores manage state only)
- Use `loading` (not `isLoading`) for loading state variables
- Use composables (`usePagination`, `useModalWithData`) for common patterns
- Biome enforces style automatically — run `bun run lint:fix` before committing

## Pull Request Template

When you open a PR, a template will guide you through describing your changes. Make sure to:

- Describe **what** changed and **why**
- Note any breaking changes
- Confirm you've run the relevant checks locally
- Link related issues (e.g., `Closes #42`)

## Review Process

1. Open a PR against `main`
2. CI checks run automatically
3. A maintainer reviews the code
4. Address any feedback
5. Once approved and CI passes, the PR is merged

# Database & Testing

## Database

- **Production**: PostgreSQL (configured via `POSTGRES_*` env vars)
- **Development or small environments**: SQLite is supported (`DB_ENGINE=sqlite`)
- **ORM**: SQLAlchemy 2.0 with modern `Mapped` type annotations

### Schema Generation (No Migrations)

The project currently **does not use Alembic** or any migration tool. 

The database schema is automatically generated on application startup. In `app/core/startup.py`, the backend inspects all modules that inherit from `Base` and ensures the database tables exist:

```python
Base.metadata.create_all(bind=engine)
```

Because of this, destructive changes (like dropping a column or renaming a table) require manual database intervention if applied to an existing production database.

### Session Management

Database sessions are managed via FastAPI's dependency injection system, ensuring a session is opened when a request begins and closed when it finishes. Always inject `Session = Depends(get_session)` into your routers, and explicitly pass it down to your services.

```python
from app.db.session import get_session

@router.get("/")
def my_endpoint(session: Session = Depends(get_session)):
    return my_service(session)
```

## Database Schema

Entity-relationship diagram of all SQLAlchemy models in `app/models/`. The diagram is split into three sections: **Core** (assessment workflow), **Templates** (reusable configuration), and **Reference Data** (MITRE ATT&CK).

All models inherit from `Base`, which provides audit fields (`created_by`, `created_at`, `updated_by`, `updated_at`) — these are omitted from the diagram for clarity.  Models using `SoftDeleteMixin` also have `deleted`, `deleted_at`, and `deleted_by` fields.

```mermaid
erDiagram
    %% ──────────────────────────────────────────────
    %% CORE — Assessment Workflow
    %% ──────────────────────────────────────────────

    User {
        uuid id PK
        string email UK
        UserRole role
        bool mfa_verified
        string mfa_secret
        string hashed_password
        bool disabled
        datetime last_login_at
        datetime last_logout_at
    }

    Assessment {
        uuid id PK
        string name
        string description
        AssessmentType assessment_type
        json default_evaluation_templates
    }

    Acl {
        uuid id PK
        uuid user_id FK
        uuid assessment_id FK
        AclRole assessment_role
    }

    ActivityGroup {
        uuid id PK
        uuid assessment_id FK
        string name
        bool visible
        bool is_default
        int activity_group_position
    }

    Activity {
        uuid id PK
        uuid assessment_id FK
        uuid activity_group_id FK
        string name
        string mitre_tactic
        string mitre_technique
        string provider
        ActivityPriority priority
        ActivityState state
        bool visible
        int activity_position
        json linked_knowledge_base_articles
    }

    ActivityEvaluation {
        uuid id PK
        uuid activity_id FK
        EvaluationResult logged_evaluation
        EvaluationResult alerted_evaluation
        EvaluationResult prevented_evaluation
        EvaluationResult stakeholder_notified_evaluation
        int activity_coverage_score
    }

    ActivityEvaluationDynamicQuestions {
        uuid id PK
        uuid activity_evaluation_id FK
        uuid evaluation_template_id FK
        string data
        EvaluationResult evaluation_result
        int position
    }

    ActivityHistory {
        uuid id PK
        uuid activity_id FK
        int version
        datetime saved_at
        uuid saved_by_id FK
        json snapshot
    }

    Tag {
        uuid id PK
        uuid assessment_id FK
        string name
        string color
    }

    Asset {
        uuid id PK
        uuid assessment_id FK
        string name
        string icon
        json properties
    }

    File {
        uuid id PK
        uuid activity_id FK
        string filename
        FileType content_type
        bytes file_content
        int size
        FileCategory category
    }

    KnowledgeBase {
        uuid id PK
        string name UK
        string mitre_technique_id
        json content
    }

    %% ──────────────────────────────────────────────
    %% TEMPLATES — Reusable Configuration
    %% ──────────────────────────────────────────────

    EvaluationTemplate {
        uuid id PK
        string name UK
        string evaluation_criteria
        string description
    }

    ReportTemplate {
        uuid id PK
        string filename
        ReportTemplateFormat format
        bytes template_content
    }

    CampaignTemplate {
        uuid id PK
        string name UK
        string description
    }

    CampaignTemplateItem {
        uuid id PK
        uuid campaign_template_id FK
        int position
        string item_type
        uuid activity_group_template_id FK
        uuid activity_template_id FK
    }

    ActivityGroupTemplate {
        uuid id PK
        string name UK
        string description
    }

    ActivityTemplate {
        uuid id PK
        string name
        string mitre_tactic
        string mitre_technique
        string provider
        string priority
        json linked_knowledge_base_articles
    }

    %% ──────────────────────────────────────────────
    %% REFERENCE DATA — MITRE ATT&CK
    %% ──────────────────────────────────────────────

    Tactic {
        uuid id PK
        string mitre_id UK
        string name
        string url
    }

    Technique {
        uuid id PK
        string mitre_id UK
        string name
        string url
    }

    %% ──────────────────────────────────────────────
    %% RELATIONSHIPS
    %% ──────────────────────────────────────────────

    %% Core
    User ||--o{ Acl : "has roles"
    Assessment ||--o{ Acl : "grants access"
    Assessment ||--o{ ActivityGroup : "contains"
    Assessment ||--o{ Activity : "contains"
    Assessment ||--o{ Tag : "has"
    Assessment ||--o{ Asset : "has"
    ActivityGroup ||--o{ Activity : "groups"
    Activity ||--o| ActivityEvaluation : "has evaluation"
    Activity ||--o{ File : "has files"
    Activity ||--o{ ActivityHistory : "has history"
    ActivityEvaluation ||--o{ ActivityEvaluationDynamicQuestions : "has questions"
    ActivityEvaluationDynamicQuestions }o--|| EvaluationTemplate : "uses template"
    User ||--o{ ActivityHistory : "saved by"

    %% Many-to-many (via association tables)
    Activity }o--o{ Tag : "activity_tag"
    Activity }o--o{ Asset : "activity_asset (role-based)"

    %% Templates
    CampaignTemplate ||--o{ CampaignTemplateItem : "contains"
    CampaignTemplateItem }o--o| ActivityGroupTemplate : "references"
    CampaignTemplateItem }o--o| ActivityTemplate : "references"
    ActivityGroupTemplate }o--o{ ActivityTemplate : "activity_template_activity_group"

    %% MITRE
    Tactic }o--o{ Technique : "technique_tactic"
```

## Association Tables

The following join tables implement many-to-many relationships:

| Table | Links | Extra columns |
|-------|-------|---------------|
| `activity_tag` | Activity ↔ Tag | — |
| `activity_asset` | Activity ↔ Asset | `role` (source, target, tool, log_source, prevention_source, alert_source, stakeholder_notification_source) |
| `technique_tactic` | Technique ↔ Tactic | — |
| `activity_template_activity_group` | ActivityTemplate ↔ ActivityGroupTemplate | `position` |

## Mixins

| Mixin | Used by | Fields added |
|-------|---------|-------------|
| `SoftDeleteMixin` | Activity, ActivityGroup, Tag, Asset | `deleted`, `deleted_at`, `deleted_by` |

## Testing

The backend test suite runs against an isolated, in-memory SQLite database (`sqlite://`), completely separate from your development or production data.

```bash
uv run pytest              # Run all tests
uv run pytest tests/test_assessment.py  # Run specific test file
uv run pytest -v           # Verbose output
```

??? bug "AI Slop"
    Full transparency: All, I mean ALL, tests are AI generated. Without AI, there would probably be no tests, since I couldn't be bothered with writing tests. The effectiveness and coverage of these tests must be proven in the future.

### Pytest Fixtures

The test environment provides several crucial fixtures automatically (defined in `tests/conftest.py`):

- **`session`**: Provides an active SQLAlchemy session connected to the empty in-memory test database. Use this to seed test data or query results directly.
- **`client`**: A `TestClient` instance that has its `get_session` dependency overridden to use the test database above.
- **Auth Fixtures**: Pre-built users (`test_admin_user`, `test_regular_user`, `test_disabled_user`) and their corresponding ready-to-use API headers (`auth_headers_admin`, `auth_headers_regular`).

**Example Test:**
```python
def test_create_widget(client: TestClient, auth_headers_admin: dict):
    response = client.post(
        "/api/v1/widgets/",
        json={"name": "Test Widget"},
        headers=auth_headers_admin
    )
    assert response.status_code == 200
```

## Linting and Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting:

```bash
uv run ruff check .        # Lint (errors, pyflakes, import sorting)
uv run ruff check --fix .  # Lint with auto-fix
uv run ruff format .       # Format code
uv run ruff format --check .  # Check formatting without changes
```

Ruff configuration in `pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["E", "F", "I"]   # Error, Pyflakes, isort
ignore = ["E501"]           # Line length not enforced
```

All linting and format checks run automatically in CI on pull requests.

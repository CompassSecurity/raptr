# Templates

Templates are reusable blueprints managed at the system level — outside of any single assessment. They allow organizations to maintain a library of standardized content that can be [imported into assessments](assessments.md#importing-templates-and-campaigns) to avoid starting from scratch.

Templates are typically populated via [seeding](administration.md#seeding-data) from external sources such as the Atomic Red Team library or a custom organization repository.

## Activity Template

An **activity template** is a reusable blueprint for creating activities. It contains pre-filled values for MITRE mapping, expected outcomes, rationale, actions, requirements, and notes — everything needed to describe a specific attack technique without having to write it from scratch each time.

When imported into an assessment, each activity template creates a new [activity](key_objects.md#activity) with all its fields pre-populated.

## Activity Group Template

An **activity group template** is a reusable collection of activity templates organized under a common name. When imported into an assessment, the group and all its activity templates are added together, preserving their order and organization.

This is useful for standardized scenarios that involve multiple related activities — for example, a "Credential Access" group template might bundle several credential dumping and brute force activity templates.

## Campaign Template

A **campaign template** is a pre-configured collection of activity group templates and individual activity templates that can be imported into an assessment in bulk. Campaigns allow you to reuse entire engagement plans without recreating activities from scratch.

Campaign templates contain ordered **items**, each of which references either an activity group template or an individual activity template. This is the fastest way to populate a new assessment with a full set of activities.

## Evaluation Template

An **evaluation template** defines a custom evaluation question or criterion that can be applied to activities. Templates are reusable across assessments and contain:

- A **name** identifying the template
- **Evaluation criteria**: the question to be answered (e.g., "Was the attack detected within SLA?")
- An optional **description** explaining the criteria

When an assessment is configured with [default evaluation templates](assessments.md#default-evaluation-templates), new activities automatically receive those evaluation questions. See [Evaluation and Reporting](evaluation.md) for how evaluation results are calculated.


## Report Template

A **report template** defines the output format and structure for [generated reports](evaluation.md#generating-a-report). Supported formats:

- **DOCX**: Microsoft Word documents
- **HTML**: Web-based reports

Report templates are managed at the system level and populated via [seeding](administration.md#custom-data). They are fully re-seeded each time — all existing report templates are deleted and replaced with the imported set.


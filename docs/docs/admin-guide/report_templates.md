# Report Templates

Report templates define the output format and structure for generated reports. RAPTR supports two formats: **DOCX** (Microsoft Word) and **HTML**. Both use Jinja2 templating syntax with access to the full assessment data.

Report templates are managed via [custom data seeding](custom_data.md#report-templates).

## Template Context

When a report is generated, RAPTR builds a `ReportContext` and passes all its fields as **top-level Jinja2 variables** to the template. The following sections document every available variable.

??? tip "Download `ReportContext` layer"
    You can download the `ReportContext` layer from the UI. See [Export Result as JSON](../user-guide/evaluation.md#json-export).

### Top-Level Variables

| Variable | Type | Description |
|---|---|---|
| `assessment` | [AssessmentInfo](#assessmentinfo) | Assessment metadata |
| `activities_grouped` | list of [ActivityGroupReport](#activitygroupreport) | Activities organized by group and ordered by position |
| `activities_flat` | list of [ActivityReport](#activityreport) | All activities in a flat sorted list. Sort order is chosen by the user during export |
| `statistics` | [AssessmentStatistics](#assessmentstatistics) | Assessment-level statistics — same data as the Statistics page in the UI |
| `generated_at` | datetime | Timestamp when the report was generated |
| `generated_by` | string | Email of the user who generated the report |
| `template_filename` | string | Filename of the template used |

---

## Data Reference

### AssessmentInfo

| Field | Type | Description |
|---|---|---|
| `id` | string | Assessment UUID |
| `name` | string | Assessment name |
| `description` | string | Assessment description |
| `assessment_type` | string | `"Purple Team"` or `"Red Team"` |

### ActivityGroupReport

| Field | Type | Description |
|---|---|---|
| `name` | string | Group name |
| `position` | int | Group position in the assessment |
| `is_default` | bool | Whether this is the default group |
| `activities` | list of [ActivityReport](#activityreport) | Activities in this group, sorted by position |

### ActivityReport

This is the most detailed data object — it contains everything about a single activity.

#### Identity & Metadata

| Field | Type | Description |
|---|---|---|
| `id` | string | Activity UUID |
| `name` | string | Activity name |
| `position` | int | Position within its group |
| `group_name` | string | Name of the parent group |
| `group_position` | int | Position of the parent group |
| `provider` | string or null | Template provider (e.g., "Custom", "ART") |
| `priority` | string or null | `"Critical"`, `"High"`, `"Medium"`, `"Low"` |
| `state` | string or null | `"Pending"`, `"In Progress"`, `"Waiting Blue"`, `"Waiting Red"`, `"Completed"`, `"Cancelled"` |
| `visible` | bool | Whether the activity is visible to Blue Team |

#### MITRE ATT&CK

| Field | Type | Description |
|---|---|---|
| `mitre_tactic` | string | Tactic ID or name as stored |
| `mitre_technique` | string | Technique ID as stored (e.g., "T1204.001") |
| `mitre_tactic_name` | string | Resolved tactic name (e.g., "Execution") |
| `mitre_technique_name` | string | Resolved technique name (e.g., "User Execution: Malicious Link") |

#### Timing

| Field | Type | Description |
|---|---|---|
| `start_time` | datetime or null | Activity start time |
| `end_time` | datetime or null | Activity end time |

#### Detail Fields (Markdown)

| Field | Type | Description |
|---|---|---|
| `rationale` | string or null | Why this activity is tested |
| `actions` | string or null | Step-by-step execution instructions |
| `requirements` | string or null | Environmental prerequisites |
| `notes` | string or null | Additional notes |

#### Expected Results (Red Team)

| Field | Type | Description |
|---|---|---|
| `expected_logging` | bool or null | Whether logging is expected |
| `expected_prevention` | bool or null | Whether prevention is expected |
| `expected_alert_creation` | bool or null | Whether an alert is expected |
| `expected_stakeholder_notification` | bool or null | Whether stakeholder notification is expected |
| `expected_severity` | string or null | Expected severity level |

#### Actual Results (Blue Team)

| Field | Type | Description |
|---|---|---|
| `logged` | bool or null | Whether the activity was logged |
| `log_time` | datetime or null | When logging was detected |
| `prevented` | bool or null | Whether the activity was prevented |
| `prevent_time` | datetime or null | When prevention occurred |
| `alerted` | bool or null | Whether an alert was triggered |
| `alert_severity` | string or null | Actual alert severity |
| `alert_time` | datetime or null | When the alert was triggered |
| `stakeholder_notified` | bool or null | Whether stakeholders were notified |
| `stakeholder_notification_severity` | string or null | Actual notification severity |
| `stakeholder_notification_time` | datetime or null | When the notification was sent |

#### Detection Notes (Markdown)

| Field | Type | Description |
|---|---|---|
| `log_notes` | string or null | Blue Team notes on logging |
| `alert_notes` | string or null | Blue Team notes on alerting |
| `prevent_notes` | string or null | Blue Team notes on prevention |
| `stakeholder_notification_notes` | string or null | Blue Team notes on stakeholder notification |

#### Related Entities

| Field | Type | Description |
|---|---|---|
| `tags` | list of dicts | `[{"name": "...", "color": "..."}]` |
| `sources` | list of dicts | Source assets: `[{"name": "...", "icon": "...", "properties": {...}}]` |
| `targets` | list of dicts | Target assets (same structure) |
| `tools` | list of dicts | Tool assets (same structure) |
| `log_sources` | list of dicts | Log source assets (same structure) |
| `prevention_sources` | list of dicts | Prevention source assets (same structure) |
| `alert_sources` | list of dicts | Alert source assets (same structure) |
| `stakeholder_notification_sources` | list of dicts | Notification source assets (same structure) |

#### Static Evaluation

| Field | Type | Description |
|---|---|---|
| `coverage_score` | int or null | Activity coverage percentage (0-100) |
| `logged_evaluation` | string or null | `"pass"`, `"fail"`, or `"n/a"` |
| `alerted_evaluation` | string or null | `"pass"`, `"fail"`, or `"n/a"` |
| `prevented_evaluation` | string or null | `"pass"`, `"fail"`, or `"n/a"` |
| `stakeholder_notified_evaluation` | string or null | `"pass"`, `"fail"`, or `"n/a"` |

#### Time-Based Evaluation

| Field | Type | Description |
|---|---|---|
| `event_to_alert_data` | string or null | Calculated time between event and alert (text) |
| `event_to_alert_result` | string or null | `"pass"`, `"fail"`, or `"n/a"` |
| `alert_to_stakeholder_data` | string or null | Calculated time between alert and notification (text) |
| `alert_to_stakeholder_result` | string or null | `"pass"`, `"fail"`, or `"n/a"` |

#### Severity-Based Evaluation

| Field | Type | Description |
|---|---|---|
| `alert_severity_data` | string or null | Expected vs actual alert severity (text) |
| `alert_severity_result` | string or null | `"pass"`, `"fail"`, or `"n/a"` |
| `stakeholder_notification_severity_data` | string or null | Expected vs actual notification severity (text) |
| `stakeholder_notification_severity_result` | string or null | `"pass"`, `"fail"`, or `"n/a"` |

#### Dynamic Evaluation Questions

| Field | Type | Description |
|---|---|---|
| `dynamic_questions` | list of [DynamicQuestionReport](#dynamicquestionreport) | Custom evaluation questions and answers |

#### Files / Attachments

| Field | Type | Description |
|---|---|---|
| `files` | list of [FileReport](#filereport) | Uploaded attachments with base64-encoded content |

### DynamicQuestionReport

| Field | Type | Description |
|---|---|---|
| `question` | string | The evaluation criteria text |
| `description` | string | Description of the criteria |
| `data` | string or null | The answer/data provided |
| `result` | string | `"pass"`, `"fail"`, or `"n/a"` |
| `position` | int | Display order |

### FileReport

| Field | Type | Description |
|---|---|---|
| `id` | string | File UUID |
| `filename` | string | Original filename |
| `content_type` | string | MIME type (e.g., `"image/png"`) |
| `size` | int | File size in bytes |
| `category` | string | `"red"` or `"blue"` |
| `data_base64` | string | Base64-encoded file content |

### AssessmentStatistics

The `statistics` variable contains the same data that powers the Statistics page in the RAPTR frontend. All metrics are computed over visible, non-deleted activities in visible, non-deleted groups.

| Field | Type | Description |
|---|---|---|
| `state_distribution` | list of [StateDistributionItem](#statedistributionitem) | Count of activities per state |
| `priority_breakdown` | list of [PriorityBreakdownItem](#prioritybreakdownitem) | Count of completed activities per priority |
| `average_coverage_score` | float or null | Average coverage score across completed activities |
| `average_coverage_scores_by_priority` | list of [PriorityAverageScoreItem](#priorityaveragescoreitem) | Average coverage score per priority level |
| `mitre_overall_tactic_scores` | list of [MitreOverallTacticScoreItem](#mitreoveralltacticscoreitem) | Aggregated detection scores per MITRE tactic |
| `mitre_tactic_scores` | list of [MitreTacticScoreItem](#mitretacticscoreitem) | Per-technique scores grouped by MITRE tactic |
| `mean_time_metrics` | list of [MeanTimeMetricsItem](#meantimemetricsitem) | Mean time to detect and respond, grouped by priority |
| `severity_accuracy` | list of [SeverityAccuracyItem](#severityaccuracyitem) | Expected vs actual alert severity confusion matrix |

### StateDistributionItem

| Field | Type | Description |
|---|---|---|
| `state` | string | Activity state (e.g., `"Completed"`, `"Pending"`) |
| `count` | int | Number of activities in this state |

### PriorityBreakdownItem

| Field | Type | Description |
|---|---|---|
| `priority` | string | Priority level (`"Critical"`, `"High"`, `"Medium"`, `"Low"`) |
| `count` | int | Number of completed activities at this priority |

### PriorityAverageScoreItem

| Field | Type | Description |
|---|---|---|
| `priority` | string | Priority level |
| `average_score` | float or null | Average coverage score for completed activities at this priority |

### MitreOverallTacticScoreItem

Aggregated detection scores for a single MITRE tactic across all its techniques. Scores are percentages (0-100).

| Field | Type | Description |
|---|---|---|
| `tactic` | string | Tactic display name (e.g., `"Execution - TA0002"`) |
| `overall_score` | float or null | Average coverage score |
| `expected_logged_score` | float or null | % of activities where logging was expected |
| `logged_score` | float or null | % where expected logging actually occurred |
| `expected_prevented_score` | float or null | % where prevention was expected |
| `prevented_score` | float or null | % where expected prevention actually occurred |
| `expected_alerted_score` | float or null | % where alerting was expected |
| `alerted_score` | float or null | % where expected alerting actually occurred |
| `expected_stakeholder_notified_score` | float or null | % where stakeholder notification was expected |
| `stakeholder_notified_score` | float or null | % where expected notification actually occurred |

### MitreTacticScoreItem

Groups techniques under a single tactic.

| Field | Type | Description |
|---|---|---|
| `tactic` | string | Tactic display name |
| `techniques` | list of [MitreTechniqueScoreItem](#mitretechniquescoreitem) | Per-technique scores |

### MitreTechniqueScoreItem

Same fields as [MitreOverallTacticScoreItem](#mitreoveralltacticscoreitem) but for a single technique.

| Field | Type | Description |
|---|---|---|
| `technique` | string | Technique display name (e.g., `"User Execution: Malicious Link - T1204.001"`) |
| `overall_score` | float or null | Average coverage score |
| `expected_logged_score` | float or null | % where logging was expected |
| `logged_score` | float or null | % where expected logging occurred |
| `expected_prevented_score` | float or null | % where prevention was expected |
| `prevented_score` | float or null | % where expected prevention occurred |
| `expected_alerted_score` | float or null | % where alerting was expected |
| `alerted_score` | float or null | % where expected alerting occurred |
| `expected_stakeholder_notified_score` | float or null | % where notification was expected |
| `stakeholder_notified_score` | float or null | % where expected notification occurred |

### MeanTimeMetricsItem

Mean time metrics grouped by priority. Times are in seconds.

| Field | Type | Description |
|---|---|---|
| `priority` | string | Priority level |
| `mean_time_to_detect_seconds` | float or null | Average seconds from activity start to alert |
| `mean_time_to_respond_seconds` | float or null | Average seconds from alert to stakeholder notification |

### SeverityAccuracyItem

Confusion matrix row showing how actual alert severities compare to the expected severity.

| Field | Type | Description |
|---|---|---|
| `expected_severity` | string | The expected severity level |
| `actual_informational` | int | Count of actual Informational alerts |
| `actual_low` | int | Count of actual Low alerts |
| `actual_medium` | int | Count of actual Medium alerts |
| `actual_high` | int | Count of actual High alerts |
| `actual_critical` | int | Count of actual Critical alerts |
| `actual_none` | int | Count of missed/unmatched alerts |

---

## DOCX Templates

DOCX templates use [docxtpl](https://docxtpl.readthedocs.io/) (Jinja2 for Word documents). You create a `.docx` file in Microsoft Word or LibreOffice and insert Jinja2 tags directly into the document text.

### Basic Syntax

Use standard Jinja2 syntax inside the document:

- **Variables**: `{{ assessment.name }}`
- **Loops**: `{%tr for activity in activities_flat %}` ... `{%tr endfor %}`
- **Conditionals**: `{% if activity.logged %}Yes{% else %}No{% endif %}`

### Markdown Fields

Markdown fields (rationale, actions, requirements, notes, detection notes) are automatically converted to styled Word content if the [required styles](#required-styles) are present in the template.

### Required Styles

Your DOCX template must define these named styles for markdown rendering to work correctly. If a style is missing, the content falls back to the "Normal" style.

**Paragraph styles** (applied to entire paragraphs via `w:pStyle`):

| Style Name | Used For |
|---|---|
| `Heading 1` through `Heading 6` | Markdown headings (`#` through `######`) |
| `List Bullet` | First-level bullet lists |
| `List Bullet 2` | Nested bullet lists |
| `List Number` | First-level numbered lists |
| `List Number 2` | Nested numbered lists |
| `Code` | Fenced code blocks |
| `TableBodyBullet` | Bullet lists inside table cells |

**Character styles** (applied to inline text runs via `w:rStyle`):

| Style Name | Used For |
|---|---|
| `Code-Inline` | Inline code (`` `text` ``). In Word, create this as a **Character** style (e.g. based on "Default Paragraph Font"). Word may display it as "Code-Inline Char" in the styles pane. |

### Table Rows

To loop over activities in a table, use the `{%tr %}` tag (table row):

```
| # | Activity Name | Tactic | Result |
|---|---|---|---|
{%tr for a in activities_flat %}
| {{ a.position }} | {{ a.name }} | {{ a.mitre_tactic_name }} | {{ a.coverage_score }}% |
{%tr endfor %}
```

### Images & Attachments

Images from markdown fields (pasted screenshots) are automatically embedded as inline images in the DOCX output, scaled to a maximum width of 5.5 inches. If an image cannot be loaded, a fallback italic text with the alt text is inserted.

??? bug "Attachments"
    Attachments are not automatically embedded in DOCX output. You need to manually extract them (e.g. from the [Assessment Export](../user-guide/assessments.md#exporting-an-assessment)) and send them to the customer.

---

## HTML Templates

HTML templates use standard [Jinja2](https://jinja.palletsprojects.com/) syntax with autoscaping enabled.

### The `tojson` Filter

The `| tojson` filter is the only custom Jinja2 filter available. It serializes a Python object to a JSON string for embedding in `<script>` tags:

```html
<script>
    const activities = {{ raw_activities | tojson }};
    const stats = {{ statistics | tojson }};
</script>
```

This custom filter is required instead of Jinja2's built-in because:

1. **Datetime handling** — the report context contains `datetime` objects (e.g. `generated_at`, activity timestamps) that Python's `json.dumps()` cannot serialize by default. The filter converts them to ISO 8601 strings.
2. **Autoescaping safety** — the rendering engine runs with `autoescape=True`, which would HTML-entity-encode raw JSON output (e.g. turning `"` into `&quot;`). The filter wraps the output in `Markup()` to prevent this, keeping the JSON valid inside `<script>` blocks.

All other formatting (dates, percentages, colors, etc.) should be handled client-side in JavaScript.

### Images in HTML

File attachments include base64-encoded content. To embed images:

```html
{% for file in activity.files %}
  {% if file.content_type.startswith('image/') %}
    <img src="data:{{ file.content_type }};base64,{{ file.data_base64 }}"
         alt="{{ file.filename }}" />
  {% endif %}
{% endfor %}
```

### Markdown in HTML

Unlike DOCX templates, markdown fields in HTML are **not** automatically converted. The raw markdown string is provided. To render markdown in HTML, either:

- Use a JavaScript markdown library (e.g., marked.js) in the rendered HTML
- Pre-process the markdown fields in the template with a custom filter

### Example HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ assessment.name }} - Report</title>
    <style>
        /* Your styles here */
    </style>
</head>
<body>
    <h1>{{ assessment.name }}</h1>
    <p>{{ assessment.description }}</p>
    <p>Generated: {{ generated_at | format_datetime }} by {{ generated_by }}</p>

    <h2>Summary</h2>
    <p>Coverage: {{ statistics.average_coverage_score | round(1) }}%</p>
    <p>Completed by Priority:</p>
    <ul>
    {% for item in statistics.priority_breakdown %}
        <li>{{ item.priority }}: {{ item.count }}</li>
    {% endfor %}
    </ul>

    <h2>Activities</h2>
    {% for group in activities_grouped %}
    <h3>{{ group.name }}</h3>
    <table>
        <tr><th>Activity</th><th>Tactic</th><th>Coverage</th></tr>
        {% for a in group.activities %}
        <tr>
            <td>{{ a.name }}</td>
            <td>{{ a.mitre_tactic_name }}</td>
            <td>{{ a.coverage_score or 'N/A' }}%</td>
        </tr>
        {% endfor %}
    </table>
    {% endfor %}
</body>
</html>
```

---

## Common Patterns

### Iterating Grouped vs Flat

**Grouped** — preserves group structure:

```
{% for group in activities_grouped %}
  Group: {{ group.name }} ({{ group.stats.total_activities }} activities)
  {% for activity in group.activities %}
    {{ activity.name }}
  {% endfor %}
{% endfor %}
```

**Flat** — single sorted list (sort order selected by user during export):

```
{% for activity in activities_flat %}
  {{ activity.name }} — {{ activity.group_name }}
{% endfor %}
```

### Conditional Detection Results

```
{% if activity.logged %}
  Logged: Yes ({{ activity.log_time | format_datetime }})
{% else %}
  Logged: No
{% endif %}
```

### Pass/Fail Styling

```
{% if activity.logged_evaluation == "pass" %}
  PASS
{% elif activity.logged_evaluation == "fail" %}
  FAIL
{% else %}
  N/A
{% endif %}
```

### Dynamic Evaluation Questions

```
{% for dq in activity.dynamic_questions %}
  Q: {{ dq.question }}
  A: {{ dq.data or "Not answered" }}
  Result: {{ dq.result }}
{% endfor %}
```

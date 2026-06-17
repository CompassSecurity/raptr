"""
Report rendering engine.

Supports two output formats:
- HTML: Jinja2 template with | tojson filter for embedding data in <script> tags
- DOCX: docxtpl (Jinja2-based DOCX templating) with RichText pre-processing
"""

import io
import json
from dataclasses import asdict
from datetime import datetime

import jinja2
import jinja2.sandbox

from app.services.report.markdown import prepare_docx_context
from app.services.report.report_data import ReportContext
from app.services.utils.memory import release_memory

# ---------------------------------------------------------------------------
# Custom Jinja2 filters
# ---------------------------------------------------------------------------


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def _tojson_filter(value: object) -> str:
    """Serialize a Python object to a JSON string safe for embedding in HTML.

    This custom filter is required (instead of Jinja2's built-in tojson) because:
    1. The context contains datetime objects (generated_at, activity timestamps)
       that the stdlib json module cannot serialize — _DateTimeEncoder handles
       these by converting them to ISO 8601 strings.
    2. The output is wrapped in markupsafe.Markup so that autoescape mode does
       not HTML-entity-encode the JSON (e.g. turning quotes into &quot;), which
       would break <script> blocks that parse the JSON as JavaScript.
    """
    from markupsafe import Markup

    return Markup(json.dumps(value, cls=_DateTimeEncoder))


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


def render_html_report(
    template_content: bytes,
    context: ReportContext,
) -> str:
    """
    Render an HTML report template with Jinja2.

    The template has access to all ReportContext fields as top-level variables,
    plus the | tojson filter for safely embedding data in <script> tags.

    Image data is already embedded as base64 in the context (FileReport.data_base64),
    so templates handle image rendering client-side.
    """
    # Use a SandboxedEnvironment so that templates (which originate from an
    # external, admin-seeded source via CUSTOM_DATA_URL) cannot execute
    # arbitrary Python via Jinja2 SSTI user generates a report.
    env = jinja2.sandbox.SandboxedEnvironment(autoescape=True)
    env.filters["tojson"] = _tojson_filter

    template = env.from_string(template_content.decode("utf-8"))
    return template.render(**asdict(context))


# ---------------------------------------------------------------------------
# DOCX rendering
# ---------------------------------------------------------------------------


def render_docx_report(
    template_content: bytes,
    context: ReportContext,
    image_data: dict[str, tuple[str, bytes]] | None = None,
) -> bytes:
    """
    Render a DOCX report template with docxtpl.

    Markdown fields are pre-converted to RichText objects before rendering.
    Image references in markdown are converted to InlineImage objects.
    """
    from docxtpl import DocxTemplate

    tpl = DocxTemplate(io.BytesIO(template_content))
    docx_context = prepare_docx_context(asdict(context), tpl, image_data)
    # Render with a SandboxedEnvironment to prevent Jinja2 SSTI/RCE from
    # externally-sourced (admin-seeded) templates. docxtpl manages XML escaping
    # itself, so autoescape stays off (the default).
    tpl.render(docx_context, jinja_env=jinja2.sandbox.SandboxedEnvironment())

    output = io.BytesIO()
    tpl.save(output)
    result = output.getvalue()

    # Explicitly drop heavy references before memory release
    del tpl, docx_context, output
    release_memory()

    return result

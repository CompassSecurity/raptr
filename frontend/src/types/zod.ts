import { makeApi, Zodios, type ZodiosOptions } from "@zodios/core";
import { z } from "zod";

const MessageResponse = z.object({ message: z.string() }).passthrough();
const Body_login_api_v1_auth_token_post = z
  .object({
    grant_type: z.union([z.string(), z.null()]).optional(),
    username: z.string(),
    password: z.string(),
    scope: z.string().optional().default(""),
    client_id: z.union([z.string(), z.null()]).optional(),
    client_secret: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const Token = z
  .object({
    access_token: z.string(),
    token_type: z.string(),
    next_url: z.string(),
  })
  .passthrough();
const ValidationError = z
  .object({
    loc: z.array(z.union([z.string(), z.number()])),
    msg: z.string(),
    type: z.string(),
    input: z.unknown().optional(),
    ctx: z.object({}).partial().passthrough().optional(),
  })
  .passthrough();
const HTTPValidationError = z
  .object({ detail: z.array(ValidationError) })
  .partial()
  .passthrough();
const MFASetupResponse = z
  .object({ provisioning_uri: z.string(), message: z.string() })
  .passthrough();
const OTP = z
  .object({
    otp: z
      .string()
      .min(6)
      .max(6)
      .regex(/^\d{6}$/),
  })
  .passthrough();
const ExternalAuthProvider = z
  .object({
    name: z.string(),
    authority: z.string(),
    client_id: z.string(),
    scope: z.string(),
  })
  .passthrough();
const AclRole = z.enum(["red", "blue", "spectator"]);
const AclRead = z
  .object({
    assessment_role: AclRole.optional(),
    user_id: z.string().uuid(),
    assessment_id: z.string().uuid(),
    id: z.string().uuid(),
  })
  .passthrough();
const AclBase = z
  .object({
    assessment_role: AclRole.optional(),
    user_id: z.string().uuid(),
    assessment_id: z.string().uuid(),
  })
  .passthrough();
const sort_order = z.union([z.enum(["asc", "desc"]), z.null()]).optional();
const name = z.union([z.string(), z.null()]).optional();
const ActivityPriority = z.enum(["Low", "Medium", "High", "Critical"]);
const priority = z.union([z.array(ActivityPriority), z.null()]).optional();
const sort_by = z
  .union([
    z.enum(["name", "mitre_tactic", "mitre_technique", "provider", "priority"]),
    z.null(),
  ])
  .optional();
const ActivitySeverity = z.enum([
  "Informational",
  "Low",
  "Medium",
  "High",
  "Critical",
]);
const ActivityTemplateRead = z
  .object({
    activity_actions: z.union([z.string(), z.null()]).optional(),
    activity_notes: z.union([z.string(), z.null()]).optional(),
    activity_rationale: z.union([z.string(), z.null()]).optional(),
    activity_requirements: z.union([z.string(), z.null()]).optional(),
    expected_logging: z.union([z.boolean(), z.null()]).optional(),
    expected_alert_creation: z.union([z.boolean(), z.null()]).optional(),
    expected_prevention: z.union([z.boolean(), z.null()]).optional(),
    expected_stakeholder_notification: z
      .union([z.boolean(), z.null()])
      .optional(),
    expected_severity: z.union([ActivitySeverity, z.null()]).optional(),
    mitre_tactic: z.string(),
    mitre_technique: z.string(),
    name: z.string(),
    priority: z.union([ActivityPriority, z.null()]).optional(),
    provider: z.string(),
    linked_knowledge_base_articles: z
      .union([z.array(z.string()), z.null()])
      .optional(),
    id: z.string().uuid(),
  })
  .passthrough();
const PaginatedResponse_ActivityTemplateRead_ = z
  .object({
    items: z.array(ActivityTemplateRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const ActivityGroupTemplateRead = z
  .object({
    id: z.string().uuid(),
    name: z.string(),
    description: z.union([z.string(), z.null()]).optional(),
    activity_template_ids: z.array(z.string().uuid()).optional().default([]),
  })
  .passthrough();
const PaginatedResponse_ActivityGroupTemplateRead_ = z
  .object({
    items: z.array(ActivityGroupTemplateRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const CampaignTemplateItemRead = z
  .object({
    id: z.string().uuid(),
    position: z.number().int(),
    item_type: z.string(),
    activity_group_template_id: z.union([z.string(), z.null()]).optional(),
    activity_template_id: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const CampaignTemplateRead = z
  .object({
    id: z.string().uuid(),
    name: z.string(),
    description: z.union([z.string(), z.null()]).optional(),
    items: z.array(CampaignTemplateItemRead).optional().default([]),
  })
  .passthrough();
const PaginatedResponse_CampaignTemplateRead_ = z
  .object({
    items: z.array(CampaignTemplateRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const EvaluationTemplateRead = z
  .object({
    name: z.string().optional().default(""),
    evaluation_criteria: z.string().optional().default(""),
    description: z.union([z.string(), z.null()]).optional(),
    id: z.string().uuid(),
  })
  .passthrough();
const PaginatedResponse_EvaluationTemplateRead_ = z
  .object({
    items: z.array(EvaluationTemplateRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const ReportTemplateFormat = z.enum(["html", "docx"]);
const format = z.union([ReportTemplateFormat, z.null()]).optional();
const ReportTemplateRead = z
  .object({
    filename: z.string(),
    format: ReportTemplateFormat,
    id: z.string().uuid(),
  })
  .passthrough();
const names = z.union([z.array(z.string()), z.null()]).optional();
const sort_by__2 = z
  .union([z.enum(["name", "mitre_technique_id"]), z.null()])
  .optional();
const KnowledgeBaseRead = z
  .object({
    name: z.string(),
    mitre_technique_id: z.union([z.string(), z.null()]).optional(),
    content: z.union([z.unknown(), z.null()]).optional(),
    id: z.string().uuid(),
  })
  .passthrough();
const PaginatedResponse_KnowledgeBaseRead_ = z
  .object({
    items: z.array(KnowledgeBaseRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const sort_by__3 = z.union([z.enum(["name", "mitre_id"]), z.null()]).optional();
const TacticBase = z
  .object({
    id: z.string().uuid(),
    mitre_id: z.string(),
    name: z.string(),
    url: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const TechniqueBase = z
  .object({
    id: z.string().uuid(),
    mitre_id: z.string(),
    name: z.string(),
    url: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const TacticWithTechniques = z
  .object({
    id: z.string().uuid(),
    mitre_id: z.string(),
    name: z.string(),
    url: z.union([z.string(), z.null()]).optional(),
    techniques: z.array(TechniqueBase),
  })
  .passthrough();
const TechniqueWithTactics = z
  .object({
    id: z.string().uuid(),
    mitre_id: z.string(),
    name: z.string(),
    url: z.union([z.string(), z.null()]).optional(),
    tactics: z.array(TacticBase),
  })
  .passthrough();
const UserRole = z.enum(["admin", "user"]);
const role = z.union([z.array(UserRole), z.null()]).optional();
const disabled = z.union([z.array(z.boolean()), z.null()]).optional();
const sort_by__4 = z
  .union([z.enum(["email", "role", "disabled", "mfa_verified"]), z.null()])
  .optional();
const UserRead = z
  .object({
    email: z.string().email(),
    role: UserRole,
    disabled: z.boolean(),
    id: z.string().uuid(),
    mfa_verified: z.boolean(),
    last_login_at: z.union([z.string(), z.null()]),
    last_logout_at: z.union([z.string(), z.null()]),
  })
  .passthrough();
const PaginatedResponse_UserRead_ = z
  .object({
    items: z.array(UserRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const UserBase = z
  .object({ email: z.string().email(), role: UserRole, disabled: z.boolean() })
  .passthrough();
const UserCreate = z
  .object({
    email: z.string().email(),
    role: UserRole,
    disabled: z.boolean(),
    password: z.string(),
  })
  .passthrough();
const UserPasswordReset = z.object({ new_password: z.string() }).passthrough();
const ExternalAuthConfig = z
  .object({
    name: z.string(),
    configuration: z.string(),
    issuer: z.string(),
    jwks_url: z.string(),
    audience: z.string(),
    scope: z.string(),
    username_claim: z.string(),
    client_id: z.string(),
    trusted_email_domains: z.array(z.string()),
  })
  .passthrough();
const Configuration = z
  .object({
    LOG_LEVEL: z.enum(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    APPLICATION_NAME: z.string(),
    FASTAPI_DOCUMENTATION: z.boolean(),
    ADMIN_EMAIL: z.string(),
    MIN_PASSWORD_LENGTH: z.number().int(),
    OTP_LOCAL_ENABLED: z.boolean(),
    OTP_EXTERNAL_ENABLED: z.boolean(),
    CORS_ENABLED: z.boolean(),
    CORS_ORIGINS: z.array(z.string()),
    CORS_METHODS: z.array(z.string()),
    CORS_HEADERS: z.array(z.string()),
    CORS_CREDENTIALS: z.boolean(),
    CORS_MAX_AGE: z.number().int(),
    DB_ENGINE: z.enum(["postgres", "sqlite"]),
    SQLITE_DB_PATH: z.string(),
    POSTGRES_USER: z.string(),
    POSTGRES_DB: z.string(),
    POSTGRES_HOST: z.string(),
    POSTGRES_PORT: z.number().int(),
    ALGORITHM: z.string(),
    ACCESS_TOKEN_EXPIRE_MINUTES: z.number().int(),
    MITRE_JSON_URL: z.string(),
    CUSTOM_DATA_URL: z.union([z.string(), z.null()]),
    ATOMIC_RED_TEAM_URL: z.string(),
    WELCOME_MESSAGE: z.union([z.string(), z.null()]),
    EXTERNAL_AUTH_CONFIGS: z.union([z.array(ExternalAuthConfig), z.null()]),
  })
  .passthrough();
const UserReadAcl = z
  .object({
    email: z.string().email(),
    role: UserRole,
    disabled: z.boolean(),
    id: z.string().uuid(),
    mfa_verified: z.boolean(),
    last_login_at: z.union([z.string(), z.null()]),
    last_logout_at: z.union([z.string(), z.null()]),
    acl: z
      .union([z.array(AclBase), z.null()])
      .optional()
      .default([]),
  })
  .passthrough();
const UserPasswordUpdate = z
  .object({ new_password: z.string(), old_password: z.string() })
  .passthrough();
const UserPasswordMfaReset = z.object({ password: z.string() }).passthrough();
const AssessmentType = z.enum(["PurpleTeam", "RedTeam"]);
const assessment_type = z.union([z.array(AssessmentType), z.null()]).optional();
const sort_by__5 = z
  .union([z.enum(["name", "assessment_type", "description"]), z.null()])
  .optional();
const AssessmentRead = z
  .object({
    name: z.string().min(1),
    description: z.string().min(1),
    assessment_type: AssessmentType.optional(),
    id: z.string().uuid(),
    default_evaluation_templates: z.array(
      z.record(z.union([z.string(), z.number()]))
    ),
  })
  .passthrough();
const PaginatedResponse_AssessmentRead_ = z
  .object({
    items: z.array(AssessmentRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const AssessmentBase = z
  .object({
    name: z.string().min(1),
    description: z.string().min(1),
    assessment_type: AssessmentType.optional(),
  })
  .passthrough();
const Body_import_assessment_api_v1_assessment_import_post = z
  .object({ file: z.string() })
  .passthrough();
const ImportResponse = z
  .object({
    assessment_id: z.string().uuid(),
    message: z.string(),
    warnings: z.array(z.string()).optional().default([]),
  })
  .passthrough();
const DynamicEvaluationQuestionAssign = z
  .object({
    evaluation_template_id: z.string().uuid(),
    position: z.number().int().optional().default(0),
  })
  .passthrough();
const activity_group_position = z.union([z.number(), z.null()]).optional();
const sort_by__6 = z
  .union([z.enum(["name", "activity_group_position"]), z.null()])
  .optional();
const ActivityGroupRead = z
  .object({
    name: z.string(),
    visible: z.boolean().optional().default(false),
    id: z.string().uuid(),
    deleted: z.boolean(),
    is_default: z.boolean(),
    activity_group_position: z.number().int(),
  })
  .passthrough();
const ActivityGroupBase = z
  .object({ name: z.string(), visible: z.boolean().optional().default(false) })
  .passthrough();
const ActivityState = z.enum([
  "Pending",
  "Waiting Red",
  "Waiting Blue",
  "Ready",
  "In Progress",
  "In Evaluation",
  "Completed",
  "Cancelled",
]);
const TagRead = z
  .object({
    name: z.string(),
    color: z.string().regex(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/),
    id: z.string().uuid(),
    deleted: z.boolean(),
  })
  .passthrough();
const AssetRead = z
  .object({
    name: z.string(),
    icon: z.union([z.string(), z.null()]).optional(),
    properties: z
      .union([z.object({}).partial().passthrough(), z.null()])
      .optional(),
    id: z.string().uuid(),
    deleted: z.boolean(),
  })
  .passthrough();
const EvaluationResult = z.enum(["pass", "fail", "n/a"]);
const ActivityEvaluationDynamicQuestionsRead = z
  .object({
    evaluation_template_id: z.string().uuid(),
    data: z.string().optional().default(""),
    evaluation_result: EvaluationResult.optional(),
    position: z.number().int().optional().default(0),
    id: z.string().uuid(),
  })
  .passthrough();
const ActivityEvaluationRead = z
  .object({
    logged_evaluation: EvaluationResult.optional(),
    alerted_evaluation: EvaluationResult.optional(),
    prevented_evaluation: EvaluationResult.optional(),
    stakeholder_notified_evaluation: EvaluationResult.optional(),
    activity_coverage_score: z.number().int().optional().default(0),
    event_to_alert_data: z.string().optional().default(""),
    event_to_alert_evaluation_result: EvaluationResult.optional(),
    alert_to_stakeholder_data: z.string().optional().default(""),
    alert_to_stakeholder_evaluation_result: EvaluationResult.optional(),
    alert_severity_data: z.string().optional().default(""),
    alert_severity_evaluation_result: EvaluationResult.optional(),
    stakeholder_notification_severity_data: z.string().optional().default(""),
    stakeholder_notification_severity_evaluation_result:
      EvaluationResult.optional(),
    dynamic_questions: z
      .array(ActivityEvaluationDynamicQuestionsRead)
      .optional()
      .default([]),
    id: z.string().uuid(),
    activity_id: z.string().uuid(),
  })
  .passthrough();
const ActivityRead = z
  .object({
    name: z.string(),
    mitre_tactic: z.string(),
    mitre_technique: z.string(),
    provider: z.union([z.string(), z.null()]).optional(),
    visible: z.boolean().optional().default(false),
    priority: z.union([ActivityPriority, z.null()]).optional(),
    state: z.union([ActivityState, z.null()]).optional(),
    tags: z.array(TagRead).optional().default([]),
    activity_group_id: z.union([z.string(), z.null()]).optional(),
    updated_at: z.union([z.string(), z.null()]).optional(),
    activity_rationale: z.union([z.string(), z.null()]).optional(),
    activity_actions: z.union([z.string(), z.null()]).optional(),
    activity_requirements: z.union([z.string(), z.null()]).optional(),
    activity_notes: z.union([z.string(), z.null()]).optional(),
    activity_start_time: z.union([z.string(), z.null()]).optional(),
    activity_end_time: z.union([z.string(), z.null()]).optional(),
    sources: z.array(AssetRead).optional().default([]),
    targets: z.array(AssetRead).optional().default([]),
    tools: z.array(AssetRead).optional().default([]),
    expected_logging: z.union([z.boolean(), z.null()]).optional(),
    expected_prevention: z.union([z.boolean(), z.null()]).optional(),
    expected_alert_creation: z.union([z.boolean(), z.null()]).optional(),
    expected_stakeholder_notification: z
      .union([z.boolean(), z.null()])
      .optional(),
    expected_severity: z.union([ActivitySeverity, z.null()]).optional(),
    log_sources: z.array(AssetRead).optional().default([]),
    prevention_sources: z.array(AssetRead).optional().default([]),
    alert_sources: z.array(AssetRead).optional().default([]),
    stakeholder_notification_sources: z.array(AssetRead).optional().default([]),
    logged: z.union([z.boolean(), z.null()]).optional(),
    log_time: z.union([z.string(), z.null()]).optional(),
    prevented: z.union([z.boolean(), z.null()]).optional(),
    prevent_time: z.union([z.string(), z.null()]).optional(),
    alerted: z.union([z.boolean(), z.null()]).optional(),
    alert_severity: z.union([ActivitySeverity, z.null()]).optional(),
    alert_time: z.union([z.string(), z.null()]).optional(),
    stakeholder_notification_created: z
      .union([z.boolean(), z.null()])
      .optional(),
    stakeholder_notification_severity: z
      .union([ActivitySeverity, z.null()])
      .optional(),
    stakeholder_notification_time: z.union([z.string(), z.null()]).optional(),
    linked_knowledge_base_articles: z
      .union([z.array(z.string()), z.null()])
      .optional(),
    log_notes: z.union([z.string(), z.null()]).optional(),
    alert_notes: z.union([z.string(), z.null()]).optional(),
    prevent_notes: z.union([z.string(), z.null()]).optional(),
    stakeholder_notification_notes: z.union([z.string(), z.null()]).optional(),
    evaluation: z.union([ActivityEvaluationRead, z.null()]).optional(),
    id: z.string().uuid(),
    deleted: z.boolean(),
    activity_position: z.union([z.number(), z.null()]).optional(),
    activity_group: z.union([ActivityGroupRead, z.null()]).optional(),
    created_at: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const ActivityGroupReorder = z
  .object({ activity_group_ids: z.array(z.string().uuid()) })
  .passthrough();
const ActivityReorder = z
  .object({ activity_ids: z.array(z.string().uuid()) })
  .passthrough();
const state = z.union([z.array(ActivityState), z.null()]).optional();
const visible = z.union([z.boolean(), z.null()]).optional();
const tags = z.union([z.array(z.string().uuid()), z.null()]).optional();
const sort_by__7 = z
  .union([
    z.enum([
      "name",
      "activity_position",
      "mitre_tactic",
      "mitre_technique",
      "priority",
      "state",
      "visible",
      "created_at",
      "updated_at",
      "activity_group.name",
      "activity_coverage_score",
      "activity_start_time",
      "activity_end_time",
      "tags",
    ]),
    z.null(),
  ])
  .optional();
const PaginatedResponse_ActivityRead_ = z
  .object({
    items: z.array(ActivityRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const ActivityBase = z
  .object({
    name: z.string(),
    mitre_tactic: z.string(),
    mitre_technique: z.string(),
  })
  .passthrough();
const ActivityEvaluationDynamicQuestionsUpdate = z
  .object({
    evaluation_template_id: z.string().uuid(),
    data: z.union([z.string(), z.null()]).optional(),
    evaluation_result: z.union([EvaluationResult, z.null()]).optional(),
  })
  .passthrough();
const ActivityEvaluationUpdate = z
  .object({
    logged_evaluation: EvaluationResult,
    alerted_evaluation: EvaluationResult,
    prevented_evaluation: EvaluationResult,
    stakeholder_notified_evaluation: EvaluationResult,
    activity_coverage_score: z.number().int().default(0),
    event_to_alert_data: z.string().default(""),
    event_to_alert_evaluation_result: EvaluationResult,
    alert_to_stakeholder_data: z.string().default(""),
    alert_to_stakeholder_evaluation_result: EvaluationResult,
    alert_severity_data: z.string().default(""),
    alert_severity_evaluation_result: EvaluationResult,
    stakeholder_notification_severity_data: z.string().default(""),
    stakeholder_notification_severity_evaluation_result: EvaluationResult,
    dynamic_questions: z.union([
      z.array(ActivityEvaluationDynamicQuestionsUpdate),
      z.null(),
    ]),
  })
  .partial()
  .passthrough();
const ActivityUpdate = z
  .object({
    name: z.string(),
    mitre_tactic: z.string(),
    mitre_technique: z.string(),
    provider: z.union([z.string(), z.null()]).optional(),
    visible: z.boolean().optional().default(false),
    priority: z.union([ActivityPriority, z.null()]).optional(),
    state: z.union([ActivityState, z.null()]).optional(),
    tags: z.array(z.string().uuid()).optional().default([]),
    activity_group_id: z.union([z.string(), z.null()]).optional(),
    updated_at: z.union([z.string(), z.null()]).optional(),
    activity_rationale: z.union([z.string(), z.null()]).optional(),
    activity_actions: z.union([z.string(), z.null()]).optional(),
    activity_requirements: z.union([z.string(), z.null()]).optional(),
    activity_notes: z.union([z.string(), z.null()]).optional(),
    activity_start_time: z.union([z.string(), z.null()]).optional(),
    activity_end_time: z.union([z.string(), z.null()]).optional(),
    sources: z.array(z.string().uuid()).optional().default([]),
    targets: z.array(z.string().uuid()).optional().default([]),
    tools: z.array(z.string().uuid()).optional().default([]),
    expected_logging: z.union([z.boolean(), z.null()]).optional(),
    expected_prevention: z.union([z.boolean(), z.null()]).optional(),
    expected_alert_creation: z.union([z.boolean(), z.null()]).optional(),
    expected_stakeholder_notification: z
      .union([z.boolean(), z.null()])
      .optional(),
    expected_severity: z.union([ActivitySeverity, z.null()]).optional(),
    log_sources: z.array(z.string().uuid()).optional().default([]),
    prevention_sources: z.array(z.string().uuid()).optional().default([]),
    alert_sources: z.array(z.string().uuid()).optional().default([]),
    stakeholder_notification_sources: z
      .array(z.string().uuid())
      .optional()
      .default([]),
    logged: z.union([z.boolean(), z.null()]).optional(),
    log_time: z.union([z.string(), z.null()]).optional(),
    prevented: z.union([z.boolean(), z.null()]).optional(),
    prevent_time: z.union([z.string(), z.null()]).optional(),
    alerted: z.union([z.boolean(), z.null()]).optional(),
    alert_severity: z.union([ActivitySeverity, z.null()]).optional(),
    alert_time: z.union([z.string(), z.null()]).optional(),
    stakeholder_notification_created: z
      .union([z.boolean(), z.null()])
      .optional(),
    stakeholder_notification_severity: z
      .union([ActivitySeverity, z.null()])
      .optional(),
    stakeholder_notification_time: z.union([z.string(), z.null()]).optional(),
    linked_knowledge_base_articles: z
      .union([z.array(z.string()), z.null()])
      .optional(),
    log_notes: z.union([z.string(), z.null()]).optional(),
    alert_notes: z.union([z.string(), z.null()]).optional(),
    prevent_notes: z.union([z.string(), z.null()]).optional(),
    stakeholder_notification_notes: z.union([z.string(), z.null()]).optional(),
    evaluation: z.union([ActivityEvaluationUpdate, z.null()]).optional(),
  })
  .passthrough();
const ActivityTagsUpdate = z
  .object({ tag_ids: z.array(z.string().uuid()).default([]) })
  .partial()
  .passthrough();
const ActivityGroupUpdate = z
  .object({ activity_group_id: z.union([z.string(), z.null()]) })
  .partial()
  .passthrough();
const ActivityAssetUpdate = z
  .object({ asset_ids: z.array(z.string().uuid()) })
  .passthrough();
const FileCategory = z.enum(["red", "blue"]);
const category = z.union([FileCategory, z.null()]).optional();
const sort_by__8 = z
  .union([z.enum(["filename", "created_at"]), z.null()])
  .optional();
const FileType = z.enum(["image/png", "image/jpeg", "image/jpg", "text/plain"]);
const FileRead = z
  .object({
    filename: z.string(),
    content_type: FileType,
    size: z.number().int(),
    category: FileCategory,
    activity_id: z.string().uuid(),
    id: z.string().uuid(),
    created_at: z.string().datetime({ offset: true }),
    created_by: z.string().uuid(),
  })
  .passthrough();
const Body_upload_file_api_v1_assessments__assessment_id__activity__activity_id__upload_post =
  z.object({ file: z.string() }).passthrough();
const FileUploadResponse = z
  .object({ message: z.string(), url: z.string(), file_id: z.string().uuid() })
  .passthrough();
const ActivityHistoryRead = z
  .object({
    activity_id: z.string().uuid(),
    version: z.number().int(),
    saved_at: z.string().datetime({ offset: true }),
    saved_by_id: z.union([z.string(), z.null()]),
    snapshot: z.object({}).partial().passthrough(),
    id: z.string().uuid(),
    saved_by: z.union([UserBase, z.null()]).optional(),
  })
  .passthrough();
const sort_by__9 = z.union([z.enum(["name", "deleted"]), z.null()]).optional();
const PaginatedResponse_AssetRead_ = z
  .object({
    items: z.array(AssetRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const AssetBase = z
  .object({
    name: z.string(),
    icon: z.union([z.string(), z.null()]).optional(),
    properties: z
      .union([z.object({}).partial().passthrough(), z.null()])
      .optional(),
  })
  .passthrough();
const sort_by__10 = z
  .union([z.enum(["name", "color", "deleted"]), z.null()])
  .optional();
const PaginatedResponse_TagRead_ = z
  .object({
    items: z.array(TagRead),
    total: z.number().int(),
    page: z.number().int(),
    size: z.number().int(),
    pages: z.number().int(),
  })
  .passthrough();
const TagBase = z
  .object({
    name: z.string(),
    color: z.string().regex(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/),
  })
  .passthrough();
const ReportContextRequest = z
  .object({
    sort_by: z
      .enum([
        "activity_position",
        "name",
        "mitre_tactic",
        "priority",
        "state",
        "start_time",
        "coverage_score",
      ])
      .default("activity_position"),
    sort_order: z.enum(["asc", "desc"]).default("asc"),
  })
  .partial()
  .passthrough();
const ReportGenerateRequest = z
  .object({
    sort_by: z
      .enum([
        "activity_position",
        "name",
        "mitre_tactic",
        "priority",
        "state",
        "start_time",
        "coverage_score",
      ])
      .optional()
      .default("activity_position"),
    sort_order: z.enum(["asc", "desc"]).optional().default("asc"),
    template_id: z.string().uuid(),
  })
  .passthrough();
const StateDistributionItem = z
  .object({ state: z.string(), count: z.number().int() })
  .passthrough();
const PriorityBreakdownItem = z
  .object({ priority: z.string(), count: z.number().int() })
  .passthrough();
const PriorityAverageScoreItem = z
  .object({
    priority: z.string(),
    average_score: z.union([z.number(), z.null()]),
  })
  .passthrough();
const MitreOverallTacticScoreItem = z
  .object({
    tactic: z.string(),
    overall_score: z.union([z.number(), z.null()]),
    expected_logged_score: z.union([z.number(), z.null()]),
    logged_score: z.union([z.number(), z.null()]),
    expected_prevented_score: z.union([z.number(), z.null()]),
    prevented_score: z.union([z.number(), z.null()]),
    expected_alerted_score: z.union([z.number(), z.null()]),
    alerted_score: z.union([z.number(), z.null()]),
    expected_stakeholder_notified_score: z.union([z.number(), z.null()]),
    stakeholder_notified_score: z.union([z.number(), z.null()]),
  })
  .passthrough();
const MitreTechniqueScoreItem = z
  .object({
    technique: z.string(),
    overall_score: z.union([z.number(), z.null()]),
    expected_logged_score: z.union([z.number(), z.null()]),
    logged_score: z.union([z.number(), z.null()]),
    expected_prevented_score: z.union([z.number(), z.null()]),
    prevented_score: z.union([z.number(), z.null()]),
    expected_alerted_score: z.union([z.number(), z.null()]),
    alerted_score: z.union([z.number(), z.null()]),
    expected_stakeholder_notified_score: z.union([z.number(), z.null()]),
    stakeholder_notified_score: z.union([z.number(), z.null()]),
  })
  .passthrough();
const MitreTacticScoreItem = z
  .object({ tactic: z.string(), techniques: z.array(MitreTechniqueScoreItem) })
  .passthrough();
const MeanTimeMetricsItem = z
  .object({
    priority: z.string(),
    mean_time_to_detect_seconds: z.union([z.number(), z.null()]),
    mean_time_to_respond_seconds: z.union([z.number(), z.null()]),
  })
  .passthrough();
const SeverityAccuracyItem = z
  .object({
    expected_severity: z.string(),
    actual_informational: z.number().int(),
    actual_low: z.number().int(),
    actual_medium: z.number().int(),
    actual_high: z.number().int(),
    actual_critical: z.number().int(),
    actual_none: z.number().int(),
  })
  .passthrough();
const AssessmentStatisticsResponse = z
  .object({
    state_distribution: z.array(StateDistributionItem),
    priority_breakdown: z.array(PriorityBreakdownItem),
    average_coverage_score: z.union([z.number(), z.null()]).optional(),
    average_coverage_scores_by_priority: z.array(PriorityAverageScoreItem),
    mitre_overall_tactic_scores: z.array(MitreOverallTacticScoreItem),
    mitre_tactic_scores: z.array(MitreTacticScoreItem),
    mean_time_metrics: z.array(MeanTimeMetricsItem),
    severity_accuracy: z.array(SeverityAccuracyItem),
  })
  .passthrough();
const ActivityAssetRole = z.enum([
  "source",
  "target",
  "tool",
  "log_source",
  "prevention_source",
  "alert_source",
  "stakeholder_notification_source",
]);

export const schemas = {
  MessageResponse,
  Body_login_api_v1_auth_token_post,
  Token,
  ValidationError,
  HTTPValidationError,
  MFASetupResponse,
  OTP,
  ExternalAuthProvider,
  AclRole,
  AclRead,
  AclBase,
  sort_order,
  name,
  ActivityPriority,
  priority,
  sort_by,
  ActivitySeverity,
  ActivityTemplateRead,
  PaginatedResponse_ActivityTemplateRead_,
  ActivityGroupTemplateRead,
  PaginatedResponse_ActivityGroupTemplateRead_,
  CampaignTemplateItemRead,
  CampaignTemplateRead,
  PaginatedResponse_CampaignTemplateRead_,
  EvaluationTemplateRead,
  PaginatedResponse_EvaluationTemplateRead_,
  ReportTemplateFormat,
  format,
  ReportTemplateRead,
  names,
  sort_by__2,
  KnowledgeBaseRead,
  PaginatedResponse_KnowledgeBaseRead_,
  sort_by__3,
  TacticBase,
  TechniqueBase,
  TacticWithTechniques,
  TechniqueWithTactics,
  UserRole,
  role,
  disabled,
  sort_by__4,
  UserRead,
  PaginatedResponse_UserRead_,
  UserBase,
  UserCreate,
  UserPasswordReset,
  ExternalAuthConfig,
  Configuration,
  UserReadAcl,
  UserPasswordUpdate,
  UserPasswordMfaReset,
  AssessmentType,
  assessment_type,
  sort_by__5,
  AssessmentRead,
  PaginatedResponse_AssessmentRead_,
  AssessmentBase,
  Body_import_assessment_api_v1_assessment_import_post,
  ImportResponse,
  DynamicEvaluationQuestionAssign,
  activity_group_position,
  sort_by__6,
  ActivityGroupRead,
  ActivityGroupBase,
  ActivityState,
  TagRead,
  AssetRead,
  EvaluationResult,
  ActivityEvaluationDynamicQuestionsRead,
  ActivityEvaluationRead,
  ActivityRead,
  ActivityGroupReorder,
  ActivityReorder,
  state,
  visible,
  tags,
  sort_by__7,
  PaginatedResponse_ActivityRead_,
  ActivityBase,
  ActivityEvaluationDynamicQuestionsUpdate,
  ActivityEvaluationUpdate,
  ActivityUpdate,
  ActivityTagsUpdate,
  ActivityGroupUpdate,
  ActivityAssetUpdate,
  FileCategory,
  category,
  sort_by__8,
  FileType,
  FileRead,
  Body_upload_file_api_v1_assessments__assessment_id__activity__activity_id__upload_post,
  FileUploadResponse,
  ActivityHistoryRead,
  sort_by__9,
  PaginatedResponse_AssetRead_,
  AssetBase,
  sort_by__10,
  PaginatedResponse_TagRead_,
  TagBase,
  ReportContextRequest,
  ReportGenerateRequest,
  StateDistributionItem,
  PriorityBreakdownItem,
  PriorityAverageScoreItem,
  MitreOverallTacticScoreItem,
  MitreTechniqueScoreItem,
  MitreTacticScoreItem,
  MeanTimeMetricsItem,
  SeverityAccuracyItem,
  AssessmentStatisticsResponse,
  ActivityAssetRole,
};

const endpoints = makeApi([
  {
    method: "get",
    path: "/api/v1/acl/",
    alias: "get_acls_api_v1_acl__get",
    description: `Get all acls.`,
    requestFormat: "json",
    response: z.array(AclRead),
  },
  {
    method: "post",
    path: "/api/v1/acl/",
    alias: "create_acl_api_v1_acl__post",
    description: `Create a new acl.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AclBase,
      },
    ],
    response: AclRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/acl/:acl_id",
    alias: "get_acl_api_v1_acl__acl_id__get",
    description: `Get an acl by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "acl_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AclRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/acl/:acl_id",
    alias: "update_acl_api_v1_acl__acl_id__put",
    description: `Update an acl by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AclBase,
      },
      {
        name: "acl_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AclRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/v1/acl/:acl_id",
    alias: "delete_acl_api_v1_acl__acl_id__delete",
    description: `Delete an acl by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "acl_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/acl/assessment/:assessment_id",
    alias: "get_acls_by_assessment_api_v1_acl_assessment__assessment_id__get",
    description: `Get all acls by assessment ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.array(AclRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/acl/user/:user_id",
    alias: "get_acls_by_user_api_v1_acl_user__user_id__get",
    description: `Get all acls by user ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.array(AclRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/activity_group_template/",
    alias: "get_activity_group_templates_api_v1_activity_group_template__get",
    description: `Get all activity group templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: name,
      },
    ],
    response: PaginatedResponse_ActivityGroupTemplateRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/activity_template/",
    alias: "get_activity_templates_api_v1_activity_template__get",
    description: `Get all activity templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_tactic",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_technique",
        type: "Query",
        schema: name,
      },
      {
        name: "provider",
        type: "Query",
        schema: name,
      },
      {
        name: "priority",
        type: "Query",
        schema: priority,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by,
      },
    ],
    response: PaginatedResponse_ActivityTemplateRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/activity_template/:activity_template_id",
    alias:
      "get_activity_template_api_v1_activity_template__activity_template_id__get",
    description: `Get an activity template by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_template_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityTemplateRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/admin/configuration",
    alias: "get_configuration_api_v1_admin_configuration_get",
    description: `Get the configuration of the server.`,
    requestFormat: "json",
    response: Configuration,
  },
  {
    method: "post",
    path: "/api/v1/admin/seed/ART",
    alias:
      "import_atomic_red_team_activity_templates_api_v1_admin_seed_ART_post",
    description: `Import Atomic Red Team templates from git repository.`,
    requestFormat: "json",
    response: z.object({ message: z.string() }).passthrough(),
  },
  {
    method: "post",
    path: "/api/v1/admin/seed/custom",
    alias: "import_custom_data_api_v1_admin_seed_custom_post",
    description: `Import custom data from git repository.`,
    requestFormat: "json",
    response: z.object({ message: z.string() }).passthrough(),
  },
  {
    method: "post",
    path: "/api/v1/admin/seed/mitre/",
    alias: "import_mitre_techniques_and_tactics_api_v1_admin_seed_mitre__post",
    description: `Create MITRE ATT&amp;CK data.`,
    requestFormat: "json",
    response: z.object({ message: z.string() }).passthrough(),
  },
  {
    method: "get",
    path: "/api/v1/admin/users",
    alias: "read_users_api_v1_admin_users_get",
    description: `Get all users with pagination metadata.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "email",
        type: "Query",
        schema: name,
      },
      {
        name: "role",
        type: "Query",
        schema: role,
      },
      {
        name: "disabled",
        type: "Query",
        schema: disabled,
      },
      {
        name: "mfa_verified",
        type: "Query",
        schema: disabled,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__4,
      },
    ],
    response: PaginatedResponse_UserRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/admin/users/",
    alias: "create_user_api_v1_admin_users__post",
    description: `Create a new user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserCreate,
      },
    ],
    response: UserRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/admin/users/:user_id",
    alias: "read_user_api_v1_admin_users__user_id__get",
    description: `Get a user by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/admin/users/:user_id",
    alias: "update_user_api_v1_admin_users__user_id__put",
    description: `Update a user by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserBase,
      },
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/v1/admin/users/:user_id",
    alias: "delete_user_api_v1_admin_users__user_id__delete",
    description: `Delete a user by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/admin/users/:user_id/reset_mfa",
    alias: "reset_user_mfa_api_v1_admin_users__user_id__reset_mfa_post",
    description: `Reset a user&#x27;s MFA.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/admin/users/:user_id/reset_password",
    alias:
      "reset_user_password_api_v1_admin_users__user_id__reset_password_post",
    description: `Reset a user&#x27;s password.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ new_password: z.string() }).passthrough(),
      },
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessment/",
    alias: "get_assessments_api_v1_assessment__get",
    description: `Get all assessments.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "assessment_type",
        type: "Query",
        schema: assessment_type,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__5,
      },
    ],
    response: PaginatedResponse_AssessmentRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessment/",
    alias: "create_assessment_api_v1_assessment__post",
    description: `Create a new assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AssessmentBase,
      },
    ],
    response: AssessmentRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessment/:assessment_id",
    alias: "get_assessment_api_v1_assessment__assessment_id__get",
    description: `Get an assessment by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssessmentRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessment/:assessment_id",
    alias: "update_assessment_api_v1_assessment__assessment_id__put",
    description: `Update an assessment by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AssessmentBase,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssessmentRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/v1/assessment/:assessment_id",
    alias: "delete_assessment_api_v1_assessment__assessment_id__delete",
    description: `Delete an assessment by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessment/:assessment_id/default_evaluation_templates",
    alias:
      "update_assessment_default_evaluation_templates_api_v1_assessment__assessment_id__default_evaluation_templates_put",
    description: `Update an assessment&#x27;s evaluation template.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.array(DynamicEvaluationQuestionAssign),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssessmentRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessment/import",
    alias: "import_assessment_api_v1_assessment_import_post",
    description: `Import an assessment from an exported zip archive.
Creates a new assessment with all child data.`,
    requestFormat: "form-data",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ file: z.string() }).passthrough(),
      },
    ],
    response: ImportResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity_group/",
    alias:
      "get_activity_groups_api_v1_assessments__assessment_id__activity_group__get",
    description: `Get all activity groups for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "activity_group_position",
        type: "Query",
        schema: activity_group_position,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__6,
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
    ],
    response: z.array(ActivityGroupRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/activity_group/",
    alias:
      "create_activity_group_api_v1_assessments__assessment_id__activity_group__post",
    description: `Create a new activity group for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityGroupBase,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityGroupRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity_group/:activity_group_id",
    alias:
      "get_activity_group_api_v1_assessments__assessment_id__activity_group__activity_group_id__get",
    description: `Get a specific activity group for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_group_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityGroupRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity_group/:activity_group_id",
    alias:
      "update_activity_group_api_v1_assessments__assessment_id__activity_group__activity_group_id__put",
    description: `Update an activity group for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityGroupBase,
      },
      {
        name: "activity_group_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityGroupRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity_group/:activity_group_id/activities",
    alias:
      "get_activity_group_activities_api_v1_assessments__assessment_id__activity_group__activity_group_id__activities_get",
    description: `Get all activities for a specific activity group.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_group_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.array(ActivityRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity_group/:activity_group_id/delete",
    alias:
      "toggle_activity_group_delete_api_v1_assessments__assessment_id__activity_group__activity_group_id__delete_put",
    description: `Toggle the deleted flag for an activity group for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_group_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity_group/:activity_group_id/reorder",
    alias:
      "reorder_activities_api_v1_assessments__assessment_id__activity_group__activity_group_id__reorder_put",
    description: `Reorder activities within an activity group.

Provide the activity IDs in the desired order.
The first ID gets position 0, second gets position 1, etc.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityReorder,
      },
      {
        name: "activity_group_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity_group/:activity_group_id/visible",
    alias:
      "toggle_activity_group_visible_api_v1_assessments__assessment_id__activity_group__activity_group_id__visible_put",
    description: `Toggle the visible flag for an activity group for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_group_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity_group/reorder",
    alias:
      "reorder_activity_groups_api_v1_assessments__assessment_id__activity_group_reorder_put",
    description: `Reorder activity groups within an assessment.

Provide the activity group IDs in the desired order.
The first ID gets position 0, second gets position 1, etc.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityGroupReorder,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/",
    alias:
      "get_all_activities_api_v1_assessments__assessment_id__activity__get",
    description: `Get all activities for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_tactic",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_technique",
        type: "Query",
        schema: name,
      },
      {
        name: "priority",
        type: "Query",
        schema: priority,
      },
      {
        name: "state",
        type: "Query",
        schema: state,
      },
      {
        name: "visible",
        type: "Query",
        schema: visible,
      },
      {
        name: "deleted",
        type: "Query",
        schema: visible,
      },
      {
        name: "tags",
        type: "Query",
        schema: tags,
      },
      {
        name: "activity_group_id",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__7,
      },
    ],
    response: PaginatedResponse_ActivityRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/activity/",
    alias: "create_activity_api_v1_assessments__assessment_id__activity__post",
    description: `Create a new activity for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityBase,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id",
    alias:
      "get_activity_by_id_api_v1_assessments__assessment_id__activity__activity_id__get",
    description: `Get an activity by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id",
    alias:
      "update_activity_api_v1_assessments__assessment_id__activity__activity_id__put",
    description: `Update an activity by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityUpdate,
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/activity_group",
    alias:
      "assign_update_activity_to_activity_group_api_v1_assessments__assessment_id__activity__activity_id__activity_group_put",
    description: `Assign an activity to a group or remove it.
To assign: Provide activity_group_id.
To remove: Provide activity_group_id as null.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityGroupUpdate,
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/assets/:role",
    alias:
      "assign_update_assets_to_activity_api_v1_assessments__assessment_id__activity__activity_id__assets__role__put",
    description: `Assign assets to an activity for a specific role (source, target, tool, etc.).
Replaces all existing assets for this role.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityAssetUpdate,
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "role",
        type: "Path",
        schema: z.enum([
          "source",
          "target",
          "tool",
          "log_source",
          "prevention_source",
          "alert_source",
          "stakeholder_notification_source",
        ]),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/clone",
    alias:
      "clone_activity_api_v1_assessments__assessment_id__activity__activity_id__clone_put",
    description: `Clone an activity by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/delete",
    alias:
      "toggle_delete_activity_state_api_v1_assessments__assessment_id__activity__activity_id__delete_put",
    description: `Toggle delete state of an activity by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/dynamic_evaluation_questions",
    alias:
      "assign_dynamic_evaluation_questions_api_v1_assessments__assessment_id__activity__activity_id__dynamic_evaluation_questions_put",
    description: `Assign, update, remove dynamic evaluation questions to an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.array(DynamicEvaluationQuestionAssign),
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/files",
    alias:
      "get_activity_files_api_v1_assessments__assessment_id__activity__activity_id__files_get",
    description: `Get files for an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "filename",
        type: "Query",
        schema: name,
      },
      {
        name: "category",
        type: "Query",
        schema: category,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__8,
      },
    ],
    response: z.array(FileRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/files/:file_id",
    alias:
      "get_activity_file_api_v1_assessments__assessment_id__activity__activity_id__files__file_id__get",
    description: `Get a file for an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "file_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: FileRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/files/:file_id",
    alias:
      "delete_activity_file_api_v1_assessments__assessment_id__activity__activity_id__files__file_id__delete",
    description: `Delete a file for an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "file_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/files/:file_id/download",
    alias:
      "download_activity_file_api_v1_assessments__assessment_id__activity__activity_id__files__file_id__download_get",
    description: `Download a file for an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "file_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/tags",
    alias:
      "assign_update_activity_tags_api_v1_assessments__assessment_id__activity__activity_id__tags_put",
    description: `Update tags for an activity. Replaces all existing tags with the provided list.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ActivityTagsUpdate,
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/upload",
    alias:
      "upload_file_api_v1_assessments__assessment_id__activity__activity_id__upload_post",
    description: `Upload a file to an activity.`,
    requestFormat: "form-data",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ file: z.string() }).passthrough(),
      },
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: FileUploadResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/version",
    alias:
      "get_activity_history_list_api_v1_assessments__assessment_id__activity__activity_id__version_get",
    description: `Get a list of all historical versions of an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.array(ActivityHistoryRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/version/:version_id",
    alias:
      "get_activity_history_version_api_v1_assessments__assessment_id__activity__activity_id__version__version_id__get",
    description: `Get a specific historical version (snapshot) of an activity.`,
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "version_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: ActivityHistoryRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/activity/:activity_id/visible",
    alias:
      "toggle_visible_activity_api_v1_assessments__assessment_id__activity__activity_id__visible_put",
    requestFormat: "json",
    parameters: [
      {
        name: "activity_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/asset/",
    alias: "get_assets_api_v1_assessments__assessment_id__asset__get",
    description: `Get all assets for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "deleted",
        type: "Query",
        schema: visible,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__9,
      },
    ],
    response: PaginatedResponse_AssetRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/asset/",
    alias: "create_asset_api_v1_assessments__assessment_id__asset__post",
    description: `Create a new asset for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AssetBase,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssetRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/asset/:asset_id",
    alias: "get_asset_api_v1_assessments__assessment_id__asset__asset_id__get",
    description: `Get a specific asset for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "asset_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssetRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/asset/:asset_id",
    alias:
      "update_asset_api_v1_assessments__assessment_id__asset__asset_id__put",
    description: `Update a specific asset for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AssetBase,
      },
      {
        name: "asset_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssetRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/asset/:asset_id/delete",
    alias:
      "toggle_asset_delete_api_v1_assessments__assessment_id__asset__asset_id__delete_put",
    description: `Toggle the deleted flag for a specific asset for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "asset_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/export/assessment",
    alias:
      "export_assessment_api_v1_assessments__assessment_id__export_assessment_post",
    description: `Export the entire assessment as a zip archive download.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.void(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/export/mitre",
    alias:
      "generate_mitre_attack_navigator_layer_api_v1_assessments__assessment_id__export_mitre_post",
    description: `Generate a MITRE ATT&amp;CK Navigator layer for the assessment.
Returns a file download (JSON).`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.void(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/export/report/context",
    alias:
      "get_report_context_api_v1_assessments__assessment_id__export_report_context_post",
    description: `Return the report data layer as JSON.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReportContextRequest,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/export/report/generate",
    alias:
      "generate_report_api_v1_assessments__assessment_id__export_report_generate_post",
    description: `Generate a report for the assessment using the specified template.
Returns a file download (HTML or DOCX).`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReportGenerateRequest,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.void(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/imports/activity_group_templates",
    alias:
      "import_from_activity_group_templates_api_v1_assessments__assessment_id__imports_activity_group_templates_post",
    description: `Import multiple activity groups from activity group templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.array(z.string().uuid()),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/imports/activity_templates",
    alias:
      "import_from_activity_templates_api_v1_assessments__assessment_id__imports_activity_templates_post",
    description: `Import multiple activities from activity templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.array(z.string().uuid()),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/imports/campaign_template",
    alias:
      "import_from_campaign_template_api_v1_assessments__assessment_id__imports_campaign_template_post",
    description: `Import all content from a campaign template into an assessment.
Creates groups and activities with correct ordering.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "campaign_template_id",
        type: "Query",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/statistics/",
    alias:
      "get_assessment_statistics_endpoint_api_v1_assessments__assessment_id__statistics__get",
    description: `Get statistics for a single assessment.

Returns metrics over visible, non-deleted activities in visible,
non-deleted groups. All roles see the same data.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: AssessmentStatisticsResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/tag/",
    alias: "get_tags_api_v1_assessments__assessment_id__tag__get",
    description: `Get all tags for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "deleted",
        type: "Query",
        schema: visible,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__10,
      },
    ],
    response: PaginatedResponse_TagRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/assessments/:assessment_id/tag/",
    alias: "create_tag_api_v1_assessments__assessment_id__tag__post",
    description: `Create a new tag for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TagBase,
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: TagRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/assessments/:assessment_id/tag/:tag_id",
    alias: "get_tag_api_v1_assessments__assessment_id__tag__tag_id__get",
    description: `Get a specific tag for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "tag_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: TagRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/tag/:tag_id",
    alias: "update_tag_api_v1_assessments__assessment_id__tag__tag_id__put",
    description: `Update a specific tag for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TagBase,
      },
      {
        name: "tag_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: TagRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/assessments/:assessment_id/tag/:tag_id/delete",
    alias:
      "toggle_tag_delete_api_v1_assessments__assessment_id__tag__tag_id__delete_put",
    description: `Toggle the deleted flag for a specific tag for an assessment.`,
    requestFormat: "json",
    parameters: [
      {
        name: "tag_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "assessment_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/auth/logout",
    alias: "logout_api_v1_auth_logout_post",
    description: `Logout the authenticated user.`,
    requestFormat: "json",
    response: z.object({ message: z.string() }).passthrough(),
  },
  {
    method: "post",
    path: "/api/v1/auth/mfa",
    alias: "validate_mfa_api_v1_auth_mfa_post",
    description: `Validate MFA token and issue a new jwt with MFA verified claim.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z
          .object({
            otp: z
              .string()
              .min(6)
              .max(6)
              .regex(/^\d{6}$/),
          })
          .passthrough(),
      },
    ],
    response: Token,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/v1/auth/mfa/setup",
    alias: "setup_mfa_api_v1_auth_mfa_setup_post",
    description: `Setup MFA for the authenticated user.
Returns a provisioning URI for QR code generation.`,
    requestFormat: "json",
    response: MFASetupResponse,
  },
  {
    method: "post",
    path: "/api/v1/auth/mfa/setup/validate",
    alias: "validate_mfa_setup_api_v1_auth_mfa_setup_validate_post",
    description: `Validate MFA setup for the authenticated user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z
          .object({
            otp: z
              .string()
              .min(6)
              .max(6)
              .regex(/^\d{6}$/),
          })
          .passthrough(),
      },
    ],
    response: Token,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/auth/motd",
    alias: "get_motd_api_v1_auth_motd_get",
    description: `Get the welcome message of the day.`,
    requestFormat: "json",
    response: z.object({ message: z.string() }).passthrough(),
  },
  {
    method: "get",
    path: "/api/v1/auth/providers",
    alias: "get_providers_api_v1_auth_providers_get",
    description: `Get a list of available external authentication providers.`,
    requestFormat: "json",
    response: z.array(ExternalAuthProvider),
  },
  {
    method: "post",
    path: "/api/v1/auth/token",
    alias: "login_api_v1_auth_token_post",
    description: `Login the user and issue a new token.`,
    requestFormat: "form-url",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: Body_login_api_v1_auth_token_post,
      },
    ],
    response: Token,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/campaign_template/",
    alias: "get_campaign_templates_api_v1_campaign_template__get",
    description: `Get all campaign templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: name,
      },
    ],
    response: PaginatedResponse_CampaignTemplateRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/campaign_template/:campaign_template_id",
    alias:
      "get_campaign_template_api_v1_campaign_template__campaign_template_id__get",
    description: `Get a single campaign template by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "campaign_template_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: CampaignTemplateRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/evaluation_template/",
    alias: "get_evaluation_templates_api_v1_evaluation_template__get",
    description: `Get all evaluation question templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "evaluation_criteria",
        type: "Query",
        schema: name,
      },
      {
        name: "description",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: name,
      },
    ],
    response: PaginatedResponse_EvaluationTemplateRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/evaluation_template/:evaluation_template_id",
    alias:
      "get_evaluation_template_by_id_api_v1_evaluation_template__evaluation_template_id__get",
    description: `Get evaluation question template by id.`,
    requestFormat: "json",
    parameters: [
      {
        name: "evaluation_template_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: EvaluationTemplateRead,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/health/",
    alias: "health_check_api_v1_health__get",
    description: `Check the health of the server and database.`,
    requestFormat: "json",
    response: z.object({ message: z.string() }).passthrough(),
  },
  {
    method: "get",
    path: "/api/v1/knowledge-base/",
    alias: "get_knowledge_base_articles_api_v1_knowledge_base__get",
    description: `Get knowledge base articles.`,
    requestFormat: "json",
    parameters: [
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
      {
        name: "mitre_technique_id",
        type: "Query",
        schema: name,
      },
      {
        name: "names",
        type: "Query",
        schema: names,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__2,
      },
    ],
    response: PaginatedResponse_KnowledgeBaseRead_,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/mitre/tactics",
    alias: "read_tactics_api_v1_mitre_tactics_get",
    description: `Get all tactics`,
    requestFormat: "json",
    parameters: [
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_id",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__3,
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
    ],
    response: z.array(TacticBase),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/mitre/tactics-with-techniques",
    alias:
      "read_tactics_with_techniques_api_v1_mitre_tactics_with_techniques_get",
    description: `Get tactics with its associated techniques.`,
    requestFormat: "json",
    parameters: [
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_id",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__3,
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
    ],
    response: z.array(TacticWithTechniques),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/mitre/techniques",
    alias: "read_techniques_api_v1_mitre_techniques_get",
    description: `Get all techniques`,
    requestFormat: "json",
    parameters: [
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_id",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__3,
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
    ],
    response: z.array(TechniqueBase),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/mitre/techniques-with-tactics",
    alias:
      "read_techniques_with_tactics_api_v1_mitre_techniques_with_tactics_get",
    description: `Get techniques with its associated tactics.`,
    requestFormat: "json",
    parameters: [
      {
        name: "name",
        type: "Query",
        schema: name,
      },
      {
        name: "mitre_id",
        type: "Query",
        schema: name,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: sort_by__3,
      },
      {
        name: "sort_order",
        type: "Query",
        schema: sort_order,
      },
    ],
    response: z.array(TechniqueWithTactics),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/report_template/",
    alias: "get_report_templates_api_v1_report_template__get",
    description: `Get all report templates.`,
    requestFormat: "json",
    parameters: [
      {
        name: "filename",
        type: "Query",
        schema: name,
      },
      {
        name: "format",
        type: "Query",
        schema: format,
      },
      {
        name: "sort_by",
        type: "Query",
        schema: z.enum(["filename", "format"]).optional().default("filename"),
      },
      {
        name: "sort_order",
        type: "Query",
        schema: z.enum(["asc", "desc"]).optional().default("asc"),
      },
    ],
    response: z.array(ReportTemplateRead),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/v1/user/me",
    alias: "read_user_self_api_v1_user_me_get",
    description: `Get the authenticated user, and the corresponding ACLs.`,
    requestFormat: "json",
    response: UserReadAcl,
  },
  {
    method: "put",
    path: "/api/v1/user/me/mfa",
    alias: "reset_user_mfa_self_api_v1_user_me_mfa_put",
    description: `Reset the authenticated user&#x27;s MFA.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ password: z.string() }).passthrough(),
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/api/v1/user/me/password",
    alias: "update_user_password_self_api_v1_user_me_password_put",
    description: `Update the authenticated user&#x27;s password.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserPasswordUpdate,
      },
    ],
    response: z.object({ message: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
]);

export const api = new Zodios(endpoints);

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options);
}

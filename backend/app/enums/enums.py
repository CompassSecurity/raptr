import enum


class UserRole(str, enum.Enum):
    """
    Possible user roles
    """

    ADMIN = "admin"
    USER = "user"


class EvaluationResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "n/a"


class AclRole(str, enum.Enum):
    """
    Possible acl roles
    """

    RED = "red"
    BLUE = "blue"
    SPECTATOR = "spectator"


class ActivitySeverity(str, enum.Enum):
    """
    Possible activity severity levels
    """

    INFORMATIONAL = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ActivityPriority(str, enum.Enum):
    """
    Possible activity priority levels
    """

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ActivityState(str, enum.Enum):
    """
    Possible activity state levels
    """

    PENDING = "Pending"
    WAITING_RED = "Waiting Red"
    WAITING_BLUE = "Waiting Blue"
    READY = "Ready"
    IN_PROGRESS = "In Progress"
    IN_EVALUATION = "In Evaluation"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ActivityStateBlue(str, enum.Enum):
    """
    Possible activity state levels for Blue users
    """

    WAITING_RED = "Waiting Red"
    WAITING_BLUE = "Waiting Blue"


class ActivityAssetRole(str, enum.Enum):
    """
    Possible asset roles in an activity
    """

    SOURCE = "source"
    TARGET = "target"
    TOOL = "tool"
    LOG_SOURCE = "log_source"
    PREVENTION_SOURCE = "prevention_source"
    ALERT_SOURCE = "alert_source"
    STAKEHOLDER_NOTIFICATION_SOURCE = "stakeholder_notification_source"


class AssessmentType(str, enum.Enum):
    """
    Possible assessment types
    """

    PurpleTeam = "PurpleTeam"
    RedTeam = "RedTeam"


class ReportTemplateFormat(str, enum.Enum):
    """
    Possible report template formats
    """

    HTML = "html"
    DOCX = "docx"


class FileCategory(str, enum.Enum):
    """
    Possible file categories
    """

    RED = "red"
    BLUE = "blue"


class FileType(str, enum.Enum):
    """
    Possible file types
    """

    PNG = "image/png"
    JPEG = "image/jpeg"
    JPG = "image/jpg"
    TXT = "text/plain"


class CampaignTemplateItemType(str, enum.Enum):
    """
    Possible campaign template item types
    """

    GROUP = "group"
    ACTIVITY = "activity"

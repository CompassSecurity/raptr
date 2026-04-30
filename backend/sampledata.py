#!/usr/bin/env python3
"""
Sample Data Script for RAPTR Backend

This script creates consistent, reproducible test data in the PostgreSQL database.
All entities use static UUIDs for predictability across runs.

Usage:
    python sampledata.py [--clear]

Options:
    --clear    Clear all existing data before creating sample data (prompts for confirmation)
"""

import argparse
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.password import hash_password
from app.db.session import engine
from app.models.acl import Acl
from app.models.activity import Activity, activity_asset_association
from app.models.activity_evaluation import ActivityEvaluation
from app.models.activity_evaluation_dynamic_questions import (
    ActivityEvaluationDynamicQuestions,
    EvaluationResult,
)
from app.models.activity_group import ActivityGroup
from app.models.assessment import Assessment
from app.models.asset import Asset
from app.models.evaluation_template import EvaluationTemplate
from app.models.tag import Tag
from app.models.user import User

# Static UUIDs for predictable test data
STATIC_IDS = {
    "users": {
        "admin": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "manager": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "regular": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "observer": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "disabled": uuid.UUID("00000000-0000-0000-0000-000000000005"),
    },
    "assets": {
        # Security Assets
        "kali_vm": uuid.UUID("60000000-0000-0000-0000-000000000001"),
        "dc_01": uuid.UUID("60000000-0000-0000-0000-000000000002"),
        "web_01": uuid.UUID("60000000-0000-0000-0000-000000000003"),
        "firewall": uuid.UUID("60000000-0000-0000-0000-000000000004"),
        "nmap_tool": uuid.UUID("60000000-0000-0000-0000-000000000005"),
        "burp_tool": uuid.UUID("60000000-0000-0000-0000-000000000006"),
        "mimikatz_tool": uuid.UUID("60000000-0000-0000-0000-000000000007"),
        "impacket_tool": uuid.UUID("60000000-0000-0000-0000-000000000008"),
        "cobalt_strike": uuid.UUID("60000000-0000-0000-0000-000000000009"),
        "sqlmap_tool": uuid.UUID("60000000-0000-0000-0000-00000000000A"),
        "sec_alert": uuid.UUID("60000000-0000-0000-0000-00000000000B"),
        "sec_incident": uuid.UUID("60000000-0000-0000-0000-00000000000C"),
        # Vulnerability Assets
        "prod_db": uuid.UUID("60000000-0000-0000-0000-000000000010"),
        "nessus_scanner": uuid.UUID("60000000-0000-0000-0000-000000000011"),
        "vuln_prev": uuid.UUID("60000000-0000-0000-0000-000000000012"),
        "vuln_alert": uuid.UUID("60000000-0000-0000-0000-000000000013"),
        "vuln_incident": uuid.UUID("60000000-0000-0000-0000-000000000014"),
        # Compliance Assets
        "siem": uuid.UUID("60000000-0000-0000-0000-000000000020"),  # Used as Target
        "comp_source": uuid.UUID("60000000-0000-0000-0000-000000000021"),
        "comp_tool": uuid.UUID("60000000-0000-0000-0000-000000000022"),
        "comp_prev": uuid.UUID("60000000-0000-0000-0000-000000000023"),
        "comp_alert": uuid.UUID("60000000-0000-0000-0000-000000000024"),
        "comp_incident": uuid.UUID("60000000-0000-0000-0000-000000000025"),
    },
    "assessments": {
        "security": uuid.UUID("10000000-0000-0000-0000-000000000001"),
        "vulnerability": uuid.UUID("10000000-0000-0000-0000-000000000002"),
        "compliance": uuid.UUID("10000000-0000-0000-0000-000000000003"),
    },
    "tags": {
        "security_critical": uuid.UUID("20000000-0000-0000-0000-000000000001"),
        "security_high": uuid.UUID("20000000-0000-0000-0000-000000000002"),
        "security_network": uuid.UUID("20000000-0000-0000-0000-000000000003"),
        "security_endpoint": uuid.UUID("20000000-0000-0000-0000-000000000004"),
        "vuln_critical": uuid.UUID("20000000-0000-0000-0000-000000000011"),
        "vuln_high": uuid.UUID("20000000-0000-0000-0000-000000000012"),
        "vuln_Medium": uuid.UUID("20000000-0000-0000-0000-000000000013"),
        "vuln_low": uuid.UUID("20000000-0000-0000-0000-000000000014"),
        "comp_required": uuid.UUID("20000000-0000-0000-0000-000000000021"),
        "comp_optional": uuid.UUID("20000000-0000-0000-0000-000000000022"),
        "comp_audit": uuid.UUID("20000000-0000-0000-0000-000000000023"),
    },
    "activity_groups": {
        "security_default": uuid.UUID("30000000-0000-0000-0000-000000000000"),
        "security_recon": uuid.UUID("30000000-0000-0000-0000-000000000001"),
        "security_exploit": uuid.UUID("30000000-0000-0000-0000-000000000002"),
        "vuln_default": uuid.UUID("30000000-0000-0000-0000-000000000010"),
        "vuln_scan": uuid.UUID("30000000-0000-0000-0000-000000000011"),
        "vuln_validate": uuid.UUID("30000000-0000-0000-0000-000000000012"),
        "comp_default": uuid.UUID("30000000-0000-0000-0000-000000000020"),
        "comp_review": uuid.UUID("30000000-0000-0000-0000-000000000021"),
        "comp_remediate": uuid.UUID("30000000-0000-0000-0000-000000000022"),
    },
    "activities": {
        # Security Assessment Activities
        "sec_act_1": uuid.UUID("40000000-0000-0000-0000-000000000001"),
        "sec_act_2": uuid.UUID("40000000-0000-0000-0000-000000000002"),
        "sec_act_3": uuid.UUID("40000000-0000-0000-0000-000000000003"),
        "sec_act_4": uuid.UUID("40000000-0000-0000-0000-000000000004"),
        "sec_act_5": uuid.UUID("40000000-0000-0000-0000-000000000005"),
        "sec_act_6": uuid.UUID("40000000-0000-0000-0000-000000000006"),
        # Vulnerability Assessment Activities
        "vuln_act_1": uuid.UUID("40000000-0000-0000-0000-000000000011"),
        "vuln_act_2": uuid.UUID("40000000-0000-0000-0000-000000000012"),
        "vuln_act_3": uuid.UUID("40000000-0000-0000-0000-000000000013"),
        "vuln_act_4": uuid.UUID("40000000-0000-0000-0000-000000000014"),
        "vuln_act_5": uuid.UUID("40000000-0000-0000-0000-000000000015"),
        # Compliance Assessment Activities
        "comp_act_1": uuid.UUID("40000000-0000-0000-0000-000000000021"),
        "comp_act_2": uuid.UUID("40000000-0000-0000-0000-000000000022"),
        "comp_act_3": uuid.UUID("40000000-0000-0000-0000-000000000023"),
        "comp_act_4": uuid.UUID("40000000-0000-0000-0000-000000000024"),
    },
    "acls": {
        "manager_security": uuid.UUID("50000000-0000-0000-0000-000000000001"),
        "manager_vuln": uuid.UUID("50000000-0000-0000-0000-000000000002"),
        "regular_security": uuid.UUID("50000000-0000-0000-0000-000000000003"),
        "regular_comp": uuid.UUID("50000000-0000-0000-0000-000000000004"),
        "observer_vuln": uuid.UUID("50000000-0000-0000-0000-000000000005"),
        "observer_comp": uuid.UUID("50000000-0000-0000-0000-000000000006"),
    },
    "evaluation_templates": {
        "template_1": uuid.UUID("70000000-0000-0000-0000-000000000001"),
        "template_2": uuid.UUID("70000000-0000-0000-0000-000000000002"),
    },
}


def clear_data(session: Session, force: bool = False) -> None:
    """
    Clear all data from the database.

    Args:
        session: Database session
        force: If True, skip confirmation prompt
    """
    if not force:
        print("\n⚠️  WARNING: This will delete ALL data from the database!")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != "yes":
            print("Operation cancelled.")
            sys.exit(0)

    print("\n🗑️  Clearing existing data...")

    # Delete in correct order to respect foreign key constraints
    session.execute(delete(ActivityEvaluationDynamicQuestions))
    session.execute(delete(ActivityEvaluation))
    session.execute(delete(Acl))
    session.execute(delete(Activity))
    session.execute(delete(ActivityGroup))
    session.execute(delete(EvaluationTemplate))
    session.execute(delete(Asset))
    session.execute(delete(Tag))
    session.execute(delete(Assessment))
    # Keep admin user, delete others
    session.execute(delete(User).where(User.email != "admin@raptr.app"))

    session.commit()
    print("✅ Data cleared successfully")


def create_users(session: Session) -> dict[str, User]:
    """Create test users with different roles."""
    print("\n👥 Creating users...")

    admin_id = STATIC_IDS["users"]["admin"]
    now = datetime.now(timezone.utc)

    users_data = [
        {
            "id": admin_id,
            "email": "admin2@raptr.app",
            "password": "Password.123",
            "role": "admin",
            "disabled": False,
            "key": "admin",
        },
        {
            "id": STATIC_IDS["users"]["manager"],
            "email": "manager@raptr.app",
            "password": "Password.123",
            "role": "user",
            "disabled": False,
            "key": "manager",
        },
        {
            "id": STATIC_IDS["users"]["regular"],
            "email": "user@raptr.app",
            "password": "Password.123",
            "role": "user",
            "disabled": False,
            "key": "regular",
        },
        {
            "id": STATIC_IDS["users"]["observer"],
            "email": "observer@raptr.app",
            "password": "Password.123",
            "role": "user",
            "disabled": False,
            "key": "observer",
        },
        {
            "id": STATIC_IDS["users"]["disabled"],
            "email": "disabled@raptr.app",
            "password": "Password.123",
            "role": "user",
            "disabled": True,
            "key": "disabled",
        },
    ]

    users = {}
    for user_data in users_data:
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            role=user_data["role"],
            disabled=user_data["disabled"],
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        users[user_data["key"]] = user
        print(f"  ✓ Created {user_data['role']} user: {user_data['email']}")

    session.commit()
    print(f"✅ Created {len(users)} users")
    return users


def create_assessments(
    session: Session, users: dict[str, User]
) -> dict[str, Assessment]:
    """Create test assessments."""
    print("\n📋 Creating assessments...")

    now = datetime.now(timezone.utc)
    admin_id = users["admin"].id

    assessments_data = [
        {
            "id": STATIC_IDS["assessments"]["security"],
            "name": "Security Red Team Assessment Q1 2026",
            "description": "Comprehensive red team security assessment focusing on network penetration and lateral movement capabilities.",
            "assessment_type": "RedTeam",
            "key": "security",
        },
        {
            "id": STATIC_IDS["assessments"]["vulnerability"],
            "name": "Vulnerability Assessment - Infrastructure",
            "description": "Purple team vulnerability assessment of critical infrastructure components and services.",
            "assessment_type": "PurpleTeam",
            "key": "vulnerability",
        },
        {
            "id": STATIC_IDS["assessments"]["compliance"],
            "name": "Compliance Audit - SOC 2",
            "description": "Purple team compliance audit for SOC 2 Type II certification requirements.",
            "assessment_type": "PurpleTeam",
            "key": "compliance",
        },
    ]

    assessments = {}
    for assessment_data in assessments_data:
        assessment = Assessment(
            id=assessment_data["id"],
            name=assessment_data["name"],
            description=assessment_data["description"],
            assessment_type=assessment_data["assessment_type"],
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(assessment)
        assessments[assessment_data["key"]] = assessment
        print(f"  ✓ Created assessment: {assessment_data['name']}")

    session.commit()
    print(f"✅ Created {len(assessments)} assessments")
    return assessments


def create_tags(
    session: Session, assessments: dict[str, Assessment], admin_id: uuid.UUID
) -> dict[str, Tag]:
    """Create tags for assessments."""
    print("\n🏷️  Creating tags...")

    now = datetime.now(timezone.utc)

    tags_data = [
        # Security Assessment Tags
        {
            "id": STATIC_IDS["tags"]["security_critical"],
            "name": "Critical",
            "color": "#dc2626",
            "assessment": "security",
            "key": "security_critical",
        },
        {
            "id": STATIC_IDS["tags"]["security_high"],
            "name": "High Priority",
            "color": "#ea580c",
            "assessment": "security",
            "key": "security_high",
        },
        {
            "id": STATIC_IDS["tags"]["security_network"],
            "name": "Network",
            "color": "#2563eb",
            "assessment": "security",
            "key": "security_network",
        },
        {
            "id": STATIC_IDS["tags"]["security_endpoint"],
            "name": "Endpoint",
            "color": "#7c3aed",
            "assessment": "security",
            "key": "security_endpoint",
        },
        # Vulnerability Assessment Tags
        {
            "id": STATIC_IDS["tags"]["vuln_critical"],
            "name": "Critical",
            "color": "#991b1b",
            "assessment": "vulnerability",
            "key": "vuln_critical",
        },
        {
            "id": STATIC_IDS["tags"]["vuln_high"],
            "name": "High",
            "color": "#c2410c",
            "assessment": "vulnerability",
            "key": "vuln_high",
        },
        {
            "id": STATIC_IDS["tags"]["vuln_Medium"],
            "name": "Medium",
            "color": "#ca8a04",
            "assessment": "vulnerability",
            "key": "vuln_Medium",
        },
        {
            "id": STATIC_IDS["tags"]["vuln_low"],
            "name": "Low",
            "color": "#65a30d",
            "assessment": "vulnerability",
            "key": "vuln_low",
        },
        # Compliance Assessment Tags
        {
            "id": STATIC_IDS["tags"]["comp_required"],
            "name": "Required",
            "color": "#be123c",
            "assessment": "compliance",
            "key": "comp_required",
        },
        {
            "id": STATIC_IDS["tags"]["comp_optional"],
            "name": "Optional",
            "color": "#0891b2",
            "assessment": "compliance",
            "key": "comp_optional",
        },
        {
            "id": STATIC_IDS["tags"]["comp_audit"],
            "name": "Audit",
            "color": "#4f46e5",
            "assessment": "compliance",
            "key": "comp_audit",
        },
    ]

    tags = {}
    for tag_data in tags_data:
        tag = Tag(
            id=tag_data["id"],
            name=tag_data["name"],
            color=tag_data["color"],
            assessment_id=assessments[tag_data["assessment"]].id,
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(tag)
        tags[tag_data["key"]] = tag
        print(
            f"  ✓ Created tag: {tag_data['name']} for {tag_data['assessment']} assessment"
        )

    session.commit()
    session.commit()
    print(f"✅ Created {len(tags)} tags")
    return tags


def create_assets(
    session: Session, assessments: dict[str, Assessment], admin_id: uuid.UUID
) -> dict[str, Asset]:
    """Create assets for assessments."""
    print("\n💻 Creating assets...")

    now = datetime.now(timezone.utc)

    assets_data = [
        # Security Assessment Assets
        {
            "id": STATIC_IDS["assets"]["kali_vm"],
            "name": "Kali Linux VM (Attacker)",
            "assessment": "security",
            "icon": "Laptop",
            "key": "kali_vm",
        },
        {
            "id": STATIC_IDS["assets"]["dc_01"],
            "name": "DC-01 (Domain Controller)",
            "assessment": "security",
            "icon": "Server",
            "key": "dc_01",
        },
        {
            "id": STATIC_IDS["assets"]["web_01"],
            "name": "WEB-01 (IIS Server)",
            "assessment": "security",
            "icon": "Server",
            "key": "web_01",
        },
        {
            "id": STATIC_IDS["assets"]["firewall"],
            "name": "Edge Firewall",
            "assessment": "security",
            "icon": "Shield",
            "key": "firewall",
        },
        {
            "id": STATIC_IDS["assets"]["nmap_tool"],
            "name": "Nmap Scanner",
            "assessment": "security",
            "icon": "Terminal",
            "key": "nmap_tool",
        },
        {
            "id": STATIC_IDS["assets"]["mimikatz_tool"],
            "name": "Mimikatz",
            "assessment": "security",
            "icon": "Key",
            "key": "mimikatz_tool",
        },
        {
            "id": STATIC_IDS["assets"]["impacket_tool"],
            "name": "Impacket Suite",
            "assessment": "security",
            "icon": "Tool",
            "key": "impacket_tool",
        },
        {
            "id": STATIC_IDS["assets"]["cobalt_strike"],
            "name": "Cobalt Strike Beacon",
            "assessment": "security",
            "icon": "Zap",
            "key": "cobalt_strike",
        },
        {
            "id": STATIC_IDS["assets"]["sec_alert"],
            "name": "Splunk SIEM (Sec)",
            "assessment": "security",
            "icon": "Activity",
            "key": "sec_alert",
        },
        {
            "id": STATIC_IDS["assets"]["sec_incident"],
            "name": "JIRA Security Board",
            "assessment": "security",
            "icon": "Clipboard",
            "key": "sec_incident",
        },
        # Vulnerability Assessment Assets
        {
            "id": STATIC_IDS["assets"]["prod_db"],
            "name": "PROD-DB-01",
            "assessment": "vulnerability",
            "icon": "Database",
            "key": "prod_db",
        },
        {
            "id": STATIC_IDS["assets"]["nessus_scanner"],
            "name": "Nessus Scanner",
            "assessment": "vulnerability",
            "icon": "Search",
            "key": "nessus_scanner",
        },
        {
            "id": STATIC_IDS["assets"]["burp_tool"],
            "name": "Burp Suite Pro",
            "assessment": "vulnerability",
            "icon": "Bug",
            "key": "burp_tool",
        },
        {
            "id": STATIC_IDS["assets"]["sqlmap_tool"],
            "name": "SQLMap",
            "assessment": "vulnerability",
            "icon": "Database",
            "key": "sqlmap_tool",
        },
        {
            "id": STATIC_IDS["assets"]["vuln_prev"],
            "name": "AWS WAF",
            "assessment": "vulnerability",
            "icon": "Shield",
            "key": "vuln_prev",
        },
        {
            "id": STATIC_IDS["assets"]["vuln_alert"],
            "name": "Datadog",
            "assessment": "vulnerability",
            "icon": "Activity",
            "key": "vuln_alert",
        },
        {
            "id": STATIC_IDS["assets"]["vuln_incident"],
            "name": "ServiceNow",
            "assessment": "vulnerability",
            "icon": "Clipboard",
            "key": "vuln_incident",
        },
        # Compliance Assessment Assets
        {
            "id": STATIC_IDS["assets"]["siem"],
            "name": "Central SIEM",
            "assessment": "compliance",
            "icon": "Activity",
            "key": "siem",
        },
        {
            "id": STATIC_IDS["assets"]["comp_source"],
            "name": "Auditor Laptop",
            "assessment": "compliance",
            "icon": "Laptop",
            "key": "comp_source",
        },
        {
            "id": STATIC_IDS["assets"]["comp_tool"],
            "name": "Audit Checklist",
            "assessment": "compliance",
            "icon": "FileText",
            "key": "comp_tool",
        },
        {
            "id": STATIC_IDS["assets"]["comp_prev"],
            "name": "Access Policy Doc",
            "assessment": "compliance",
            "icon": "Lock",
            "key": "comp_prev",
        },
        {
            "id": STATIC_IDS["assets"]["comp_alert"],
            "name": "Compliance Dashboard",
            "assessment": "compliance",
            "icon": "Layout",
            "key": "comp_alert",
        },
        {
            "id": STATIC_IDS["assets"]["comp_incident"],
            "name": "Audit Finding Log",
            "assessment": "compliance",
            "icon": "Clipboard",
            "key": "comp_incident",
        },
    ]

    assets = {}
    for asset_data in assets_data:
        asset = Asset(
            id=asset_data["id"],
            name=asset_data["name"],
            icon=asset_data.get("icon"),
            assessment_id=assessments[asset_data["assessment"]].id,
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(asset)
        assets[asset_data["key"]] = asset
        print(f"  ✓ Created asset: {asset_data['name']}")

    session.commit()
    print(f"✅ Created {len(assets)} assets")
    return assets


def create_activity_groups(
    session: Session, assessments: dict[str, Assessment], admin_id: uuid.UUID
) -> dict[str, ActivityGroup]:
    """Create activity groups for assessments."""
    print("\n📁 Creating activity groups...")

    now = datetime.now(timezone.utc)

    groups_data = [
        # Security Assessment Groups
        {
            "id": STATIC_IDS["activity_groups"]["security_default"],
            "name": "Ungrouped",
            "assessment": "security",
            "visible": True,
            "activity_group_position": 0,
            "is_default": True,
            "key": "security_default",
        },
        {
            "id": STATIC_IDS["activity_groups"]["security_recon"],
            "name": "Reconnaissance Phase",
            "assessment": "security",
            "visible": True,
            "activity_group_position": 1,
            "key": "security_recon",
        },
        {
            "id": STATIC_IDS["activity_groups"]["security_exploit"],
            "name": "Exploitation Phase",
            "assessment": "security",
            "visible": True,
            "activity_group_position": 2,
            "key": "security_exploit",
        },
        # Vulnerability Assessment Groups
        {
            "id": STATIC_IDS["activity_groups"]["vuln_default"],
            "name": "Ungrouped",
            "assessment": "vulnerability",
            "visible": True,
            "activity_group_position": 0,
            "is_default": True,
            "key": "vuln_default",
        },
        {
            "id": STATIC_IDS["activity_groups"]["vuln_scan"],
            "name": "Vulnerability Scanning",
            "assessment": "vulnerability",
            "visible": True,
            "activity_group_position": 1,
            "key": "vuln_scan",
        },
        {
            "id": STATIC_IDS["activity_groups"]["vuln_validate"],
            "name": "Validation & Testing",
            "assessment": "vulnerability",
            "visible": True,
            "activity_group_position": 2,
            "key": "vuln_validate",
        },
        # Compliance Assessment Groups
        {
            "id": STATIC_IDS["activity_groups"]["comp_default"],
            "name": "Ungrouped",
            "assessment": "compliance",
            "visible": True,
            "activity_group_position": 0,
            "is_default": True,
            "key": "comp_default",
        },
        {
            "id": STATIC_IDS["activity_groups"]["comp_review"],
            "name": "Policy Review",
            "assessment": "compliance",
            "visible": True,
            "activity_group_position": 1,
            "key": "comp_review",
        },
        {
            "id": STATIC_IDS["activity_groups"]["comp_remediate"],
            "name": "Remediation Tasks",
            "assessment": "compliance",
            "activity_group_position": 2,
            "visible": True,
            "key": "comp_remediate",
        },
    ]

    groups = {}
    for group_data in groups_data:
        group = ActivityGroup(
            id=group_data["id"],
            name=group_data["name"],
            assessment_id=assessments[group_data["assessment"]].id,
            visible=group_data["visible"],
            is_default=group_data.get("is_default", False),
            activity_group_position=group_data.get("activity_group_position", 0),
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(group)
        groups[group_data["key"]] = group
        print(
            f"  ✓ Created activity group: {group_data['name']} for {group_data['assessment']} assessment"
        )

    session.commit()
    print(f"✅ Created {len(groups)} activity groups")
    return groups


def create_activities(
    session: Session,
    assessments: dict[str, Assessment],
    groups: dict[str, ActivityGroup],
    tags: dict[str, Tag],
    assets: dict[str, Asset],
    admin_id: uuid.UUID,
    evaluation_templates: dict[str, EvaluationTemplate] = {},
) -> dict[str, Activity]:
    """Create activities with tags."""
    print("\n⚡ Creating activities...")

    now = datetime.now(timezone.utc)
    base_time = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

    activities_data = [
        # Security Assessment Activities
        {
            "id": STATIC_IDS["activities"]["sec_act_1"],
            "name": "Network Reconnaissance - Port Scanning",
            "assessment": "security",
            "group": "security_recon",
            "position": 1,
            "mitre_tactic": "TA0043",
            "mitre_technique": "T1046",
            "state": "Pending",
            "visible": True,
            "priority": "High",
            "provider": "Nmap",
            "activity_rationale": "Identify open ports and services on target network",
            "activity_actions": "Run nmap -sV -sC -p- against target range",
            "expected_prevention": False,
            "expected_alert_creation": True,
            "expected_severity": "Medium",
            "logged": True,
            "prevented": False,
            "alerted": True,
            "alert_severity": "Medium",
            "start_offset": 0,
            "end_offset": 2,
            "tags": ["security_network", "security_high"],
            "assets": [
                {"role": "source", "key": "kali_vm"},
                {"role": "target", "key": "dc_01"},
                {"role": "tool", "key": "nmap_tool"},
            ],
            "evaluation": {
                "logged_evaluation": True,
                "alerted_evaluation": True,
                "prevented_evaluation": False,
                "stakeholder_notified_evaluation": False,
                "activity_coverage_score": 100,
                "event_to_alert_data": "Network scan detected by IDS",
                "event_to_alert_evaluation_result": EvaluationResult.PASS,
                "alert_severity_evaluation_result": EvaluationResult.PASS,
            },
            "key": "sec_act_1",
        },
        {
            "id": STATIC_IDS["activities"]["sec_act_2"],
            "name": "Service Enumeration - SMB Discovery",
            "assessment": "security",
            "group": "security_recon",
            "position": 2,
            "mitre_tactic": "TA0043",
            "mitre_technique": "T1135",
            "state": "Pending",
            "visible": True,
            "priority": "High",
            "provider": "CrackMapExec",
            "activity_rationale": "Enumerate SMB shares and permissions",
            "activity_actions": "Execute crackmapexec smb targets --shares",
            "expected_prevention": False,
            "expected_alert_creation": True,
            "expected_severity": "Low",
            "logged": True,
            "prevented": False,
            "alerted": True,
            "alert_severity": "Low",
            "start_offset": 3,
            "end_offset": 4,
            "tags": ["security_network"],
            "assets": [
                {"role": "source", "key": "kali_vm"},
                {"role": "target", "key": "web_01"},
            ],
            "key": "sec_act_2",
        },
        {
            "id": STATIC_IDS["activities"]["sec_act_3"],
            "name": "Credential Dumping - LSASS Memory",
            "assessment": "security",
            "group": "security_exploit",
            "position": 1,
            "mitre_tactic": "TA0006",
            "mitre_technique": "T1003.001",
            "state": "Pending",
            "visible": True,
            "priority": "High",
            "provider": "Mimikatz",
            "activity_rationale": "Extract credentials from LSASS process memory",
            "activity_actions": "Run mimikatz sekurlsa::logonpasswords",
            "expected_prevention": True,
            "expected_alert_creation": True,
            "expected_severity": "Critical",
            "logged": False,
            "prevented": False,
            "alerted": False,
            "start_offset": 5,
            "end_offset": None,
            "tags": ["security_critical", "security_endpoint"],
            "assets": [
                {"role": "source", "key": "kali_vm"},
                {"role": "target", "key": "dc_01"},
                {"role": "tool", "key": "mimikatz_tool"},
            ],
            "evaluation": {
                "logged_evaluation": False,
                "alerted_evaluation": False,
                "prevented_evaluation": False,
                "stakeholder_notified_evaluation": False,
                "activity_coverage_score": 0,
                "event_to_alert_data": "No logs found",
                "event_to_alert_evaluation_result": EvaluationResult.FAIL,
            },
            "key": "sec_act_3",
        },
        {
            "id": STATIC_IDS["activities"]["sec_act_4"],
            "name": "Lateral Movement - PsExec",
            "assessment": "security",
            "group": "security_exploit",
            "position": 2,
            "mitre_tactic": "TA0008",
            "mitre_technique": "T1021.002",
            "state": "Pending",
            "visible": True,
            "priority": "High",
            "provider": "Impacket",
            "activity_rationale": "Test lateral movement capabilities using PsExec",
            "activity_actions": "Use impacket-psexec to access remote system",
            "expected_prevention": True,
            "expected_alert_creation": True,
            "expected_severity": "High",
            "start_offset": None,
            "end_offset": None,
            "tags": ["security_critical", "security_network"],
            "assets": [
                {"role": "source", "key": "kali_vm"},
                {"role": "target", "key": "dc_01"},
                {"role": "tool", "key": "impacket_tool"},
            ],
            "key": "sec_act_4",
        },
        {
            "id": STATIC_IDS["activities"]["sec_act_5"],
            "name": "Privilege Escalation - Token Impersonation",
            "assessment": "security",
            "group": "security_exploit",
            "position": 3,
            "mitre_tactic": "TA0004",
            "mitre_technique": "T1134",
            "state": "Pending",
            "visible": False,
            "priority": "High",
            "provider": "Cobalt Strike",
            "activity_rationale": "Escalate privileges through token impersonation",
            "activity_actions": "Steal and impersonate SYSTEM token",
            "expected_prevention": True,
            "expected_alert_creation": True,
            "expected_severity": "High",
            "start_offset": None,
            "end_offset": None,
            "tags": ["security_high", "security_endpoint"],
            "assets": [
                {"role": "source", "key": "kali_vm"},
                {"role": "target", "key": "dc_01"},
                {"role": "tool", "key": "cobalt_strike"},
            ],
            "key": "sec_act_5",
        },
        {
            "id": STATIC_IDS["activities"]["sec_act_6"],
            "name": "Data Exfiltration - DNS Tunneling",
            "assessment": "security",
            "group": "security_exploit",
            "position": 4,
            "mitre_tactic": "TA0010",
            "mitre_technique": "T1048.003",
            "state": "Waiting Red",
            "visible": True,
            "priority": "High",
            "provider": "dnscat2",
            "activity_rationale": "Test data exfiltration via DNS tunneling",
            "activity_actions": "Setup dnscat2 tunnel and exfiltrate test data",
            "expected_prevention": True,
            "expected_alert_creation": True,
            "expected_severity": "High",
            "start_offset": None,
            "end_offset": None,
            "tags": ["security_high", "security_network"],
            "assets": [
                {"role": "source", "key": "web_01"},
                {"role": "target", "key": "kali_vm"},
            ],
            "key": "sec_act_6",
        },
        # Vulnerability Assessment Activities
        {
            "id": STATIC_IDS["activities"]["vuln_act_1"],
            "name": "Infrastructure Vulnerability Scan",
            "assessment": "vulnerability",
            "group": "vuln_scan",
            "position": 1,
            "mitre_tactic": "TA0043",
            "mitre_technique": "T1595",
            "state": "Completed",
            "visible": True,
            "priority": "High",
            "provider": "Nessus",
            "activity_rationale": "Comprehensive vulnerability scan of infrastructure",
            "activity_actions": "Run full credentialed Nessus scan",
            "expected_prevention": False,
            "expected_alert_creation": False,
            "expected_severity": "Informational",
            "logged": True,
            "prevented": False,
            "alerted": False,
            "start_offset": 0,
            "end_offset": 5,
            "tags": ["vuln_critical", "vuln_high"],
            "assets": [
                {"role": "source", "key": "nessus_scanner"},
                {"role": "target", "key": "prod_db"},
            ],
            "key": "vuln_act_1",
        },
        {
            "id": STATIC_IDS["activities"]["vuln_act_2"],
            "name": "Web Application Security Scan",
            "assessment": "vulnerability",
            "group": "vuln_scan",
            "position": 2,
            "mitre_tactic": "TA0043",
            "mitre_technique": "T1595.002",
            "state": "Waiting Blue",
            "visible": True,
            "priority": "High",
            "provider": "Burp Suite",
            "activity_rationale": "Identify web application vulnerabilities",
            "activity_actions": "Run Burp Suite active scan on web applications",
            "expected_prevention": False,
            "expected_alert_creation": True,
            "expected_severity": "Low",
            "logged": True,
            "prevented": False,
            "alerted": True,
            "alert_severity": "Low",
            "start_offset": 6,
            "end_offset": 10,
            "tags": ["vuln_high", "vuln_Medium"],
            "assets": [
                {"role": "tool", "key": "burp_tool"},
            ],
            "key": "vuln_act_2",
        },
        {
            "id": STATIC_IDS["activities"]["vuln_act_3"],
            "name": "SQL Injection Testing",
            "assessment": "vulnerability",
            "group": "vuln_validate",
            "position": 1,
            "mitre_tactic": "TA0001",
            "mitre_technique": "T1190",
            "state": "Cancelled",
            "visible": True,
            "priority": "High",
            "provider": "SQLMap",
            "activity_rationale": "Validate SQL injection vulnerabilities",
            "activity_actions": "Use sqlmap to test for SQL injection",
            "expected_prevention": True,
            "expected_alert_creation": True,
            "expected_severity": "Critical",
            "logged": True,
            "prevented": True,
            "alerted": True,
            "alert_severity": "Critical",
            "start_offset": 11,
            "end_offset": None,
            "tags": ["vuln_critical"],
            "assets": [
                {"role": "target", "key": "prod_db"},
                {"role": "tool", "key": "sqlmap_tool"},
            ],
            "evaluation": {
                "logged_evaluation": True,
                "alerted_evaluation": True,
                "prevented_evaluation": True,
                "stakeholder_notified_evaluation": True,
                "activity_coverage_score": 100,
                "event_to_alert_data": "WAF blocked SQL Injection attempt",
                "event_to_alert_evaluation_result": EvaluationResult.PASS,
                "alert_severity_evaluation_result": EvaluationResult.PASS,
                "stakeholder_notification_severity_data": "Critical",
                "stakeholder_notification_severity_evaluation_result": EvaluationResult.PASS,
            },
            "key": "vuln_act_3",
        },
        {
            "id": STATIC_IDS["activities"]["vuln_act_4"],
            "name": "Privilege Escalation Testing - Linux",
            "assessment": "vulnerability",
            "group": "vuln_validate",
            "position": 2,
            "mitre_tactic": "TA0004",
            "mitre_technique": "T1068",
            "state": "Ready",
            "visible": True,
            "priority": "High",
            "provider": "LinPEAS",
            "activity_rationale": "Test for privilege escalation vectors on Linux systems",
            "activity_actions": "Run LinPEAS and attempt identified vectors",
            "expected_prevention": True,
            "expected_alert_creation": True,
            "expected_severity": "High",
            "start_offset": None,
            "end_offset": None,
            "tags": ["vuln_high"],
            "assets": [
                {"role": "target", "key": "prod_db"},
            ],
            "key": "vuln_act_4",
        },
        {
            "id": STATIC_IDS["activities"]["vuln_act_5"],
            "name": "Container Security Assessment",
            "assessment": "vulnerability",
            "group": "vuln_validate",
            "position": 3,
            "mitre_tactic": "TA0043",
            "mitre_technique": "T1613",
            "state": "In Progress",
            "visible": True,
            "priority": "Medium",
            "provider": "Trivy",
            "activity_rationale": "Assess container images for vulnerabilities",
            "activity_actions": "Scan all production containers with Trivy",
            "expected_prevention": False,
            "expected_alert_creation": False,
            "expected_severity": "Informational",
            "start_offset": None,
            "end_offset": None,
            "tags": ["vuln_Medium", "vuln_low"],
            "assets": [
                {"role": "target", "key": "prod_db"},
            ],
            "key": "vuln_act_5",
        },
        # Compliance Assessment Activities
        {
            "id": STATIC_IDS["activities"]["comp_act_1"],
            "name": "Access Control Review",
            "assessment": "compliance",
            "group": "comp_review",
            "position": 1,
            "mitre_tactic": "TA0006",
            "mitre_technique": "T1078",
            "state": "Completed",
            "visible": True,
            "priority": "High",
            "provider": "Manual",
            "activity_rationale": "Review access controls for SOC 2 compliance",
            "activity_actions": "Audit user permissions and access logs",
            "expected_prevention": False,
            "expected_alert_creation": False,
            "expected_severity": "Informational",
            "logged": True,
            "prevented": False,
            "alerted": False,
            "start_offset": 0,
            "end_offset": 3,
            "tags": ["comp_required", "comp_audit"],
            "assets": [
                {"role": "target", "key": "siem"},
            ],
            "key": "comp_act_1",
        },
        {
            "id": STATIC_IDS["activities"]["comp_act_2"],
            "name": "Logging and Monitoring Review",
            "assessment": "compliance",
            "group": "comp_review",
            "position": 2,
            "mitre_tactic": "TA0009",
            "mitre_technique": "T1562.002",
            "state": "Pending",
            "visible": True,
            "priority": "High",
            "provider": "Manual",
            "activity_rationale": "Verify logging meets SOC 2 requirements",
            "activity_actions": "Review SIEM configuration and log retention",
            "expected_prevention": False,
            "expected_alert_creation": False,
            "expected_severity": "Informational",
            "start_offset": 4,
            "end_offset": None,
            "tags": ["comp_required"],
            "assets": [
                {"role": "target", "key": "siem"},
            ],
            "key": "comp_act_2",
        },
        {
            "id": STATIC_IDS["activities"]["comp_act_3"],
            "name": "Encryption Standards Validation",
            "assessment": "compliance",
            "group": "comp_remediate",
            "position": 1,
            "mitre_tactic": "TA0005",
            "mitre_technique": "T1027",
            "state": "Pending",
            "visible": True,
            "priority": "High",
            "provider": "OpenSSL",
            "activity_rationale": "Validate encryption implementations meet standards",
            "activity_actions": "Audit TLS configurations and cipher suites",
            "expected_prevention": False,
            "expected_alert_creation": False,
            "expected_severity": "Informational",
            "start_offset": None,
            "end_offset": None,
            "tags": ["comp_required"],
            "assets": [
                {"role": "target", "key": "web_01"},
            ],
            "key": "comp_act_3",
        },
        {
            "id": STATIC_IDS["activities"]["comp_act_4"],
            "name": "Incident Response Plan Review",
            "assessment": "compliance",
            "group": "comp_remediate",
            "position": 2,
            "mitre_tactic": "TA0040",
            "mitre_technique": "T1485",
            "state": "Pending",
            "visible": True,
            "priority": "Medium",
            "provider": "Manual",
            "activity_rationale": "Review and update incident response procedures",
            "activity_actions": "Audit IR plan against SOC 2 requirements",
            "expected_prevention": False,
            "expected_alert_creation": False,
            "expected_severity": "Informational",
            "start_offset": None,
            "end_offset": None,
            "tags": ["comp_optional", "comp_audit"],
            "assets": [
                {"role": "target", "key": "siem"},
            ],
            "key": "comp_act_4",
        },
    ]

    activities = {}
    for activity_data in activities_data:
        # Calculate timestamps
        start_time = None
        end_time = None
        if activity_data["start_offset"] is not None:
            start_time = base_time + timedelta(hours=activity_data["start_offset"])
        if activity_data["end_offset"] is not None:
            end_time = base_time + timedelta(hours=activity_data["end_offset"])

        activity = Activity(
            id=activity_data["id"],
            assessment_id=assessments[activity_data["assessment"]].id,
            activity_group_id=groups[activity_data["group"]].id,
            activity_position=(
                groups[activity_data["group"]].activity_group_position + 1
            )
            * 100_000
            + activity_data["position"],
            name=activity_data["name"],
            mitre_tactic=activity_data["mitre_tactic"],
            mitre_technique=activity_data["mitre_technique"],
            state=activity_data["state"],
            visible=activity_data["visible"],
            priority=activity_data["priority"],
            provider=activity_data["provider"],
            activity_rationale=activity_data["activity_rationale"],
            activity_actions=activity_data["activity_actions"],
            # Optional string fields with empty string defaults
            activity_requirements=activity_data.get("activity_requirements", ""),
            activity_notes=activity_data.get("activity_notes", ""),
            # activity_sources, activity_targets, etc. are now handled via relationships
            # Expected results with proper defaults
            expected_prevention=activity_data.get("expected_prevention", False),
            expected_alert_creation=activity_data.get("expected_alert_creation", False),
            expected_stakeholder_notification=activity_data.get(
                "expected_incident_creation", False
            ),
            expected_severity=activity_data.get("expected_severity", "Low"),
            # Actual results with proper defaults
            logged=activity_data.get("logged", False),
            prevented=activity_data.get("prevented", False),
            # prevention_sources, etc. handled via relationships
            alerted=activity_data.get("alerted", False),
            alert_severity=activity_data.get("alert_severity", "Low"),
            stakeholder_notification_created=activity_data.get(
                "incident_created", False
            ),
            stakeholder_notification_severity=activity_data.get(
                "incident_severity", "Low"
            ),
            # Map evidence_notes to log_notes as simple migration
            log_notes=activity_data.get("evidence_notes", ""),
            alert_notes="",
            prevent_notes="",
            stakeholder_notification_notes="",
            # Timestamps
            activity_start_time=start_time,
            activity_end_time=end_time,
            # Audit fields
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )

        session.add(activity)
        session.flush()  # Flush to get the activity ID

        # Create Activity Evaluation
        eval_data = activity_data.get("evaluation", {})
        evaluation = ActivityEvaluation(
            activity_id=activity.id,
            logged_evaluation=eval_data.get("logged_evaluation", False),
            alerted_evaluation=eval_data.get("alerted_evaluation", False),
            prevented_evaluation=eval_data.get("prevented_evaluation", False),
            stakeholder_notified_evaluation=eval_data.get(
                "stakeholder_notified_evaluation", False
            ),
            activity_coverage_score=eval_data.get("activity_coverage_score", 0),
            event_to_alert_data=eval_data.get("event_to_alert_data", ""),
            event_to_alert_evaluation_result=eval_data.get(
                "event_to_alert_evaluation_result", EvaluationResult.NOT_APPLICABLE
            ),
            alert_to_stakeholder_data=eval_data.get("alert_to_stakeholder_data", ""),
            alert_to_stakeholder_evaluation_result=eval_data.get(
                "alert_to_stakeholder_evaluation_result",
                EvaluationResult.NOT_APPLICABLE,
            ),
            alert_severity_data=eval_data.get("alert_severity_data", ""),
            alert_severity_evaluation_result=eval_data.get(
                "alert_severity_evaluation_result", EvaluationResult.NOT_APPLICABLE
            ),
            stakeholder_notification_severity_data=eval_data.get(
                "stakeholder_notification_severity_data", ""
            ),
            stakeholder_notification_severity_evaluation_result=eval_data.get(
                "stakeholder_notification_severity_evaluation_result",
                EvaluationResult.NOT_APPLICABLE,
            ),
        )
        session.add(evaluation)
        session.flush()

        # Add dynamic evaluation questions for sec_act_1
        if activity_data["key"] == "sec_act_1" and evaluation_templates:
            dq1 = ActivityEvaluationDynamicQuestions(
                activity_evaluation_id=evaluation.id,
                evaluation_template_id=evaluation_templates["template_1"].id,
                data="Data matches logs.",
                evaluation_result=EvaluationResult.PASS,
                position=0,
            )
            session.add(dq1)

            dq2 = ActivityEvaluationDynamicQuestions(
                activity_evaluation_id=evaluation.id,
                evaluation_template_id=evaluation_templates["template_2"].id,
                data="Completed within 1 hour.",
                evaluation_result=EvaluationResult.PASS,
                position=1,
            )
            session.add(dq2)

        # Add tags to activity
        for tag_key in activity_data.get("tags", []):
            if tag_key in tags:
                activity.tags.append(tags[tag_key])

        # Add assets to activity via direct association insert

        # Define default assets per assessment
        defaults = {
            "security": {
                "source": "kali_vm",
                "target": "dc_01",
                "tool": "nmap_tool",
                "prevention_source": "firewall",
                "alert_source": "sec_alert",
                "incident_source": "sec_incident",
            },
            "vulnerability": {
                "source": "nessus_scanner",
                "target": "prod_db",
                "tool": "burp_tool",
                "prevention_source": "vuln_prev",
                "alert_source": "vuln_alert",
                "incident_source": "vuln_incident",
            },
            "compliance": {
                "source": "comp_source",
                "target": "siem",
                "tool": "comp_tool",
                "prevention_source": "comp_prev",
                "alert_source": "comp_alert",
                "incident_source": "comp_incident",
            },
        }

        assessment_key = activity_data["assessment"]
        default_set = defaults.get(assessment_key, {})

        # Collect existing roles for this activity from manual assignment
        existing_roles = set()
        for asset_info in activity_data.get("assets", []):
            existing_roles.add(asset_info["role"])

            asset_key = asset_info["key"]
            role = asset_info["role"]
            if asset_key in assets:
                asset = assets[asset_key]
                session.execute(
                    activity_asset_association.insert().values(
                        activity_id=activity.id,
                        asset_id=asset.id,
                        role=role,
                    )
                )

        # Fill missing roles with defaults
        for role, asset_key in default_set.items():
            if role not in existing_roles:
                if asset_key in assets:
                    asset = assets[asset_key]
                    session.execute(
                        activity_asset_association.insert().values(
                            activity_id=activity.id,
                            asset_id=asset.id,
                            role=role,
                        )
                    )

        activities[activity_data["key"]] = activity
        print(
            f"  ✓ Created activity: {activity_data['name']} ({activity_data['state']})"
        )

    session.commit()
    print(f"✅ Created {len(activities)} activities")
    return activities


def create_acls(
    session: Session,
    users: dict[str, User],
    assessments: dict[str, Assessment],
    admin_id: uuid.UUID,
) -> dict[str, Acl]:
    """Create ACL entries linking users to assessments."""
    print("\n🔐 Creating ACL entries...")

    now = datetime.now(timezone.utc)

    acls_data = [
        # Note: Admins do not require ACLs according to the service validation
        # Manager has red (attacker) access to security and vulnerability
        {
            "id": STATIC_IDS["acls"]["manager_security"],
            "user": "manager",
            "assessment": "security",
            "role": "red",
            "key": "manager_security",
        },
        {
            "id": STATIC_IDS["acls"]["manager_vuln"],
            "user": "manager",
            "assessment": "vulnerability",
            "role": "red",
            "key": "manager_vuln",
        },
        # Regular user has blue (defender) access to security and compliance
        {
            "id": STATIC_IDS["acls"]["regular_security"],
            "user": "regular",
            "assessment": "security",
            "role": "blue",
            "key": "regular_security",
        },
        {
            "id": STATIC_IDS["acls"]["regular_comp"],
            "user": "regular",
            "assessment": "compliance",
            "role": "blue",
            "key": "regular_comp",
        },
        # Observer has spectator access to vulnerability and compliance
        {
            "id": STATIC_IDS["acls"]["observer_vuln"],
            "user": "observer",
            "assessment": "vulnerability",
            "role": "spectator",
            "key": "observer_vuln",
        },
        {
            "id": STATIC_IDS["acls"]["observer_comp"],
            "user": "observer",
            "assessment": "compliance",
            "role": "spectator",
            "key": "observer_comp",
        },
    ]

    acls = {}
    for acl_data in acls_data:
        acl = Acl(
            id=acl_data["id"],
            user_id=users[acl_data["user"]].id,
            assessment_id=assessments[acl_data["assessment"]].id,
            assessment_role=acl_data["role"],
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(acl)
        acls[acl_data["key"]] = acl
        print(
            f"  ✓ Created ACL: {acl_data['user']} -> {acl_data['assessment']} ({acl_data['role']})"
        )

    session.commit()
    print(f"✅ Created {len(acls)} ACL entries")
    return acls


def create_evaluation_templates(
    session: Session, admin_id: uuid.UUID
) -> dict[str, EvaluationTemplate]:
    """
    Create sample evaluation templates.
    """
    print("\n📝 Creating evaluation templates...")
    now = datetime.now(timezone.utc)

    templates_data = [
        {
            "id": STATIC_IDS["evaluation_templates"]["template_1"],
            "name": "Data Accuracy",
            "evaluation_criteria": "Is the provided data accurate?",
            "description": "Check if the data in the activity log matches the expected values.",
            "key": "template_1",
        },
        {
            "id": STATIC_IDS["evaluation_templates"]["template_2"],
            "name": "Timeliness",
            "evaluation_criteria": "Was the action performed within the expected timeframe?",
            "description": "Check timestamps against SLA.",
            "key": "template_2",
        },
    ]

    templates = {}
    for template_data in templates_data:
        template = EvaluationTemplate(
            id=template_data["id"],
            name=template_data["name"],
            evaluation_criteria=template_data["evaluation_criteria"],
            description=template_data["description"],
            created_by=admin_id,
            created_at=now,
            updated_at=now,
        )
        session.add(template)
        templates[template_data["key"]] = template
        print(f"  ✓ Created evaluation template: {template_data['name']}")

    session.commit()
    print(f"✅ Created {len(templates)} evaluation templates.")
    return templates


def print_summary(
    users: dict[str, User],
    assessments: dict[str, Assessment],
    tags: dict[str, Tag],
    assets: dict[str, Asset],
    groups: dict[str, ActivityGroup],
    activities: dict[str, Activity],
    acls: dict[str, Acl],
    evaluation_templates: dict[str, EvaluationTemplate],
) -> None:
    """Print a comprehensive summary of all created data."""
    print("\n" + "=" * 100)
    print("📊 SAMPLE DATA SUMMARY")
    print("=" * 100)

    # Users
    print("\n👥 USERS")
    print("-" * 100)
    print(f"{'Email':<30} {'ID':<38} {'Role':<10} {'Disabled'}")
    print("-" * 100)
    for key in ["admin", "manager", "regular", "observer", "disabled"]:
        user = users[key]
        print(f"{user.email:<30} {str(user.id):<38} {user.role:<10} {user.disabled}")

    # Assessments
    print("\n📋 ASSESSMENTS")
    print("-" * 100)
    print(f"{'Name':<45} {'ID':<38} {'Type'}")
    print("-" * 100)
    for key in ["security", "vulnerability", "compliance"]:
        assessment = assessments[key]
        print(
            f"{assessment.name[:45]:<45} {str(assessment.id):<38} {assessment.assessment_type}"
        )

    # Tags
    print("\n🏷️  TAGS")
    print("-" * 100)
    print(f"{'Name':<20} {'ID':<38} {'Color':<10} {'Assessment'}")
    print("-" * 100)
    for tag in tags.values():
        assessment_name = next(
            (a.name[:20] for a in assessments.values() if a.id == tag.assessment_id),
            "Unknown",
        )
        print(f"{tag.name:<20} {str(tag.id):<38} {tag.color:<10} {assessment_name}")

    # Assets
    print("\n💻 ASSETS")
    print("-" * 100)
    print(f"{'Name':<30} {'ID':<38} {'Icon':<10} {'Assessment'}")
    print("-" * 100)
    for asset in assets.values():
        assessment_name = next(
            (a.name[:25] for a in assessments.values() if a.id == asset.assessment_id),
            "Unknown",
        )
        icon_str = asset.icon if asset.icon else "-"
        print(
            f"{asset.name[:30]:<30} {str(asset.id):<38} {icon_str:<10} {assessment_name}"
        )

    # Activity Groups
    print("\n📁 ACTIVITY GROUPS")
    print("-" * 100)
    print(f"{'Name':<35} {'ID':<38} {'Assessment'}")
    print("-" * 100)
    for group in groups.values():
        assessment_name = next(
            (a.name[:25] for a in assessments.values() if a.id == group.assessment_id),
            "Unknown",
        )
        print(f"{group.name:<35} {str(group.id):<38} {assessment_name}")

    # Activities
    print("\n⚡ ACTIVITIES")
    print("-" * 100)
    print(f"{'Name':<45} {'ID':<38} {'State':<12} {'Tags'}")
    print("-" * 100)
    for activity in activities.values():
        tag_names = ", ".join([tag.name for tag in activity.tags[:3]])
        if len(activity.tags) > 3:
            tag_names += "..."
        print(
            f"{activity.name[:45]:<45} {str(activity.id):<38} {activity.state:<12} {tag_names}"
        )

    # ACLs
    print("\n🔐 ACCESS CONTROL LISTS (ACLs)")
    print("-" * 100)
    print(f"{'User':<30} {'Assessment':<30} {'Role':<10} {'ID'}")
    print("-" * 100)
    for acl in acls.values():
        user_email = next(
            (u.email for u in users.values() if u.id == acl.user_id), "Unknown"
        )
        assessment_name = next(
            (a.name[:28] for a in assessments.values() if a.id == acl.assessment_id),
            "Unknown",
        )
        print(
            f"{user_email:<30} {assessment_name:<30} {acl.assessment_role:<10} {str(acl.id)}"
        )

    # Evaluation Templates
    print("\n📝 EVALUATION TEMPLATES")
    print("-" * 100)
    print(f"{'Name':<25} {'ID':<38} {'Criteria'}")
    print("-" * 100)
    for template in evaluation_templates.values():
        print(
            f"{template.name:<25} {str(template.id):<38} {template.evaluation_criteria[:30]}..."
        )

    # Summary counts
    print("\n" + "=" * 100)
    print("📈 TOTALS")
    print("=" * 100)
    print(f"Users:            {len(users)}")
    print(f"Assessments:      {len(assessments)}")
    print(f"Tags:             {len(tags)}")
    print(f"Assets:           {len(assets)}")
    print(f"Activity Groups:  {len(groups)}")
    print(f"Activities:       {len(activities)}")
    print(f"ACL Entries:      {len(acls)}")
    print(f"Eval Templates:   {len(evaluation_templates)}")
    print("=" * 100)

    # Credentials
    print("\n🔑 TEST CREDENTIALS")
    print("=" * 100)
    print("Admin User:      admin2@raptr.app       / Password.123")
    print("Manager User:    manager@raptr.app      / Password.123")
    print("Regular User:    user@raptr.app         / Password.123")
    print("Observer User:   observer@raptr.app     / Password.123")
    print("Disabled User:   disabled@raptr.app     / Password.123")
    print("=" * 100)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Create sample data for RAPTR backend")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before creating sample data",
    )
    args = parser.parse_args()

    print("🚀 RAPTR Sample Data Generator")
    print("=" * 100)

    with Session(engine) as session:
        # Clear data if requested
        if args.clear:
            clear_data(session, force=True)

        # Create all entities
        users = create_users(session)
        assessments = create_assessments(session, users)
        tags = create_tags(session, assessments, users["admin"].id)
        assets = create_assets(session, assessments, users["admin"].id)
        groups = create_activity_groups(session, assessments, users["admin"].id)
        evaluation_templates = create_evaluation_templates(session, users["admin"].id)
        activities = create_activities(
            session,
            assessments,
            groups,
            tags,
            assets,
            users["admin"].id,
            evaluation_templates,
        )
        acls = create_acls(session, users, assessments, users["admin"].id)

        # Print summary
        print_summary(
            users,
            assessments,
            tags,
            assets,
            groups,
            activities,
            acls,
            evaluation_templates,
        )

        print("\n✅ Sample data creation completed successfully!")


if __name__ == "__main__":
    main()

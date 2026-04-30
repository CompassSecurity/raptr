# User Types and Roles

RAPTR uses a two-level permission system: a **system-level role** that determines what you can do across the platform, and an **assessment role** that controls what you can do within a specific assessment.

??? bug "User Types"
    Currently, there is only one user type. There is no distinction between federated and local users. Any user who wants to log in via an external IdP (e.g. Entra or Okta) must first be created as a user in RAPTR, complete with a local password.

## System Roles

Every user account has exactly one system role.

| Role | Description |
|------|------------|
| **Admin** | Full access to everything. Can manage users, create assessments, seed data, and access all [admin functions](administration.md). |
| **User** | Standard account. Can access assessments they have been granted an [assessment role](user_types.md#assessment-roles) on. Cannot manage other users or system settings. |

## Assessment Roles

Users are assigned one of three roles within each assessment via the **Access Control List (ACL)**. A user can have different roles for different assessments, but they can only have one role for each assessment.

### Red Team

Red Team members act as the **offensive operators**. They are responsible for:

- Creating and configuring activities
- Defining MITRE ATT&CK mappings (tactic and technique)
- Setting expected detection outcomes (logging, prevention, alerting, stakeholder notification)
- Writing activity rationale, requirements and activity details
- Executing activities and updating their state
- Managing activity groups, assets, and tags
- Running evaluations and generating reports

Red Team members have full edit access to all activity fields and can transition activities through any workflow state.

### Blue Team

Blue Team members act as the **defensive responders**. They are responsible for:

- Reviewing executed activities which are [visible](visibility.md)
- Recording actual detection results (was it logged? prevented? alerted?)
- Adding detection timestamps and notes
- Associating and managing detection-related assets (log sources, prevention sources, alert sources)
- Handing activities back to Red Team when more information is needed or if the activity is ready for evaluation

!!! warning "Blue Team Restrictions"
    Blue Team members can **only edit activities** when the activity state is **Waiting Blue** or **Waiting Red**. They are limited to editing detection-related fields — they cannot modify activity names, descriptions, MITRE mappings, expected outcomes, or evaluation results.

### Spectator

Spectators have **read-only access** to the assessment. They can view all [visible](visibility.md) activities and their details but cannot make any changes. This role is suitable for stakeholders, management, or auditors who need visibility without editing capability.

## Permission Summary

### System-Level Permissions

These actions are controlled by the **system role** (Admin or User) and apply across the entire platform.

| Action | Admin | User |
|--------|:-----:|:----:|
| Create assessments | Yes | No |
| Delete assessments | Yes | No |
| Import assessments | Yes | No |
| Manage users | Yes | No |
| Manage assessment ACLs | Yes | No |
| Seed data (MITRE, templates) | Yes | No |
| User self-service | Yes | Yes |
| View system configuration | Yes | No |

### Assessment-Level Permissions

These actions are controlled by the **assessment role** (Red, Blue, or Spectator) and apply within a specific assessment. Admins always have full access regardless of their assessment role.

| Action | Red | Blue | Spectator |
|--------|:---:|:----:|:---------:|
| View visible activities | Yes | Yes | Yes |
| View hidden activities | Yes | No | No |
| Edit assessment details | Yes | No | No |
| Create activities | Yes | No | No |
| Edit activity (general info) | Yes | No | No |
| Edit activity (detection fields) | Yes | Yes* | No |
| Change activity state (any) | Yes | No | No |
| Change activity state (Waiting Blue / Waiting Red) | Yes | Yes* | No |
| Delete/restore activities | Yes | No | No |
| Toggle visibility | Yes | No | No |
| Manage activity groups | Yes | No | No |
| Manage assets | Yes | Yes | No |
| Assign assets to activities (source, target, tool) | Yes | No | No |
| Assign assets to activities (log, prevention, alert, notification sources) | Yes | Yes* | No |
| Manage tags | Yes | Yes | No |
| Upload attachments | Yes | Yes* | No |
| Generate reports | Yes | No | No |
| Import templates/campaigns | Yes | No | No |
| Manage evaluation questions | Yes | No | No |
| Export assessment | Yes | No | No |

_\* Blue Team can only perform these actions when the activity is in the **Waiting Blue** or **Waiting Red** state._

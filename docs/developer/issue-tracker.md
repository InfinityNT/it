# Bug Fix & Feature Sprint - Issue Tracker

This document tracks all issues addressed in the February 2026 sprint.

## Issues Summary

| # | Issue | Type | Status |
|---|-------|------|--------|
| 1 | Edit Device Asset Tag Validation | Bug Fix | Done |
| 2 | Quick Actions Problems | Bug Fix | Done |
| 3 | Manage Models - Category Specs Not Loading | Bug Fix | Done |
| 4 | Employees Page - Manage Job Titles & Departments | Feature | Done |
| 5 | Assign Device - Single/Shared Selector | Feature | Done |
| 6a | Add Device - Auto-generate Asset Tag | Feature | Done |
| 6b | Add Device - Lock Status to Available | Bug Fix | Done |
| 7 | Settings Implementation & Fixes | Feature + Fix | Done |
| 8 | Remove Misleading Email References | Bug Fix | Done |
| 9 | Profile Settings - Password Change Not Opening | Bug Fix | Done |
| 10 | Custom Report Modal Issues | Bug Fix | Done |

---

## Issue Details

### Issue 1: Edit Device Asset Tag Validation Error
**Problem**: Saving an edited device returned 400 with "Asset tag must contain only uppercase letters, numbers, and hyphens".

**Root Cause**: The edit modal had no auto-uppercase enforcement, unlike the add form.

**Fix**: Added `style="text-transform: uppercase"` and an `input` event listener to the asset_tag field in `edit_device_modal.html`.

**Testing**: Edit a device, type lowercase in asset tag -> should auto-uppercase and save without error.

---

### Issue 2: Quick Actions Problems

**2a: Modal-based actions**
Fixed the report builder JavaScript to work when loaded into `#dynamicModal` instead of `#customReportModal`.

**2b: Generate Report**
The modal content template already returns inner content without wrapper. Fixed the JS initialization to detect the correct modal container.

**Testing**: Click each quick action in sidebar -> should open the correct modal or page.

---

### Issue 3: Manage Models - Category Specs Not Loading
**Problem**: Specs showed "No specification fields defined" when editing device models.

**Root Cause**: Naming mismatch between `cat_spec_` prefix (HTMX-loaded) and `spec_` prefix (edit form).

**Fix**: Unified `spec_fields.html` to use `spec_` prefix consistently. Updated `build_spec_fields` and spec collection logic.

**Testing**: Edit a device model -> category specs should load with current values.

---

### Issue 4: Employees Page - Manage Job Titles & Departments
**Feature**: Added dropdown menu to employees page for managing departments and job titles.

**Implementation**:
- Split button dropdown following devices page pattern
- Full CRUD for departments (name, code, description, manager)
- Full CRUD for job titles (title, department, level, description)
- Added `is_department_responsible` field to Employee model
- 10 new URL patterns, 6 new templates

**Testing**: Click dropdown on employees page -> manage departments and job titles through modals.

---

### Issue 5: Assign Device - Single/Shared Selector
**Feature**: Added Individual/Shared toggle to the assign device form.

**Implementation**:
- Radio button toggle at top of assign form
- Shared mode filters employees to department responsibles only
- Override checkbox to show all employees
- Auto-detects shared devices and switches mode

**Testing**: Toggle between Individual/Shared -> employee dropdown should filter accordingly.

---

### Issue 6a: Auto-generate Asset Tag
**Feature**: Asset tags are now auto-generated from category prefix + sequential number.

**Implementation**:
- `DeviceCategory.get_asset_tag_prefix()` - intelligent 3-letter prefix
- `DeviceCategory.generate_next_asset_tag()` - sequential numbering
- API endpoint for fetching next tag
- "Custom asset tag" checkbox toggle

**Testing**: Select a category in add device -> asset tag should auto-populate (e.g., LPT-001).

---

### Issue 6b: Lock Add Device Status
**Fix**: Removed Assigned/Retired options from add device form. Status defaults to "Available".

---

### Issue 7: Settings Implementation & Fixes

**Part 1 - Fixes**:
- Fixed `onclick` handlers for backup/integrity buttons (missing `event` parameter)
- Removed Approval Workflows toggle (always enabled)
- Dynamic last backup timestamp from AuditLog
- Backup frequency setting persistence

**Part 2 - Security Enforcement**:
- Session Timeout Middleware: auto-logout after configured inactivity period
- Password Expiry Middleware: force password change when expired
- Dynamic Password Validator: reads policy from SystemSettings (standard/strong)

**Testing**: Change session timeout in settings -> verify auto-logout. Change password policy -> verify enforcement.

---

### Issue 8: Remove Misleading Email References
**Fix**: Changed "Used for notifications and password reset" to "Your contact email address".

---

### Issue 9: Password Change Not Opening
**Problem**: Password change button loaded full modal wrapper into dynamic modal, causing nesting.

**Fix**: Created `password_change_content.html` without outer wrapper. View detects HTMX and returns the correct template.

**Testing**: Click "Change Password" in profile settings -> modal should open correctly.

---

### Issue 10: Custom Report Modal Issues
**Fixes**:
- Checkmark repositioned with `transform: translateY(-50%)` and button padding-right
- `showError` now calls `showToastNotification` (correct name)
- Alert fallback has explicit background color
- Single-source selection skips suggest-primary API

**Testing**: Open report builder -> select data sources -> should work without errors.

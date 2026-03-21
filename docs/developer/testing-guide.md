# Dynamic Custom Report Builder - Testing Guide

## Overview
The dynamic custom report builder has been fully implemented and backend tested. This guide helps you test the complete system in your browser.

## Prerequisites
- Django development server running: `python manage.py runserver`
- Authenticated user account with `can_generate_reports` permission
- Sample data in the database (devices, employees, assignments, etc.)

## Test Scenarios

### 1. Basic Report Generation (Device Only)

**Steps:**
1. Navigate to `/reports/`
2. Click the "Create Report" button
3. In the modal:
   - ✅ Check "Devices" data source
   - ✅ Field selection accordion should appear automatically
   - ✅ Expand "Devices Fields" accordion
   - ✅ Select fields: Asset Tag, Serial Number, Model, Status
   - ✅ Device filters section should be visible
   - ✅ Optionally select device status filters (e.g., "Assigned")
   - ✅ Choose output format: CSV
4. Click "Preview Report"
5. Verify preview shows correct data with selected columns
6. Click "Generate Report"
7. Verify CSV downloads with correct headers and data

**Expected Results:**
- Field checkboxes populate dynamically
- Preview displays first 10 records
- CSV contains only selected columns
- Data is correctly formatted

### 2. Multi-Source Report (Device + Employee)

**Steps:**
1. Open "Create Report" modal
2. Check both "Devices" and "Employees" data sources
3. Verify both field accordions appear
4. Select fields from both sources:
   - Device: Asset Tag, Status
   - Employee: Full Name, Department, Email
5. Verify both device and employee filter sections are visible
6. Select filters from both sections
7. Generate CSV report

**Expected Results:**
- Combined fields from both sources appear
- Filters from both sections are applied
- Query optimizes with proper joins
- No duplicate records

### 3. Assignment Report

**Steps:**
1. Select "Assignments" data source only
2. Select assignment-related fields
3. Add assignment status filters
4. Generate PDF report

**Expected Results:**
- Assignment fields populate
- PDF generates with dynamic columns
- Limited to 100 rows (if more data exists)
- Proper page orientation based on column count

### 4. Validation Testing

**Test Invalid Combinations:**
1. Try selecting incompatible data sources (should show warning/error)
2. Try generating with no fields selected (should show error)
3. Select 50+ fields (should show performance warning)

**Expected Results:**
- Validation messages display in red/yellow alerts
- Generate button disabled when configuration invalid
- Clear error messages explain the issue

### 5. Filter Testing

**Verify Checkbox Filters:**
1. Device filters:
   - ✅ Device status (checkboxes)
   - ✅ Device category (dynamically populated checkboxes)
   - ✅ Usage type (checkboxes)
   - ✅ Location (dynamically populated checkboxes)
2. Employee filters:
   - ✅ Department (dynamically populated checkboxes)
   - ✅ Employment status (checkboxes)
3. Assignment filters:
   - ✅ Assignment status (checkboxes)
4. Approval filters:
   - ✅ Approval status (checkboxes)
   - ✅ Request type (checkboxes)

**Expected Results:**
- All filters use checkboxes (NO dropdowns)
- Dynamic filters populate from database
- Multiple selections allowed
- Filters show/hide based on data sources

### 6. All Output Formats

**Test Each Format:**
1. CSV - All data, proper quoting
2. JSON - Valid JSON array structure
3. PDF - Formatted table, max 100 rows
4. Excel - Proper formatting, auto-sized columns (requires openpyxl)

**Expected Results:**
- All formats download correctly
- Filenames include timestamp
- Data is properly formatted per format
- No encoding issues

### 7. Preview Functionality

**Steps:**
1. Configure report with various fields
2. Click "Preview Report" button
3. Verify preview area shows:
   - Record count
   - Preview count (first 10)
   - Table with selected columns
   - Correct data

**Expected Results:**
- Preview loads without page refresh (AJAX)
- Shows subset of data
- Allows verification before full generation
- Can modify configuration after preview

### 8. UI/UX Testing

**Verify User Experience:**
1. Modal is scrollable (modal-xl, modal-dialog-scrollable)
2. Sections are collapsible for better organization
3. Field accordions expand/collapse smoothly
4. Checkboxes are easy to select/deselect
5. "Select All" / "Deselect All" buttons work
6. Validation messages are clear and helpful
7. Generate button enables/disables appropriately

### 9. Edge Cases

**Test Edge Scenarios:**
1. No data matches filters → Should show empty report or message
2. Very large dataset (1000+ records) → Should complete without timeout
3. Fields with null values → Should display as empty strings
4. Special characters in data → Should handle properly in CSV/JSON
5. Long text fields → Should truncate in PDF
6. Related objects that don't exist → Should handle gracefully

### 10. Performance Testing

**Monitor Performance:**
1. Report with 50+ fields
2. Report with 5000+ records
3. Multiple concurrent report generations
4. Preview multiple times rapidly

**Expected Results:**
- Queries use select_related/prefetch_related efficiently
- No N+1 query problems
- Reasonable generation time (< 10 seconds for most reports)
- Browser doesn't freeze during generation

## Browser Console Checks

**Monitor JavaScript Console:**
- No JavaScript errors on modal open
- Field schema loads successfully
- Filter data populates correctly
- AJAX requests complete successfully
- No 404 errors for API endpoints

**Check Network Tab:**
- `/reports/api/field-schema/` returns 200 with JSON
- `/reports/api/categories/` returns category data
- `/reports/api/departments/` returns department data
- `/reports/api/locations/` returns location data
- `/reports/api/validate-config/` validates correctly
- `/reports/generate-dynamic/` completes successfully

## Backend Testing Already Completed ✅

The following have been verified via Python unit tests:

- ✅ All modules import successfully
- ✅ Field schema loads with 6 data sources
- ✅ Validation logic works correctly
- ✅ Device-only query: 32 records extracted correctly
- ✅ Device+Employee query: 15 records with proper joins
- ✅ CSV formatter generates valid CSV
- ✅ JSON formatter generates valid JSON
- ✅ Preview generation returns correct data
- ✅ Query optimization (select_related) verified

## Known Limitations

1. **PDF Format**: Limited to 100 rows to prevent huge files
2. **Excel Format**: Requires `openpyxl` package installed
3. **Performance**: Reports with 100+ fields may be slow
4. **Browser Testing**: Frontend JavaScript needs manual browser testing

## Troubleshooting

### Modal doesn't open
- Check browser console for errors
- Verify JavaScript file is loaded
- Check for Bootstrap modal conflicts

### Fields don't populate
- Check `/reports/api/field-schema/` returns data
- Verify user is authenticated
- Check browser console for AJAX errors

### Filters don't show
- Verify data source checkboxes are checked
- Check `updateFieldsAndFilters()` function is called
- Inspect filter accordion visibility

### Report generation fails
- Check Django logs for backend errors
- Verify selected fields are valid
- Check filter values are correct format
- Ensure user has `can_generate_reports` permission

### CSV has encoding issues
- Check for special characters in data
- Verify CSV writer handles Unicode correctly
- Test with different output formats

## Success Criteria

- ✅ All data sources selectable
- ✅ Fields populate dynamically from schema
- ✅ All filters use checkboxes
- ✅ Validation shows warnings/errors
- ✅ Preview works without page reload
- ✅ All 4 output formats generate correctly
- ✅ No JavaScript errors in console
- ✅ Modal is scrollable and organized
- ✅ Performance is acceptable
- ✅ Data integrity maintained (correct joins)

## Next Steps After Testing

1. Fix any issues discovered during browser testing
2. Adjust UI/UX based on user feedback
3. Optimize queries if performance issues found
4. Add additional features (saved configurations, scheduled reports)
5. Create user documentation/help text

---

**Server Status**: Development server should be running at `http://localhost:8000`

**Test Data**: Ensure you have sample devices, employees, and assignments in the database for meaningful testing.

**Permissions**: Verify your test user has the `core.can_generate_reports` permission.

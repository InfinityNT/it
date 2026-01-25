# Template System

This project uses a component-based SPA (Single Page Application) architecture with HTMX for dynamic content loading.

## Template Structure

```
templates/
├── base.html                    # THE single SPA base template
├── login.html                   # Authentication page
├── pages/                       # Main content pages
│   ├── dashboard.html
│   ├── devices.html
│   └── users.html
└── components/
    ├── navigation/
    │   ├── navbar.html
    │   └── sidebar.html
    ├── forms/                   # Modal forms
    │   ├── add_device_modal.html
    │   ├── edit_device_modal.html
    │   └── return_device_modal.html
    └── auth/
        └── login_form.html
```

## Design Principles

### Single Base Template

`base.html` conditionally renders authenticated/unauthenticated layouts:

```html
{% if user.is_authenticated %}
    <!-- Authenticated layout with navbar, sidebar, content -->
{% else %}
    <!-- Login page layout -->
{% endif %}
```

### Component-Based

Reusable components using Django's `{% include %}` tag:

```html
{% include 'components/navigation/navbar.html' %}
{% include 'components/forms/add_device_modal.html' %}
```

### Modal Forms

All form interactions happen via modal overlays (no full-page forms):

- Better UX with overlay forms
- Content stays visible behind modal
- HTMX handles form submission

### HTMX Integration

Dynamic content loading without full page refreshes:

```html
<a href="/devices/"
   hx-get="/devices/content/"
   hx-target="#content-area"
   hx-push-url="true">
    Devices
</a>
```

Key HTMX attributes:
- `hx-get` - Load content via GET request
- `hx-target` - Where to place the response
- `hx-push-url` - Update browser URL
- `hx-trigger` - When to trigger the request

### Clean Naming

File names clearly describe their purpose:
- `add_device_modal.html` - Modal for adding devices
- `navbar.html` - Navigation bar component
- `dashboard.html` - Dashboard page

## Reusable Components

### Empty State Component

`templates/components/common/empty_state.html` - Displays a friendly message when no data is available.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `icon` | string | Yes | Bootstrap icon name (e.g., `laptop`, `people`, `search`) |
| `title` | string | Yes | Main heading text |
| `message` | string | No | Secondary descriptive text |
| `has_filters` | boolean | No | If true, shows "clear filters" link instead of action button |
| `clear_filters_action` | string | No | JavaScript for clearing filters (default: `clearFilters(); return false;`) |
| `action_text` | string | No | Text for the action button (only shown when `has_filters` is false) |
| `action_url` | string | No | URL for the action button |
| `action_hx_get` | string | No | HTMX endpoint for modal-based actions |
| `action_hx_target` | string | No | HTMX target selector (default: `#dynamicModalContent`) |
| `action_icon` | string | No | Bootstrap icon for action button (default: `plus`) |

**Usage Examples:**

Empty database state (with add action):
```html
{ % include 'components/common/empty_state.html' with
    icon='laptop'
    title='No devices registered yet'
    message='Get started by adding your first device'
    action_text='Add Device'
    action_hx_get='/devices/create/'
    action_icon='plus' % }
```

Filtered state (no results):
```html
{ % include 'components/common/empty_state.html' with
    icon='search'
    title='No devices match your filters'
    message='Try adjusting your search criteria'
    has_filters=True % }
```

### Error State Component

`templates/components/common/error_state.html` - Displays error messages with retry functionality.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | No | Error heading (default: "Something went wrong") |
| `message` | string | No | Error description |
| `retry_url` | string | No | URL for retry button |
| `show_dashboard_link` | boolean | No | Show "Go to Dashboard" button |

## Template Modernization (Completed)

The template system has been modernized from a legacy multi-base-template system:

### Completed Tasks

- [x] Create component directory structure
- [x] Consolidate base templates into single base.html
- [x] Extract navigation components (navbar, sidebar)
- [x] Convert form pages to modal components
- [x] Create main page templates (dashboard, devices, users, etc.)
- [x] Update view references and HTMX integration
- [x] Clean up obsolete template files
- [x] 41 obsolete templates moved to `/templates/obsolete/`

### Achieved Benefits

- Clean component-based architecture with logical organization
- Single base canvas eliminating template conflicts
- Modal forms providing better UX
- Consistent HTMX integration throughout
- Maintainable and testable codebase
- Login overlay system with smooth animations

## Next Steps

- [Project Structure](project-structure.md) - Codebase organization
- [Responsive Design](../features/responsive-design.md) - Mobile UI
- [Development Setup](../getting-started/development-setup.md) - Commands

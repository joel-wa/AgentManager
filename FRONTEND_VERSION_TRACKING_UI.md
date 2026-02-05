# Frontend Version Tracking UI Integration

## Overview

This document describes the UI integration of file version tracking in the AgentManager frontend.

## User Experience Flow

### 1. Chat Interface - Inline File Changes

After each AI response that modifies files, users will see a "File Changes" section displayed directly under the response, similar to the existing "Tools Used" feature.

**Location**: Chat interface, under each AI assistant message

**Display**:
```
┌─────────────────────────────────────────────────────────┐
│ AI Assistant Message                                     │
│ [Response content here...]                              │
│                                                          │
│ ┌─ Tools Used (3) ─────────────────────────────┐       │
│ │ [Collapsible tool execution details]          │       │
│ └───────────────────────────────────────────────┘       │
│                                                          │
│ ┌─ File Changes (2) ───────────────────────────┐  ← NEW │
│ │ > test.py                          [modified] │       │
│ │   /path/to/test.py                           │       │
│ │   [View Version History]                     │       │
│ │                                                │       │
│ │ > config.json                      [modified] │       │
│ │   /path/to/config.json                       │       │
│ │   [View Version History]                     │       │
│ └───────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Expandable file list showing all modified files
- Each file shows action badge (modified/created/deleted)
- "View Version History" button per file
- Matches dark theme aesthetic
- Uses same styling as "Tools Used" section

### 2. Version History Modal (Inline)

When user clicks "View Version History" from chat:

**Display**:
```
┌─────────────────────────────────────────────────────────┐
│ File Changes (2)                                        │
│ ┌─ Version History ─────────────────────────────┐  [X] │
│ │                                                 │      │
│ │ test.py                                         │      │
│ │ /path/to/test.py                               │      │
│ │ Current version: v3                             │      │
│ │                                                 │      │
│ │ ┌─ Version 3 ─────────────────────┐  [Current] │      │
│ │ │ ⏰ Feb 5, 19:30 | 150 bytes      │            │      │
│ │ │ Hash: 9d1dd95f97...              │            │      │
│ │ └─────────────────────────────────┘            │      │
│ │                                                 │      │
│ │ ┌─ Version 2 ─────────────────────┐            │      │
│ │ │ ⏰ Feb 5, 19:28 | 142 bytes      │            │      │
│ │ │ Hash: 241a6ab311...              │            │      │
│ │ │ [Restore This Version]           │            │      │
│ │ └─────────────────────────────────┘            │      │
│ │                                                 │      │
│ │ ┌─ Version 1 ─────────────────────┐            │      │
│ │ │ ⏰ Feb 5, 19:25 | 128 bytes      │            │      │
│ │ │ Hash: 33969f54cd...              │            │      │
│ │ │ Message: "Before restoring..."   │            │      │
│ │ │ [Restore This Version]           │            │      │
│ │ └─────────────────────────────────┘            │      │
│ └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Inline display (replaces file list temporarily)
- Shows all versions with metadata
- Current version clearly marked
- Restore button for older versions
- Confirmation dialog before restore
- Close button to return to file list

### 3. Timeline Tab - File Changes View

The Timeline tab shows all file changes grouped by AI response:

**Display**:
```
┌────────────────────────────────────────────────────────┐
│ ⏰ File Changes                                        │
├────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─ AI Response: Implement login... ────────┐         │
│ │● 19:30                    2 files • 2 modified      │
│ │                                                     │
│ │  ✏️  modified: login.py            [Versions]      │
│ │  ✏️  modified: auth.py             [Versions]      │
│ └─────────────────────────────────────────────────────┘
│                                                         │
│ ┌─ AI Response: Add configuration... ───────┐         │
│ │● 19:25                    1 file • 1 modified       │
│ │                                                     │
│ │  ✏️  modified: config.json         [Versions]      │
│ └─────────────────────────────────────────────────────┘
│                                                         │
│ ┌─ AI Response: Create README ──────────────┐         │
│ │● 19:20                    1 file • 1 created        │
│ │                                                     │
│ │  ➕ created: README.md             [Versions]      │
│ └─────────────────────────────────────────────────────┘
│                                                         │
└────────────────────────────────────────────────────────┘
```

**Features**:
- Timeline entries grouped by AI response
- Expandable sections showing file details
- Action icons (✏️ modified, ➕ created, ❌ deleted)
- "Versions" button per file opens version history
- Same version history modal as chat interface

### 4. Version Restore Flow

When user clicks "Restore This Version":

**Step 1 - Confirmation**:
```
┌─────────────────────────────────────────────────────────┐
│ Are you sure you want to restore to version 2?          │
│ Your current version will be saved before restoring.    │
│                                                          │
│ [✓ Confirm]  [✗ Cancel]                                │
└─────────────────────────────────────────────────────────┘
```

**Step 2 - Success Feedback**:
- Version history refreshes automatically
- New version created (current content saved)
- File browser refreshes if viewing that file
- Timeline updates with new entry

## Technical Integration Points

### Data Flow

1. **AI Response → File Changes Detection**
   ```
   AI writes file → tool_calls include WriteFileTool
   → Extract file paths → Add to message.fileChanges
   → Display in FileChangesList component
   ```

2. **Version History Request**
   ```
   User clicks "View Version History"
   → api.listFileVersions(projectId, filePath)
   → Display in FileVersionHistory component
   → Show expandable version cards
   ```

3. **Version Restore**
   ```
   User confirms restore
   → api.restoreFileVersion(projectId, filePath, version)
   → Backend saves current as new version
   → Backend writes old version content
   → Frontend reloads: file list, timeline, viewing file
   ```

### Component Hierarchy

```
App.tsx
├── ChatInterface
│   └── MessageBubble
│       └── FileChangesList ← NEW
│           └── FileVersionHistory ← NEW
└── Timeline ← ENHANCED
    └── FileVersionHistory ← NEW (shared component)
```

### API Endpoints Used

```
GET  /api/projects/:id/versions/:path
     → Returns VersionHistory (all versions with metadata)

GET  /api/projects/:id/version/:version/:path
     → Returns VersionEntry (specific version content)

POST /api/projects/:id/restore/:version/:path
     → Restores file to specified version
```

## Design Principles

1. **Consistency**: Matches existing "Tools Used" design pattern
2. **Non-intrusive**: Collapses by default, user can expand
3. **Informative**: Shows key metadata without overwhelming
4. **Actionable**: Clear restore workflow with confirmation
5. **Integrated**: Works seamlessly with chat and timeline

## Color Scheme (Dark Theme)

- Background: `rgba(255,255,255,0.04)` - Dark surface
- Border: `rgba(255,255,255,0.06)` - Subtle border
- Text (primary): `rgba(255,255,255,0.90)` - White
- Text (secondary): `rgba(255,255,255,0.40)` - Gray
- Accent (modified): `#ff9b4d` - Orange
- Accent (created): `#4ade80` - Green
- Accent (action): `#3b82f6` - Blue
- Hover: `rgba(255,255,255,0.08)` - Light hover

## Edge Cases Handled

1. **No versions yet**: Shows message "No version history available"
2. **Error loading versions**: Shows retry button with error message
3. **Restore in progress**: Disables buttons, shows loading state
4. **Current version**: Cannot restore current version (button hidden)
5. **Multiple file changes**: All shown in expandable list
6. **Long file paths**: Truncated with tooltip showing full path

## Benefits to User

1. **Immediate visibility**: See what changed right after AI response
2. **Quick access**: View/restore versions without leaving chat
3. **Safety net**: All changes automatically versioned
4. **Confidence**: Easy to undo unwanted AI changes
5. **Transparency**: Clear history of what AI modified and when

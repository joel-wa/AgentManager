# UI Testing Guide

This guide helps you test all the new UI improvements that have been implemented.

## Prerequisites

1. Start all services:
```bash
# Terminal 1: Rust Core
cd rust-core && cargo run

# Terminal 2: Python Main Agent
cd python-services/main_agent && python main.py

# Terminal 3: Frontend
cd frontend && npm run dev
```

2. Open http://localhost:3000 in your browser

---

## Feature Testing Checklist

### ✅ 1. Advanced Chat Formatting

**Test Steps:**
1. Create a new project or select an existing one
2. Send a message asking for formatted content:
   ```
   Can you create a table comparing Python, JavaScript, and Rust?
   ```
3. Or ask for code:
   ```
   Show me a Python function that reads a file
   ```

**Expected Results:**
- Tables should render with borders and proper formatting
- Code blocks should have syntax highlighting
- Headers, lists, and other markdown elements display correctly
- Dark theme styling applied throughout

**Screenshot Areas:**
- AI message with table
- AI message with code block
- AI message with mixed markdown elements

---

### ✅ 2. Enhanced Tool Activity Styling

**Test Steps:**
1. Send a message that triggers tools:
   ```
   List all files in this project and read the README
   ```
2. Click "Tool Activity (N)" below the AI response

**Expected Results:**
- Tool activity card has backdrop blur effect
- Each tool call is in its own row with hover effect
- Icons are colored (blue for search, green for read, etc.)
- File paths display clearly
- Timestamps are formatted nicely

**Screenshot Areas:**
- Expanded tool activity view
- Hover state on tool activity item

---

### ✅ 3. Document Preview in Right Panel

**Test Steps:**
1. Click on "Files" in the side panel
2. Click on any .md file (like README.md)
3. Try typing in the chat while file is open

**Expected Results:**
- File opens in right panel (not modal)
- Can still interact with chat
- File preview stays open
- Can see both chat and file simultaneously
- For .md files, rendered view shows by default

**Screenshot Areas:**
- Three-panel layout (chat + files + preview)
- Markdown file preview

---

### ✅ 4. Markdown File Preview Toggle

**Test Steps:**
1. Open a .md file in the preview panel
2. Look for Eye/Code toggle buttons in toolbar
3. Click to switch between preview and edit modes

**Expected Results:**
- Eye icon shows rendered markdown
- Code icon shows raw markdown
- Toggle works smoothly
- Rendered view has proper styling
- Edit view shows plain text

**Screenshot Areas:**
- File preview in render mode
- Same file in edit mode

---

### ✅ 5. @document Mention Feature

**Test Steps:**
1. Click in the chat input field
2. Type `@`
3. Start typing a filename (e.g., `@REA`)
4. Select file from dropdown or press Enter
5. Type your message
6. Send

**Expected Results:**
- Dropdown appears when typing @
- List filters as you type
- Selected file appears as chip above input
- Can click X to remove mentioned file
- Files show with blue background
- File context sent with message

**Screenshot Areas:**
- @ dropdown showing file list
- Mentioned file chip
- Message with multiple mentions

---

### ✅ 6. Browser-Like Tab System

**Test Steps:**
1. Create or select a project (tab auto-creates)
2. Click the `+` button to create new tab
3. Hover over a tab to see close button
4. Click to switch between tabs
5. Try closing a tab with X button
6. Switch projects from dropdown

**Expected Results:**
- Tabs show at top of window
- Each tab displays: title + project name
- Active tab highlighted
- Hover shows X button
- + button always visible
- Each tab has independent chat
- Minimum 1 tab always present
- Switching projects creates new tab

**Screenshot Areas:**
- Multiple tabs open
- Hover state with X button
- + button location

---

### ✅ 7. Maintenance Agent Model Configuration

**Test Steps:**
1. Click Settings icon (⚙️) in top bar
2. Scroll to "AI Model Configuration" section
3. Look for two model fields:
   - Main Agent Model
   - Maintenance Model

**Expected Results:**
- Settings modal opens
- Two separate model input fields
- Main Agent Model has description: "Used for chat interactions"
- Maintenance Model has description: "Used for workspace maintenance"
- Can set different models
- Changes save when clicking "Save Settings"

**Screenshot Areas:**
- Settings modal showing both model fields

---

## Layout Testing

### Test Different Screen Sizes

1. **Full Width (1920px+)**
   - All three panels visible
   - Chat takes ~45%
   - Side panel ~30%
   - File preview ~25%

2. **Medium Width (1366px)**
   - Same layout, narrower panels
   - Should still be usable

3. **Panel Toggle**
   - Click panel toggle button
   - Side panel should collapse
   - Chat area expands

---

## Interaction Testing

### Smooth Workflows

**Workflow 1: Multi-tab Research**
1. Open project A in tab 1
2. Start conversation about feature X
3. Create new tab (+)
4. Ask about feature Y
5. Switch back to tab 1
6. Previous conversation intact

**Workflow 2: File-Assisted Chat**
1. Open a markdown file in preview
2. Use @ to mention the file
3. Ask questions about it
4. Reference multiple files
5. All while viewing file preview

**Workflow 3: Code Review**
1. Open code file in preview
2. Toggle to rendered mode (if .md)
3. Ask AI to review
4. View AI's response with code blocks
5. Make edits based on feedback

---

## Visual Consistency

Check that all UI elements follow the theme:

- [ ] Dark background (#1a1a1a)
- [ ] Surface elements slightly lighter (#2d2d2d)
- [ ] Borders subtle (#404040)
- [ ] Accent blue for primary actions
- [ ] Accent green for AI/success
- [ ] Smooth transitions (200-300ms)
- [ ] Consistent padding (12px, 16px)
- [ ] Rounded corners (8px, 12px)

---

## Accessibility Testing

- [ ] Can navigate with keyboard (Tab, Enter, Esc)
- [ ] Buttons have hover states
- [ ] Focus indicators visible
- [ ] Text contrast sufficient
- [ ] Icons have titles/tooltips
- [ ] Error messages clear

---

## Performance Testing

1. **Many Messages**
   - Send 50+ messages
   - Scrolling should be smooth
   - New messages appear instantly

2. **Many Tabs**
   - Open 10+ tabs
   - Switching should be instant
   - No memory leaks

3. **Large Files**
   - Open large markdown files
   - Rendering should be fast
   - No lag when switching modes

---

## Edge Cases

1. **Empty States**
   - [ ] No projects created yet
   - [ ] No files in project
   - [ ] Empty @ mention search

2. **Error States**
   - [ ] Service offline
   - [ ] File load failure
   - [ ] Settings save failure

3. **Long Content**
   - [ ] Very long file names
   - [ ] Very long messages
   - [ ] Very long code blocks

---

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on macOS)

---

## Screenshots to Capture

For documentation purposes, capture:

1. Overview with all features visible
2. Rich markdown message example
3. Tool activity expanded view
4. Three-panel layout
5. File preview in markdown render mode
6. @ mention dropdown
7. Multiple tabs open
8. Settings modal with models
9. Hover states (tabs, buttons)
10. Mobile/responsive view (if applicable)

---

## Bug Report Template

If you find issues, report with:

```
**Feature:** [Which feature is affected]
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**

**Actual Behavior:**

**Screenshot:** [If applicable]

**Browser:** [Chrome/Firefox/Safari]
**Version:** [Browser version]
```

---

## Success Criteria

All features pass testing when:

✅ UI is responsive and smooth
✅ All interactions work as expected
✅ No console errors
✅ Layout doesn't break at different sizes
✅ Features integrate well together
✅ Professional, polished appearance
✅ Intuitive user experience

---

## Next Steps After Testing

1. Document any bugs found
2. Capture screenshots of key features
3. Create demo video if needed
4. Update user documentation
5. Prepare for deployment

Happy testing! 🚀

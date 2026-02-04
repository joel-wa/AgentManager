# Maintenance Configuration

## Project Context
This is a test project for video concept templates.

## Maintenance Rules

### README Updates
**DO NOT** automatically suggest README updates unless:
- A new major feature is added
- The project structure changes significantly
- The user explicitly asks for documentation updates

### File Organization
- Keep markdown files in the root directory
- Archive old files to `.archive/` folder
- Do not suggest moving files unless there's a clear organizational benefit

### Suggestions to Avoid
- Routine README updates for minor changes
- Reorganization without clear purpose
- Merging files that serve different purposes

## Important Files
- `Recents.md` - Decision timeline (auto-updated)
- `video-concept-templates.md` - Core project content

## Custom Health Checks
- [ ] Core templates remain in root directory
- [ ] Archived content is properly stored
- [ ] File changes are tracked in Recents.md

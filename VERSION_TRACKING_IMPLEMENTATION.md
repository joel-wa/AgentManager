# File Version Tracking Implementation

## Overview

This document describes the implementation of file version tracking in AgentManager. The feature provides Git-like version control for all files modified by agents, allowing users to review and restore previous versions.

## Features

### Automatic Version Capture
- Every file write operation automatically saves the previous content before overwriting
- Only creates a version when content actually changes (avoids duplicates)
- Versions are transparently captured without user intervention

### Version Storage
- Versions stored in `.meta/versions/` within each project directory
- Path sanitization using base64 encoding prevents collision issues
- Original file extensions are preserved in version files
- JSON metadata file (`history.json`) tracks all versions

### Content Integrity
- SHA256 hashing for each version ensures data integrity
- Hash mismatches can detect corruption
- Metadata includes timestamp, file size, and content hash

### Restore Capability
- Users can restore any file to any previous version
- Restoration creates a backup of current content before reverting
- Prevents accidental data loss during restoration

## Architecture

### Data Models

#### VersionMetadata
```rust
pub struct VersionMetadata {
    pub version: u32,              // Sequential version number
    pub timestamp: DateTime<Utc>,  // When version was created
    pub file_size: u64,            // Size in bytes
    pub content_hash: String,      // SHA256 hash
    pub message: Option<String>,   // Optional description
}
```

#### VersionEntry
```rust
pub struct VersionEntry {
    pub metadata: VersionMetadata,
    pub content: String,           // Actual file content
}
```

#### VersionHistory
```rust
pub struct VersionHistory {
    pub file_path: String,         // Original file path
    pub current_version: u32,      // Latest version number
    pub versions: Vec<VersionMetadata>,
}
```

### Core Methods

#### `write_file(project_id, path, content)`
- Entry point for all file writes
- Automatically captures previous version if file exists and content differs
- Delegates to internal method with version capture flag

#### `save_version(project_id, file_path, content, message)`
- Creates a new version entry
- Stores version content with preserved extension
- Updates history.json with metadata
- Returns VersionMetadata on success

#### `list_versions(project_id, file_path)`
- Returns complete version history for a file
- Includes metadata for all versions
- Returns empty history if file has no versions

#### `get_version(project_id, file_path, version)`
- Retrieves specific version content and metadata
- Validates version exists
- Returns VersionEntry with both content and metadata

#### `restore_version(project_id, file_path, version)`
- Saves current content before restoration
- Restores specified version without triggering duplicate capture
- Updates file on disk with restored content

## API Endpoints

### List Versions
```
GET /api/projects/:id/versions/:path
```

**Response:**
```json
{
  "file_path": "example.txt",
  "current_version": 3,
  "versions": [
    {
      "version": 1,
      "timestamp": "2026-02-05T19:05:02Z",
      "file_size": 31,
      "content_hash": "9d1dd95f97...",
      "message": null
    }
  ]
}
```

### Get Specific Version
```
GET /api/projects/:id/version/:version/:path
```

**Response:**
```json
{
  "metadata": {
    "version": 2,
    "timestamp": "2026-02-05T19:05:02Z",
    "file_size": 65,
    "content_hash": "241a6ab311..."
  },
  "content": "File content here..."
}
```

### Restore Version
```
POST /api/projects/:id/restore/:version/:path
```

**Response:** HTTP 200 OK on success

## Storage Structure

```
project_root/
├── .meta/
│   └── versions/
│       └── {base64_encoded_path}/
│           ├── history.json      # Version metadata
│           ├── v0001.txt         # Version 1 content
│           ├── v0002.txt         # Version 2 content
│           └── v0003.txt         # Version 3 content
└── {files}...
```

### Path Encoding
- File paths are base64-encoded (URL-safe, no padding) to prevent collisions
- Example: `test.txt` → `dGVzdC50eHQ`
- Prevents issues with special characters in paths
- Ensures unique directory for each tracked file

### Version Files
- Format: `v{version:04}.{extension}`
- Examples: `v0001.txt`, `v0042.py`, `v0100.json`
- Extension preserved from original file
- Unknown extensions default to `.dat`

## Security Considerations

### Path Safety
- Base64 encoding prevents path traversal attacks
- All paths constructed using `PathBuf::join()` (safe)
- No direct string concatenation for filesystem paths

### Content Integrity
- SHA256 hashing detects tampering or corruption
- Metadata stored separately from content
- Immutable once written (versions never modified)

### Access Control
- Versions isolated per project
- Same access controls as regular project files
- No cross-project version access

### Storage Limits
- No automatic cleanup (user responsibility)
- Consider implementing retention policies for production
- Disk space monitoring recommended

## Testing

### Test Coverage
- Automatic version creation on file modification
- Version history retrieval
- Specific version content retrieval
- File restoration to previous versions
- Duplicate version prevention
- Path collision prevention (base64)
- Extension preservation

### Test Script
Run `test_version_tracking.py` to validate:
```bash
python test_version_tracking.py
```

Expected results:
- ✓ All versions created automatically
- ✓ Correct version count (no duplicates on restore)
- ✓ Content matches expected for each version
- ✓ Restoration works correctly
- ✓ Base64 directory names present

## Performance Considerations

### Version Creation
- O(1) for writing version file
- O(n) for updating history.json where n = number of versions
- SHA256 computation is fast for typical file sizes

### Version Retrieval
- O(n) for listing versions (reads history.json)
- O(1) for getting specific version (direct file read)
- No database overhead, simple filesystem operations

### Storage Overhead
- Each version stores full content (not delta-based)
- Appropriate for typical agent use cases
- Consider delta compression for large files in future

## Future Enhancements

### Potential Improvements
1. **Delta Compression**: Store only differences between versions
2. **Retention Policies**: Auto-delete old versions after N days
3. **Version Comparison**: Show diffs between versions
4. **Version Tags**: Named versions (e.g., "working", "stable")
5. **Compression**: Gzip version files to save space
6. **Atomic Operations**: Transaction-like version operations
7. **Version Search**: Search across all versions
8. **Batch Operations**: Restore multiple files to same point in time

### Scalability
For high-volume scenarios, consider:
- Database backend for metadata (faster queries)
- Object storage for version content
- Asynchronous version creation
- Background cleanup tasks

## Migration Notes

### Existing Projects
- No migration needed
- Version tracking starts automatically on first file modification
- Existing files have no initial version until first change

### Backward Compatibility
- All existing API endpoints unchanged
- Version endpoints are additive
- No breaking changes to file operations

## Troubleshooting

### No Versions Showing
- Check if file has been modified since feature was added
- Verify `.meta/versions/` directory exists
- Check file permissions on version storage

### Version Restoration Fails
- Verify version number exists in history
- Check file permissions
- Ensure sufficient disk space

### Hash Mismatches
- Indicates file corruption or tampering
- Verify filesystem integrity
- Check disk errors

## Dependencies

### Rust Crates
- `sha2 = "0.10"` - SHA256 hashing
- `base64 = "0.22"` - Path encoding
- `chrono` - Timestamp handling
- `serde_json` - Metadata serialization

### System Requirements
- Sufficient disk space for version storage
- File system with proper permission support
- No special requirements

## Conclusion

The file version tracking feature provides robust, automatic versioning for all agent-modified files. The implementation is secure, efficient, and transparent to users while offering powerful restore capabilities when needed.

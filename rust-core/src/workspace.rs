use std::path::PathBuf;
use std::fs;
use sha2::{Sha256, Digest};
use chrono::Utc;

use crate::models::{Project, FileItem, FileType, VersionMetadata, VersionEntry, VersionHistory};

/// Manages the workspace directory and projects
pub struct WorkspaceManager {
    workspace_root: PathBuf,
}

impl WorkspaceManager {
    pub fn new() -> anyhow::Result<Self> {
        // Use .agent-workspace in user's home directory
        let home_dir = std::env::var("USERPROFILE")
            .or_else(|_| std::env::var("HOME"))
            .unwrap_or_else(|_| ".".to_string());
        
        let workspace_root = PathBuf::from(home_dir).join(".agent-workspace");
        
        Ok(Self { workspace_root })
    }

    /// Get project directory path (either custom location or default)
    fn get_project_dir(&self, project: &Project) -> PathBuf {
        if let Some(location) = &project.location {
            PathBuf::from(location)
        } else {
            self.workspace_root
                .join("projects")
                .join(&project.id)
        }
    }

    /// Ensure workspace directory structure exists
    pub fn ensure_workspace_exists(&self) -> anyhow::Result<()> {
        let projects_dir = self.workspace_root.join("projects");
        let config_dir = self.workspace_root.join("config");
        
        fs::create_dir_all(&projects_dir)?;
        fs::create_dir_all(&config_dir)?;
        
        // Create default config if not exists
        let config_file = config_dir.join("settings.json");
        if !config_file.exists() {
            let default_config = serde_json::json!({
                "version": "0.1.0",
                "theme": "dark",
                "ollamaUrl": "http://localhost:11434",
                "defaultModel": "gemma:7b"
            });
            fs::write(&config_file, serde_json::to_string_pretty(&default_config)?)?;
        }
        
        tracing::info!("Workspace initialized at: {:?}", self.workspace_root);
        Ok(())
    }

    /// List all projects
    pub fn list_projects(&self) -> anyhow::Result<Vec<Project>> {
        let projects_dir = self.workspace_root.join("projects");
        let mut projects = Vec::new();
        
        if let Ok(entries) = fs::read_dir(&projects_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    let meta_file = path.join(".meta").join("project.json");
                    if let Ok(content) = fs::read_to_string(&meta_file) {
                        if let Ok(project) = serde_json::from_str::<Project>(&content) {
                            projects.push(project);
                        }
                    }
                }
            }
        }
        
        Ok(projects)
    }

    /// Create a new project
    pub fn create_project(&self, project: &Project) -> anyhow::Result<()> {
        // Get project directory (either custom or default)
        let project_dir = self.get_project_dir(project);
        
        fs::create_dir_all(&project_dir)?;
        fs::create_dir_all(project_dir.join(".meta"))?;
        fs::create_dir_all(project_dir.join("files"))?;
        fs::create_dir_all(project_dir.join("notes"))?;
        
        // Save project metadata with location information
        let meta_file = project_dir.join(".meta").join("project.json");
        fs::write(&meta_file, serde_json::to_string_pretty(project)?)?;
        
        // Create initial README
        let readme_content = format!(
            "# {}\n\n{}\n\nCreated: {}\n",
            project.name,
            project.description.clone().unwrap_or_default(),
            project.created_at.format("%Y-%m-%d %H:%M:%S")
        );
        fs::write(project_dir.join("README.md"), readme_content)?;
        
        // Create soul.md - Agent personality/system prompt for this project
        let soul_content = format!(
            r#"# Agent Soul for {}

You are an AI assistant helping with "{}".

## Personality
- Be helpful, concise, and accurate
- Focus on the user's goals
- Ask clarifying questions when needed

## Project Context
{}

## Guidelines
- Always work within this project's directory
- Respect the file organization
- Log important decisions to Recents.md

## Remember
- You have access to file tools (read, write, search, list)
- You can execute commands when needed
- Ask before making destructive changes
"#,
            project.name,
            project.name,
            project.description.clone().unwrap_or_else(|| "No description provided.".to_string())
        );
        fs::write(project_dir.join("soul.md"), soul_content)?;
        
        // Create Recents.md - Decision timeline
        let recents_content = format!(
            r#"# Recent Activity for {}

This file tracks decisions, discussions, and important changes.

## {} - Project Created
**Context**: Initial project setup
**Status**: Active
"#,
            project.name,
            project.created_at.format("%Y-%m-%d")
        );
        fs::write(project_dir.join("Recents.md"), recents_content)?;
        
        // Create maintenance.md template
        let maintenance_content = format!(
            r#"# Maintenance Configuration for {}

## Project Context
{}

## Important Files
- `README.md` - Project overview
- `soul.md` - Agent personality configuration
- `Recents.md` - Decision timeline

## Merge Rules
- Add project-specific merge rules here

## Outdated Patterns to Watch
- Add patterns to flag as outdated

## Custom Health Checks
- [ ] README is up to date
- [ ] soul.md reflects current project goals
"#,
            project.name,
            project.description.clone().unwrap_or_else(|| "No description provided.".to_string())
        );
        fs::write(project_dir.join(".meta").join("maintenance.md"), maintenance_content)?;
        
        tracing::info!("Created project: {} ({})", project.name, project.id);
        Ok(())
    }

    /// Get project by ID
    pub fn get_project(&self, id: &str) -> anyhow::Result<Option<Project>> {
        let meta_file = self.workspace_root
            .join("projects")
            .join(id)
            .join(".meta")
            .join("project.json");
        
        if meta_file.exists() {
            let content = fs::read_to_string(&meta_file)?;
            let project = serde_json::from_str(&content)?;
            Ok(Some(project))
        } else {
            Ok(None)
        }
    }

    /// List files in project
    pub fn list_files(&self, project_id: &str) -> anyhow::Result<Vec<FileItem>> {
        // Load project to get its location
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        
        let project_dir = self.get_project_dir(&project);
        
        self.scan_directory(&project_dir, &project_dir, 0)
    }

    fn scan_directory(&self, path: &PathBuf, base_dir: &PathBuf, depth: usize) -> anyhow::Result<Vec<FileItem>> {
        let mut items = Vec::new();
        
        if depth > 3 || !path.is_dir() {
            return Ok(items);
        }
        
        if let Ok(entries) = fs::read_dir(path) {
            for entry in entries.flatten() {
                let entry_path = entry.path();
                let name = entry.file_name().to_string_lossy().to_string();
                
                // Skip hidden files EXCEPT .meta directory
                if name.starts_with('.') && name != ".meta" {
                    continue;
                }
                
                // Generate relative path from base directory
                let relative_path = entry_path
                    .strip_prefix(base_dir)
                    .ok()
                    .map(|p| p.to_string_lossy().replace('\\', "/"));
                
                if entry_path.is_dir() {
                    let children = self.scan_directory(&entry_path, base_dir, depth + 1)?;
                    items.push(FileItem {
                        name: name.clone(),
                        file_type: FileType::Folder,
                        extension: None,
                        children: Some(children),
                        summary: None,
                        path: relative_path,
                    });
                } else {
                    let extension = entry_path
                        .extension()
                        .map(|e| e.to_string_lossy().to_string());
                    items.push(FileItem {
                        name: name.clone(),
                        file_type: FileType::File,
                        extension,
                        children: None,
                        summary: None,
                        path: relative_path,
                    });
                }
            }
        }
        
        // Sort: folders first, then alphabetically
        items.sort_by(|a, b| {
            match (&a.file_type, &b.file_type) {
                (FileType::Folder, FileType::File) => std::cmp::Ordering::Less,
                (FileType::File, FileType::Folder) => std::cmp::Ordering::Greater,
                _ => a.name.to_lowercase().cmp(&b.name.to_lowercase()),
            }
        });
        
        Ok(items)
    }

    /// Read file content
    pub fn read_file(&self, project_id: &str, path: &str) -> anyhow::Result<String> {
        // Load project to get its location
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        
        let file_path = self.get_project_dir(&project).join(path);
        
        Ok(fs::read_to_string(file_path)?)
    }

    /// Write file content
    pub fn write_file(&self, project_id: &str, path: &str, content: &str) -> anyhow::Result<()> {
        // Load project to get its location
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        
        let file_path = self.get_project_dir(&project).join(path);
        
        // Save version before writing (if file exists)
        if file_path.exists() {
            if let Ok(old_content) = fs::read_to_string(&file_path) {
                // Only save version if content is different
                if old_content != content {
                    let _ = self.save_version(project_id, path, &old_content, None);
                }
            }
        }
        
        // Create parent directories if needed
        if let Some(parent) = file_path.parent() {
            fs::create_dir_all(parent)?;
        }
        
        fs::write(&file_path, content)?;
        tracing::info!("Wrote file: {:?}", file_path);
        Ok(())
    }

    /// Calculate SHA256 hash of content
    fn calculate_hash(content: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(content.as_bytes());
        format!("{:x}", hasher.finalize())
    }

    /// Get version storage directory for a file
    fn get_version_dir(&self, project_id: &str, file_path: &str) -> PathBuf {
        // Sanitize file path to create a safe directory name
        let sanitized = file_path.replace(['/', '\\', ':', '*', '?', '"', '<', '>', '|'], "_");
        
        self.workspace_root
            .join("projects")
            .join(project_id)
            .join(".meta")
            .join("versions")
            .join(sanitized)
    }

    /// Save a version of a file
    pub fn save_version(
        &self,
        project_id: &str,
        file_path: &str,
        content: &str,
        message: Option<String>,
    ) -> anyhow::Result<VersionMetadata> {
        let version_dir = self.get_version_dir(project_id, file_path);
        fs::create_dir_all(&version_dir)?;

        // Load or create version history
        let history_file = version_dir.join("history.json");
        let mut history = if history_file.exists() {
            let content = fs::read_to_string(&history_file)?;
            serde_json::from_str::<VersionHistory>(&content)?
        } else {
            VersionHistory {
                file_path: file_path.to_string(),
                current_version: 0,
                versions: Vec::new(),
            }
        };

        // Create new version
        let new_version = history.current_version + 1;
        let metadata = VersionMetadata {
            version: new_version,
            timestamp: Utc::now(),
            file_size: content.len() as u64,
            content_hash: Self::calculate_hash(content),
            message,
        };

        // Save version content
        let version_file = version_dir.join(format!("v{:04}.txt", new_version));
        fs::write(&version_file, content)?;

        // Update history
        history.current_version = new_version;
        history.versions.push(metadata.clone());
        fs::write(&history_file, serde_json::to_string_pretty(&history)?)?;

        tracing::info!(
            "Saved version {} for file: {} (project: {})",
            new_version,
            file_path,
            project_id
        );

        Ok(metadata)
    }

    /// List all versions of a file
    pub fn list_versions(&self, project_id: &str, file_path: &str) -> anyhow::Result<VersionHistory> {
        let version_dir = self.get_version_dir(project_id, file_path);
        let history_file = version_dir.join("history.json");

        if !history_file.exists() {
            return Ok(VersionHistory {
                file_path: file_path.to_string(),
                current_version: 0,
                versions: Vec::new(),
            });
        }

        let content = fs::read_to_string(&history_file)?;
        Ok(serde_json::from_str(&content)?)
    }

    /// Get a specific version of a file
    pub fn get_version(&self, project_id: &str, file_path: &str, version: u32) -> anyhow::Result<VersionEntry> {
        let version_dir = self.get_version_dir(project_id, file_path);
        let version_file = version_dir.join(format!("v{:04}.txt", version));

        if !version_file.exists() {
            return Err(anyhow::anyhow!("Version {} not found", version));
        }

        let content = fs::read_to_string(&version_file)?;

        // Get metadata from history
        let history = self.list_versions(project_id, file_path)?;
        let metadata = history
            .versions
            .iter()
            .find(|v| v.version == version)
            .ok_or_else(|| anyhow::anyhow!("Version metadata not found"))?
            .clone();

        Ok(VersionEntry { metadata, content })
    }

    /// Restore a specific version of a file
    pub fn restore_version(&self, project_id: &str, file_path: &str, version: u32) -> anyhow::Result<()> {
        // Get the version content
        let version_entry = self.get_version(project_id, file_path, version)?;

        // Save current version before restoring
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        let current_file_path = self.get_project_dir(&project).join(file_path);

        if current_file_path.exists() {
            let current_content = fs::read_to_string(&current_file_path)?;
            let message = format!("Before restoring to version {}", version);
            let _ = self.save_version(project_id, file_path, &current_content, Some(message));
        }

        // Restore the version
        self.write_file(project_id, file_path, &version_entry.content)?;

        tracing::info!(
            "Restored file {} to version {} (project: {})",
            file_path,
            version,
            project_id
        );

        Ok(())
    }
}

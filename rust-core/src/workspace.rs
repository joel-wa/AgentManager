use std::path::PathBuf;
use std::fs;
use chrono::Utc;
use git2::{Repository, Signature, IndexAddOption, Oid, DiffOptions};

use crate::models::{Project, FileItem, FileType, VersionMetadata, VersionEntry, VersionHistory, TimelineEntry, FileAction};

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
        
        // Initialize Git repository for version tracking
        self.init_git_repo(&project_dir)?;
        
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
        self.write_file_internal(project_id, path, content, true)
    }

    /// Write file content with optional version capture
    fn write_file_internal(&self, project_id: &str, path: &str, content: &str, capture_version: bool) -> anyhow::Result<()> {
        // Load project to get its location
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        
        let file_path = self.get_project_dir(&project).join(path);
        
        // Create parent directories if needed
        if let Some(parent) = file_path.parent() {
            fs::create_dir_all(parent)?;
        }
        
        fs::write(&file_path, content)?;
        tracing::info!("Wrote file: {:?}", file_path);
        
        // Auto-commit to Git if capture_version is enabled
        if capture_version {
            let commit_message = format!("Update {}", path);
            if let Err(e) = self.git_commit(project_id, &[path], &commit_message) {
                tracing::warn!("Failed to auto-commit {}: {}", path, e);
            }
        }
        
        Ok(())
    }

    /// Initialize a Git repository for a project
    fn init_git_repo(&self, project_dir: &PathBuf) -> anyhow::Result<()> {
        // Check if already initialized
        if project_dir.join(".git").exists() {
            tracing::info!("Git repository already exists in {:?}", project_dir);
            return Ok(());
        }

        // Initialize repository
        let repo = Repository::init(project_dir)?;
        tracing::info!("Initialized Git repository in {:?}", project_dir);

        // Create initial .gitignore
        let gitignore_content = "# AgentManager\n.DS_Store\n*.swp\n*.tmp\n";
        fs::write(project_dir.join(".gitignore"), gitignore_content)?;

        // Make initial commit
        let mut index = repo.index()?;
        index.add_all(["*"].iter(), IndexAddOption::DEFAULT, None)?;
        index.write()?;

        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;

        let signature = Signature::now("AgentManager", "agent@agentmanager.local")?;
        
        repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            "Initial commit",
            &tree,
            &[],
        )?;

        tracing::info!("Created initial commit in Git repository");
        Ok(())
    }

    /// Get or open Git repository for a project
    fn get_git_repo(&self, project_id: &str) -> anyhow::Result<Repository> {
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        
        let project_dir = self.get_project_dir(&project);
        
        // Initialize if not exists
        if !project_dir.join(".git").exists() {
            self.init_git_repo(&project_dir)?;
        }
        
        Repository::open(&project_dir)
            .map_err(|e| anyhow::anyhow!("Failed to open Git repository: {}", e))
    }

    /// Commit changes to Git
    fn git_commit(&self, project_id: &str, paths: &[&str], message: &str) -> anyhow::Result<Oid> {
        let repo = self.get_git_repo(project_id)?;
        let mut index = repo.index()?;

        // Add specified paths to index
        for path in paths {
            index.add_path(std::path::Path::new(path))?;
        }
        index.write()?;

        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;

        let signature = Signature::now("AgentManager", "agent@agentmanager.local")?;
        
        let parent_commit = match repo.head() {
            Ok(head) => {
                let oid = head.target().ok_or_else(|| anyhow::anyhow!("No HEAD target"))?;
                Some(repo.find_commit(oid)?)
            }
            Err(_) => None,
        };

        let parent_refs: Vec<&git2::Commit> = if let Some(ref commit) = parent_commit {
            vec![commit]
        } else {
            vec![]
        };

        let commit_oid = repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parent_refs,
        )?;

        tracing::info!("Created Git commit: {} - {}", commit_oid, message);
        Ok(commit_oid)
    }

    /// List all versions (Git commits) of a file
    pub fn list_versions(&self, project_id: &str, file_path: &str) -> anyhow::Result<VersionHistory> {
        let repo = self.get_git_repo(project_id)?;
        let mut revwalk = repo.revwalk()?;
        revwalk.push_head()?;

        let mut versions = Vec::new();
        let mut version_num = 0;

        for oid in revwalk {
            let oid = oid?;
            let commit = repo.find_commit(oid)?;
            
            // Check if this commit actually modified the file (not just contains it)
            let tree = commit.tree()?;
            let file_exists = tree.get_path(std::path::Path::new(file_path)).is_ok();
            
            if !file_exists {
                continue; // File doesn't exist in this commit
            }
            
            // Check if file was modified in this commit by comparing with parent
            let file_changed = if commit.parent_count() == 0 {
                // First commit - file was created here
                true
            } else {
                // Compare with parent commit
                let parent = commit.parent(0)?;
                let parent_tree = parent.tree()?;
                
                // Get file blob in current commit
                let entry = tree.get_path(std::path::Path::new(file_path))?;
                let current_oid = entry.id();
                
                // Check if file existed in parent and if content changed
                match parent_tree.get_path(std::path::Path::new(file_path)) {
                    Ok(parent_entry) => {
                        // File existed in parent - check if content changed
                        current_oid != parent_entry.id()
                    }
                    Err(_) => {
                        // File didn't exist in parent - it was created in this commit
                        true
                    }
                }
            };
            
            if file_changed {
                version_num += 1;
                
                let timestamp = chrono::DateTime::from_timestamp(commit.time().seconds(), 0)
                    .unwrap_or_else(|| Utc::now());

                // Get file content at this commit to calculate size
                let entry = tree.get_path(std::path::Path::new(file_path))?;
                let object = entry.to_object(&repo)?;
                let blob = object.as_blob().ok_or_else(|| anyhow::anyhow!("Not a blob"))?;
                let file_size = blob.content().len() as u64;

                versions.push(VersionMetadata {
                    version: version_num,
                    timestamp,
                    file_size,
                    content_hash: oid.to_string(),
                    message: commit.message().map(|s| s.to_string()),
                });
            }
        }

        // Reverse to get oldest first
        versions.reverse();
        // Re-number from 1
        for (i, v) in versions.iter_mut().enumerate() {
            v.version = (i + 1) as u32;
        }

        Ok(VersionHistory {
            file_path: file_path.to_string(),
            current_version: versions.len() as u32,
            versions,
        })
    }

    /// Get a specific version of a file from Git
    pub fn get_version(&self, project_id: &str, file_path: &str, version: u32) -> anyhow::Result<VersionEntry> {
        let history = self.list_versions(project_id, file_path)?;
        
        let metadata = history
            .versions
            .get((version - 1) as usize)
            .ok_or_else(|| anyhow::anyhow!("Version {} not found", version))?
            .clone();

        let repo = self.get_git_repo(project_id)?;
        let oid = Oid::from_str(&metadata.content_hash)?;
        let commit = repo.find_commit(oid)?;
        let tree = commit.tree()?;
        let entry = tree.get_path(std::path::Path::new(file_path))?;
        let object = entry.to_object(&repo)?;
        let blob = object.as_blob().ok_or_else(|| anyhow::anyhow!("Not a blob"))?;
        let content = String::from_utf8_lossy(blob.content()).to_string();

        Ok(VersionEntry { metadata, content })
    }

    /// Restore a specific version of a file from Git
    pub fn restore_version(&self, project_id: &str, file_path: &str, version: u32) -> anyhow::Result<()> {
        // Get the version content from Git
        let version_entry = self.get_version(project_id, file_path, version)?;

        // Write the content (this will auto-commit)
        self.write_file_internal(project_id, file_path, &version_entry.content, false)?;
        
        // Make a commit noting the restoration
        let message = format!("Restore {} to version {}", file_path, version);
        self.git_commit(project_id, &[file_path], &message)?;

        tracing::info!(
            "Restored file {} to version {} (project: {})",
            file_path,
            version,
            project_id
        );

        Ok(())
    }

    /// Delete a file (with Git tracking)
    pub fn delete_file(&self, project_id: &str, file_path: &str) -> anyhow::Result<()> {
        let project = self.get_project(project_id)?
            .ok_or_else(|| anyhow::anyhow!("Project not found"))?;
        
        let full_path = self.get_project_dir(&project).join(file_path);
        
        if !full_path.exists() {
            return Err(anyhow::anyhow!("File does not exist: {}", file_path));
        }
        
        if full_path.is_dir() {
            return Err(anyhow::anyhow!("Path is a directory, not a file: {}", file_path));
        }
        
        // Delete the file
        fs::remove_file(&full_path)?;
        
        // Commit the deletion to Git
        let message = format!("Delete {}", file_path);
        if let Err(e) = self.git_commit(project_id, &[file_path], &message) {
            tracing::warn!("Failed to commit deletion of {}: {}", file_path, e);
        }
        
        tracing::info!(
            "Deleted file {} (project: {}), committed to Git",
            file_path,
            project_id
        );
        
        Ok(())
    }

    /// Get git commit history as timeline entries
    pub fn get_commit_timeline(&self, project_id: &str, limit: usize) -> anyhow::Result<Vec<TimelineEntry>> {
        let repo = self.get_git_repo(project_id)?;
        let mut revwalk = repo.revwalk()?;
        revwalk.push_head()?;

        let mut entries = Vec::new();
        let mut count = 0;

        for oid in revwalk {
            if count >= limit {
                break;
            }

            let oid = oid?;
            let commit = repo.find_commit(oid)?;
            
            // Get commit metadata
            let timestamp = match chrono::DateTime::from_timestamp(commit.time().seconds(), 0) {
                Some(ts) => ts,
                None => {
                    tracing::warn!("Invalid timestamp for commit {}, skipping", oid);
                    continue;
                }
            };
            let message = commit.message().unwrap_or("(no commit message)").to_string();
            
            // Get list of files changed in this commit
            let mut files = Vec::new();
            
            // Get the tree for this commit
            let tree = commit.tree()?;
            
            // Compare with parent to find changed files
            if commit.parent_count() > 0 {
                let parent = commit.parent(0)?;
                let parent_tree = parent.tree()?;
                
                let mut diff_opts = DiffOptions::new();
                let diff = repo.diff_tree_to_tree(Some(&parent_tree), Some(&tree), Some(&mut diff_opts))?;
                
                diff.foreach(
                    &mut |delta, _progress| {
                        let file_path = match delta.new_file().path().and_then(|p| p.to_str()) {
                            Some(path) => path,
                            None => {
                                tracing::warn!("Invalid UTF-8 file path in commit {}", oid);
                                return true; // Skip this file
                            }
                        };
                        
                        let action = match delta.status() {
                            git2::Delta::Added => "created",
                            git2::Delta::Deleted => "deleted",
                            git2::Delta::Modified => "modified",
                            git2::Delta::Renamed => "renamed",
                            _ => "modified",
                        };
                        
                        files.push(FileAction {
                            action: action.to_string(),
                            path: file_path.to_string(),
                        });
                        
                        true
                    },
                    None,
                    None,
                    None,
                )?;
            } else {
                // First commit - all files are "created"
                let mut tree_entries = Vec::new();
                tree.walk(git2::TreeWalkMode::PreOrder, |dir, entry| {
                    if let Some(name) = entry.name() {
                        if entry.kind() == Some(git2::ObjectType::Blob) {
                            let path = if dir.is_empty() {
                                name.to_string()
                            } else {
                                format!("{}{}", dir, name)
                            };
                            tree_entries.push(path);
                        }
                    }
                    git2::TreeWalkResult::Ok
                })?;
                
                for path in tree_entries {
                    files.push(FileAction {
                        action: "created".to_string(),
                        path,
                    });
                }
            }
            
            // Only add entries that actually changed files (skip merge commits with no changes)
            if !files.is_empty() {
                entries.push(TimelineEntry {
                    id: oid.to_string(),
                    timestamp,
                    title: message.lines().next().unwrap_or("(no commit message)").to_string(),
                    files,
                });
                count += 1;
            }
        }

        Ok(entries)
    }
}

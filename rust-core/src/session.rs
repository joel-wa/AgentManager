use chrono::{DateTime, Utc};
use std::collections::VecDeque;
use uuid::Uuid;

use crate::models::{TimelineEntry, FileAction};

/// Logs session activity and maintains breadcrumb trail
pub struct SessionLogger {
    entries: VecDeque<TimelineEntry>,
    max_entries: usize,
}

impl SessionLogger {
    pub fn new() -> Self {
        Self {
            entries: VecDeque::new(),
            max_entries: 100,
        }
    }

    /// Log a new session activity
    pub fn log(&mut self, title: &str, files: Vec<FileAction>) {
        let entry = TimelineEntry {
            id: Uuid::new_v4().to_string(),
            timestamp: Utc::now(),
            title: title.to_string(),
            files,
        };

        self.entries.push_front(entry);

        // Maintain max size
        while self.entries.len() > self.max_entries {
            self.entries.pop_back();
        }
    }

    /// Log a chat message interaction
    pub fn log_message(&self, _project_id: &str, _user_message: &str, _response: &str) {
        // TODO: Implement proper logging to timeline
        tracing::debug!("Chat message logged for project");
    }

    /// Get recent entries
    pub fn get_recent(&self, count: usize) -> Vec<&TimelineEntry> {
        self.entries.iter().take(count).collect()
    }

    /// Get entries within time range
    pub fn get_in_range(&self, start: DateTime<Utc>, end: DateTime<Utc>) -> Vec<&TimelineEntry> {
        self.entries
            .iter()
            .filter(|e| e.timestamp >= start && e.timestamp <= end)
            .collect()
    }

    /// Clear all entries
    pub fn clear(&mut self) {
        self.entries.clear();
    }

    /// Export entries to markdown
    pub fn export_markdown(&self) -> String {
        let mut md = String::from("# Session Timeline\n\n");
        
        for entry in &self.entries {
            md.push_str(&format!(
                "## {}\n_{}_\n\n",
                entry.title,
                entry.timestamp.format("%Y-%m-%d %H:%M:%S")
            ));
            
            for file in &entry.files {
                md.push_str(&format!("- **{}**: `{}`\n", file.action, file.path));
            }
            
            md.push_str("\n");
        }
        
        md
    }
}

use std::path::PathBuf;
use notify::{Watcher, RecursiveMode, Event, RecommendedWatcher, Config};
use std::sync::mpsc::channel;
use tokio::sync::broadcast;

/// File system operations and monitoring
#[allow(dead_code)]
pub struct FileOps {
    watch_sender: Option<broadcast::Sender<FileEvent>>,
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct FileEvent {
    pub event_type: FileEventType,
    pub path: PathBuf,
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub enum FileEventType {
    Created,
    Modified,
    Deleted,
    Renamed,
}

#[allow(dead_code)]
impl FileOps {
    pub fn new() -> Self {
        Self {
            watch_sender: None,
        }
    }

    /// Start watching a directory for changes
    pub fn start_watching(&mut self, path: PathBuf) -> anyhow::Result<broadcast::Receiver<FileEvent>> {
        let (tx, rx) = broadcast::channel(100);
        self.watch_sender = Some(tx.clone());

        let (watcher_tx, watcher_rx) = channel();
        
        let mut watcher = RecommendedWatcher::new(
            move |res: Result<Event, notify::Error>| {
                if let Ok(event) = res {
                    let _ = watcher_tx.send(event);
                }
            },
            Config::default(),
        )?;

        watcher.watch(&path, RecursiveMode::Recursive)?;

        // Spawn task to forward events
        tokio::spawn(async move {
            let _watcher = watcher; // Keep watcher alive
            
            while let Ok(event) = watcher_rx.recv() {
                for path in event.paths {
                    let event_type = match event.kind {
                        notify::EventKind::Create(_) => FileEventType::Created,
                        notify::EventKind::Modify(_) => FileEventType::Modified,
                        notify::EventKind::Remove(_) => FileEventType::Deleted,
                        _ => continue,
                    };
                    
                    let file_event = FileEvent { event_type, path };
                    let _ = tx.send(file_event);
                }
            }
        });

        Ok(rx)
    }

    /// Read file with metadata
    pub async fn read_with_meta(path: &PathBuf) -> anyhow::Result<FileContent> {
        let content = tokio::fs::read_to_string(path).await?;
        let metadata = tokio::fs::metadata(path).await?;
        
        Ok(FileContent {
            content,
            size: metadata.len(),
            modified: metadata.modified().ok(),
        })
    }

    /// Write file with backup
    pub async fn write_with_backup(path: &PathBuf, content: &str) -> anyhow::Result<()> {
        // Create backup if file exists
        if path.exists() {
            let backup_path = path.with_extension("bak");
            tokio::fs::copy(path, &backup_path).await?;
        }
        
        tokio::fs::write(path, content).await?;
        Ok(())
    }
}

#[allow(dead_code)]
#[derive(Debug)]
pub struct FileContent {
    pub content: String,
    pub size: u64,
    pub modified: Option<std::time::SystemTime>,
}

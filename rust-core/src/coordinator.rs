use crate::http_client::HttpClient;
use crate::models::{AgentChatRequest, AgentChatResponse, ToolCall, ToolActivity, ToolType};
use chrono::Utc;

/// Coordinates tool execution between Rust core and Python services
pub struct ToolCoordinator {
    http_client: HttpClient,
}

impl ToolCoordinator {
    pub fn new() -> Self {
        Self {
            http_client: HttpClient::new(),
        }
    }

    /// Send chat message to main agent service
    pub async fn send_to_agent(&self, message: &str, context: Option<&str>) -> anyhow::Result<AgentChatResponse> {
        let request = AgentChatRequest {
            message: message.to_string(),
            context: context.map(|s| s.to_string()),
            tools: vec![
                "search".to_string(),
                "read_file".to_string(),
                "write_file".to_string(),
            ],
            project_id: None,
            workspace_root: None,
            chat_history: None,
        };

        self.http_client
            .post("http://localhost:8001/agent/chat", &request)
            .await
    }

    /// Execute tool calls and return results
    pub async fn execute_tools(&self, tool_calls: &[ToolCall]) -> Vec<ToolActivity> {
        let mut activities = Vec::new();

        for call in tool_calls {
            let activity = match call.name.as_str() {
                "search" => {
                    let query = call.arguments.get("query")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown");
                    
                    ToolActivity {
                        activity_type: ToolType::Search,
                        description: format!("Searched workspace for '{}'", query),
                        file_path: None,
                        timestamp: Utc::now(),
                    }
                }
                "read_file" => {
                    let path = call.arguments.get("path")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown");
                    
                    ToolActivity {
                        activity_type: ToolType::Read,
                        description: format!("Read file: {}", path),
                        file_path: Some(path.to_string()),
                        timestamp: Utc::now(),
                    }
                }
                "write_file" => {
                    let path = call.arguments.get("path")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown");
                    
                    ToolActivity {
                        activity_type: ToolType::Write,
                        description: format!("Created/Updated: {}", path),
                        file_path: Some(path.to_string()),
                        timestamp: Utc::now(),
                    }
                }
                _ => continue,
            };
            
            activities.push(activity);
        }

        activities
    }

    /// Request workspace analysis from maintenance agent
    pub async fn request_analysis(&self, project_id: &str) -> anyhow::Result<()> {
        let request = serde_json::json!({
            "project_id": project_id,
        });
        
        let _: serde_json::Value = self.http_client
            .post("http://localhost:8002/maintenance/analyze", &request)
            .await?;
        
        Ok(())
    }

    /// Generate embedding for text
    pub async fn generate_embedding(&self, text: &str) -> anyhow::Result<Vec<f32>> {
        let request = serde_json::json!({
            "text": text,
        });
        
        let response: EmbeddingResponse = self.http_client
            .post("http://localhost:8003/embed", &request)
            .await?;
        
        Ok(response.embedding)
    }
}

#[derive(serde::Deserialize)]
struct EmbeddingResponse {
    embedding: Vec<f32>,
}

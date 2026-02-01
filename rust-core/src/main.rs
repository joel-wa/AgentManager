mod api;
mod websocket;
mod workspace;
mod file_ops;
mod coordinator;
mod session;
mod http_client;
mod models;

use axum::{
    routing::{get, post, put},
    Router,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::cors::{CorsLayer, Any};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::workspace::WorkspaceManager;
use crate::coordinator::ToolCoordinator;
use crate::session::SessionLogger;
use crate::models::Settings;

/// Application state shared across handlers
pub struct AppState {
    pub workspace: WorkspaceManager,
    pub coordinator: ToolCoordinator,
    pub session: SessionLogger,
    pub settings: Settings,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Starting Agent Workspace Core...");

    // Initialize workspace manager
    let workspace = WorkspaceManager::new()?;
    workspace.ensure_workspace_exists()?;

    // Initialize components
    let coordinator = ToolCoordinator::new();
    let session = SessionLogger::new();
    let settings = Settings::default();

    let state = Arc::new(RwLock::new(AppState {
        workspace,
        coordinator,
        session,
        settings,
    }));

    // Build router
    let app = Router::new()
        // REST API routes
        .route("/api/health", get(api::health_check))
        .route("/api/chat", post(api::chat))
        .route("/api/settings", get(api::get_settings))
        .route("/api/settings", put(api::update_settings))
        .route("/api/projects", get(api::list_projects))
        .route("/api/projects", post(api::create_project))
        .route("/api/projects/:id", get(api::get_project))
        .route("/api/projects/:id/files", get(api::list_files))
        .route("/api/projects/:id/files/*path", get(api::get_file))
        .route("/api/projects/:id/files/*path", post(api::write_file))
        .route("/api/projects/:id/timeline", get(api::get_timeline))
        .route("/api/projects/:id/suggestions", get(api::get_suggestions))
        .route("/api/projects/:id/suggestions/:suggestion_id/accept", post(api::accept_suggestion))
        .route("/api/projects/:id/suggestions/:suggestion_id/dismiss", post(api::dismiss_suggestion))
        // WebSocket for real-time chat
        .route("/ws", get(websocket::websocket_handler))
        // CORS layer
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        )
        .with_state(state);

    let addr = SocketAddr::from(([127, 0, 0, 1], 8000));
    tracing::info!("Listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

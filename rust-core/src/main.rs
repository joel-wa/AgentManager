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
use std::path::PathBuf;
use tokio::sync::RwLock;
use tower_http::cors::{CorsLayer, Any};
use tower_http::services::ServeDir;
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

    // Determine frontend path
    let frontend_path = std::env::current_dir()?
        .parent()
        .map(|p| p.join("frontend").join("dist"))
        .unwrap_or_else(|| PathBuf::from("../frontend/dist"));

    tracing::info!("Frontend path: {:?}", frontend_path);

    // Build router with API routes
    let api_router = Router::new()
        .route("/health", get(api::health_check))
        .route("/chat", post(api::chat))
        .route("/chat/stream", post(api::chat_stream))
        .route("/settings", get(api::get_settings))
        .route("/settings", put(api::update_settings))
        .route("/projects", get(api::list_projects))
        .route("/projects", post(api::create_project))
        .route("/projects/:id", get(api::get_project))
        .route("/projects/:id/files", get(api::list_files))
        .route("/projects/:id/versions/*path", get(api::list_file_versions))
        .route("/projects/:id/version/:version/*path", get(api::get_file_version))
        .route("/projects/:id/restore/:version/*path", post(api::restore_file_version))
        .route("/projects/:id/files/*path", get(api::get_file))
        .route("/projects/:id/files/*path", post(api::write_file))
        .route("/projects/:id/timeline", get(api::get_timeline))
        .route("/projects/:id/suggestions", get(api::get_suggestions))
        .route("/projects/:id/suggestions/stream", get(api::stream_suggestions))
        .route("/projects/:id/suggestions/:suggestion_id/accept", post(api::accept_suggestion))
        .route("/projects/:id/suggestions/:suggestion_id/dismiss", post(api::dismiss_suggestion))
        .route("/projects/:id/maintenance/trigger", post(api::trigger_maintenance))
        .with_state(state.clone());

    // Build main app with static file serving
    let app = Router::new()
        // WebSocket endpoint
        .route("/ws", get(websocket::websocket_handler))
        .with_state(state)
        // API routes under /api prefix
        .nest("/api", api_router)
        // Serve static files from frontend/dist (fallback to index.html for SPA)
        .fallback_service(ServeDir::new(frontend_path).append_index_html_on_directories(true))
        // CORS layer
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        );

    let addr = SocketAddr::from(([127, 0, 0, 1], 8000));
    tracing::info!("Listening on {}", addr);
    tracing::info!("Frontend: http://localhost:8000");
    tracing::info!("API: http://localhost:8000/api");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

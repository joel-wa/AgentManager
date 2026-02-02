use reqwest::Client;
use serde::{de::DeserializeOwned, Serialize};

/// HTTP client for communicating with Python services
pub struct HttpClient {
    client: Client,
}

#[allow(dead_code)]
impl HttpClient {
    pub fn new() -> Self {
        Self {
            client: Client::new(),
        }
    }

    /// POST request with JSON body
    pub async fn post<T, R>(&self, url: &str, body: &T) -> anyhow::Result<R>
    where
        T: Serialize,
        R: DeserializeOwned,
    {
        let response = self.client
            .post(url)
            .json(body)
            .send()
            .await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            anyhow::bail!("Request failed: {}", response.status())
        }
    }

    /// GET request
    pub async fn get<R>(&self, url: &str) -> anyhow::Result<R>
    where
        R: DeserializeOwned,
    {
        let response = self.client
            .get(url)
            .send()
            .await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            anyhow::bail!("Request failed: {}", response.status())
        }
    }

    /// Health check for a service
    pub async fn health_check(&self, url: &str) -> bool {
        self.client
            .get(url)
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false)
    }
}

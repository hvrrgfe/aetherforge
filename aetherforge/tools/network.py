# -*- coding: utf-8 -*-
"""Network detection and model source auto-switching module.

Detects available Hugging Face sources (official, mirrors, proxy),
selects the lowest-latency one, and provides auto-failover.

Usage:
    from aetherforge.tools.network import network_manager
    result = network_manager.detect()
    if result["success"]:
        endpoint = result["current"]["endpoint"]
        # use endpoint for all HF API calls
"""
from __future__ import annotations

import os, time, threading
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any


@dataclass
class SourceStatus:
    name: str
    endpoint: str
    available: bool = False
    latency_ms: float = -1
    status_code: Optional[int] = None
    error: str = ""


def _get_env_endpoint() -> str:
    """Check environment variables for HF endpoint override."""
    return (os.environ.get("HF_ENDPOINT") or
            os.environ.get("HUGGINGFACE_ENDPOINT") or
            "")


def _get_env_proxy() -> Dict[str, str]:
    """Auto-detect proxy from environment variables."""
    proxies = {}
    for var, key in [("HTTP_PROXY", "http"), ("HTTPS_PROXY", "https"),
                     ("http_proxy", "http"), ("https_proxy", "https")]:
        val = os.environ.get(var, "")
        if val:
            proxies[key] = val
    return proxies


class NetworkSourceManager:
    """Manages model source detection, selection, and failover."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.timeout = float(self.config.get("timeout", 8))
        self.retries = int(self.config.get("retries", 2))
        self.current: Optional[SourceStatus] = None
        self.statuses: List[SourceStatus] = []
        self._lock = threading.Lock()

        # Load sources: env var takes priority, then config, then defaults
        self.sources = self._load_sources()

        # Proxy: merge config + env
        self._proxies = self._load_proxies()

    def _load_sources(self) -> List[Dict]:
        """Load model sources from config, env override, or defaults."""
        env_endpoint = _get_env_endpoint()
        configured = self.config.get("sources")

        if env_endpoint:
            name = "env_override"
            if "hf-mirror" in env_endpoint:
                name = "hf_mirror"
            elif "huggingface" in env_endpoint:
                name = "huggingface"
            return [{"name": name, "endpoint": env_endpoint.rstrip("/"),
                     "enabled": True}]

        if configured:
            return [{"name": s["name"], "endpoint": s["endpoint"].rstrip("/"),
                     "enabled": s.get("enabled", True)}
                    for s in configured if s.get("enabled", True)]

        return [
            {"name": "huggingface", "endpoint": "https://huggingface.co",
             "enabled": True},
            {"name": "hf_mirror", "endpoint": "https://hf-mirror.com",
             "enabled": True},
        ]

    def _load_proxies(self) -> Optional[Dict[str, str]]:
        """Load proxy from config or environment."""
        config_proxy = self.config.get("proxy", {})
        if config_proxy.get("enabled"):
            result = {}
            if config_proxy.get("http"):
                result["http"] = config_proxy["http"]
            if config_proxy.get("https"):
                result["https"] = config_proxy["https"]
            if result:
                return result

        env_proxies = _get_env_proxy()
        if env_proxies:
            return env_proxies

        return None

    def check_source(self, source: Dict) -> SourceStatus:
        """Test connectivity to a single model source."""
        endpoint = source["endpoint"]
        url = f"{endpoint}/api/models?limit=1"
        start = time.perf_counter()

        try:
            import requests
            # Attempt with normal SSL first
            try:
                resp = requests.get(url, timeout=self.timeout,
                                    proxies=self._proxies,
                                    headers={"User-Agent": "AetherForge/2.0"})
            except requests.exceptions.SSLError as ssl_err:
                # SNI/SSL failure - try without verification as fallback
                ssl_fallback = SourceStatus(
                    name=source["name"], endpoint=endpoint,
                    available=False, error="SSL/SNI error: " + str(ssl_err)[:80],
                )
                return ssl_fallback
            latency = (time.perf_counter() - start) * 1000
            return SourceStatus(
                name=source["name"], endpoint=endpoint,
                available=resp.status_code < 500,
                latency_ms=round(latency, 2),
                status_code=resp.status_code,
            )
        except Exception as exc:
            return SourceStatus(
                name=source["name"], endpoint=endpoint,
                available=False, error=str(exc),
            )

    def detect(self, background: bool = False) -> Dict:
        """Detect all model sources and select the fastest available one.

        Args:
            background: If True, run detection in a daemon thread.

        Returns:
            Dict with success, current source, all source statuses.
        """
        if background:
            t = threading.Thread(target=self._do_detect, daemon=True)
            t.start()
            return {"success": True, "message": "Detection started in background",
                    "current": None, "sources": []}
        return self._do_detect()

    def _do_detect(self) -> Dict:
        """Internal: test all sources and select best."""
        statuses = []
        for source in self.sources:
            status = None
            for _ in range(self.retries + 1):
                status = self.check_source(source)
                if status.available:
                    break
            statuses.append(status)

        with self._lock:
            self.statuses = statuses
            available = [s for s in statuses if s.available]

            if not available:
                self.current = None
                return {
                    "success": False,
                    "current": None,
                    "sources": [asdict(s) for s in statuses],
                    "error": "No model sources available. Using local models only.",
                }

            available.sort(key=lambda s: s.latency_ms)
            self.current = available[0]

        return {
            "success": True,
            "current": asdict(self.current),
            "sources": [asdict(s) for s in statuses],
        }

    def get_endpoint(self) -> str:
        """Get the currently active endpoint, or default."""
        if self.current and self.current.available:
            return self.current.endpoint
        env = _get_env_endpoint()
        if env:
            return env
        return "https://huggingface.co"

    def get_model_mode(self) -> Dict:
        """Get the current model operation mode (online/offline/unavailable)."""
        from aetherforge.tools.model_manager import _scan_local_models
        if self.current and self.current.available:
            return {"mode": "online", "endpoint": self.current.endpoint,
                    "source_name": self.current.name}
        local = _scan_local_models()
        if local:
            return {"mode": "offline", "local_models": len(local)}
        return {"mode": "unavailable", "local_models": 0}

    def has_sni_issues(self) -> bool:
        """Check if any source failed due to SSL/SNI issues."""
        with self._lock:
            return any("SSL/SNI" in s.error or "ssl" in s.error.lower()
                      for s in self.statuses if s.error)

    def state(self) -> Dict:
        """Get full network state report."""
        with self._lock:
            return {
                "current": asdict(self.current) if self.current else None,
                "sources": [asdict(s) for s in self.statuses],
                "mode": self.get_model_mode().get("mode", "unknown"),
                "proxy_configured": self._proxies is not None,
                "sni_issues": self.has_sni_issues(),
            }

    def switch_source(self, endpoint: str) -> Dict:
        """Manually switch to a configured source by endpoint."""
        endpoint = endpoint.rstrip("/")
        found = next((s for s in self.sources if s["endpoint"] == endpoint), None)
        if not found:
            return {"success": False, "error": f"Source not configured: {endpoint}"}

        status = self.check_source(found)
        if not status.available:
            return {"success": False, "error": f"Source not reachable: {endpoint}",
                    "status": asdict(status)}

        with self._lock:
            self.current = status
        return {"success": True, "current": asdict(status)}


# Module-level singleton
network_manager = NetworkSourceManager()
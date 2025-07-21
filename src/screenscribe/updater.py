"""Self-update functionality for screenscribe."""

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


class GitHubUpdater:
    """Handle GitHub-based updates for screenscribe."""
    
    def __init__(self, repo: str = "grimmolf/screenscribe"):
        self.repo = repo
        self.github_api_base = "https://api.github.com"
        self.current_version = self._get_current_version()
        
    def _get_current_version(self) -> Optional[str]:
        """Get the current installed version."""
        try:
            # Try to get version from package metadata
            import importlib.metadata
            return importlib.metadata.version("screenscribe")
        except Exception:
            # Fallback: try to get git tag from the current directory
            try:
                result = subprocess.run(
                    ["git", "describe", "--tags", "--exact-match", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent.parent
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
            return None
    
    def _make_github_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make a request to GitHub API."""
        url = f"{self.github_api_base}/repos/{self.repo}/{endpoint}"
        try:
            req = Request(url)
            req.add_header('User-Agent', 'screenscribe-updater')
            
            with urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    return json.loads(response.read().decode('utf-8'))
                else:
                    logger.error(f"GitHub API request failed: {response.getcode()}")
                    return None
                    
        except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
            logger.error(f"Error making GitHub request: {e}")
            return None
    
    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """Get latest release information from GitHub."""
        return self._make_github_request("releases/latest")
    
    def get_latest_commit(self) -> Optional[Dict[str, Any]]:
        """Get latest commit information from main branch."""
        return self._make_github_request("commits/main")
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check if updates are available.
        
        Returns:
            Tuple of (has_update, latest_version, release_info)
        """
        if not self.current_version:
            # Can't determine current version, assume update available
            logger.warning("Cannot determine current version, checking for latest release")
            release_info = self.get_latest_release()
            if release_info:
                return True, release_info.get("tag_name"), release_info
            return False, None, None
        
        # Get latest release
        release_info = self.get_latest_release()
        if not release_info:
            logger.error("Could not fetch latest release information")
            return False, None, None
        
        latest_version = release_info.get("tag_name")
        if not latest_version:
            logger.error("Latest release has no tag name")
            return False, None, None
        
        # Simple version comparison (assumes semantic versioning)
        has_update = self._compare_versions(self.current_version, latest_version)
        
        return has_update, latest_version, release_info
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings. Returns True if latest > current."""
        try:
            # Remove 'v' prefix if present
            current_clean = current.lstrip('v')
            latest_clean = latest.lstrip('v')
            
            # Split into parts and compare
            current_parts = [int(x) for x in current_clean.split('.')]
            latest_parts = [int(x) for x in latest_clean.split('.')]
            
            # Pad with zeros to make same length
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            return latest_parts > current_parts
            
        except ValueError:
            # Fallback: string comparison
            return latest > current
    
    def update_from_source(self, target_ref: str = "main") -> bool:
        """
        Update screenscribe from GitHub source.
        
        Args:
            target_ref: Git reference to update to (tag, branch, commit)
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            logger.info(f"Updating screenscribe from {self.repo}#{target_ref}")
            
            # Clone repository to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                repo_path = temp_path / "screenscribe"
                
                logger.info("Cloning repository...")
                clone_result = subprocess.run([
                    "git", "clone", 
                    f"https://github.com/{self.repo}.git",
                    str(repo_path)
                ], capture_output=True, text=True, timeout=60)
                
                if clone_result.returncode != 0:
                    logger.error(f"Failed to clone repository: {clone_result.stderr}")
                    return False
                
                # Checkout target reference
                if target_ref != "main":
                    logger.info(f"Checking out {target_ref}...")
                    checkout_result = subprocess.run([
                        "git", "checkout", target_ref
                    ], cwd=repo_path, capture_output=True, text=True)
                    
                    if checkout_result.returncode != 0:
                        logger.error(f"Failed to checkout {target_ref}: {checkout_result.stderr}")
                        return False
                
                # Install the updated version
                logger.info("Installing updated version...")
                
                # Determine if we need Apple Silicon dependencies
                install_path = str(repo_path)
                if self._is_apple_silicon():
                    install_path = f"{install_path}[apple]"
                
                install_result = subprocess.run([
                    "uv", "tool", "install", "--editable", install_path, "--force"
                ], capture_output=True, text=True, timeout=300)
                
                if install_result.returncode != 0:
                    logger.error(f"Failed to install update: {install_result.stderr}")
                    return False
                
                logger.info("Update completed successfully!")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("Update process timed out")
            return False
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def _is_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon."""
        try:
            import platform
            return platform.system() == "Darwin" and platform.machine() == "arm64"
        except Exception:
            return False
    
    def update_to_latest_release(self) -> bool:
        """Update to the latest GitHub release."""
        has_update, latest_version, release_info = self.check_for_updates()
        
        if not has_update:
            logger.info("Already up to date!")
            return True
        
        if not latest_version:
            logger.error("Could not determine latest version")
            return False
        
        logger.info(f"Updating from {self.current_version} to {latest_version}")
        return self.update_from_source(latest_version)
    
    def update_to_latest_commit(self) -> bool:
        """Update to the latest commit on main branch."""
        logger.info("Updating to latest development version...")
        return self.update_from_source("main")
    
    def get_update_info(self) -> Dict[str, Any]:
        """Get comprehensive update information."""
        has_update, latest_version, release_info = self.check_for_updates()
        
        info = {
            "current_version": self.current_version,
            "latest_version": latest_version,
            "has_update": has_update,
            "repo": self.repo
        }
        
        if release_info:
            info.update({
                "release_date": release_info.get("published_at"),
                "release_notes": release_info.get("body"),
                "release_url": release_info.get("html_url")
            })
        
        # Get latest commit info
        commit_info = self.get_latest_commit()
        if commit_info:
            info["latest_commit"] = {
                "sha": commit_info.get("sha", "")[:8],
                "message": commit_info.get("commit", {}).get("message", "").split('\n')[0],
                "date": commit_info.get("commit", {}).get("author", {}).get("date"),
                "url": commit_info.get("html_url")
            }
        
        return info


def check_for_updates(repo: str = "grimmolf/screenscribe") -> Dict[str, Any]:
    """Convenience function to check for updates."""
    updater = GitHubUpdater(repo)
    return updater.get_update_info()


def update_screenscribe(repo: str = "grimmolf/screenscribe", to_latest: bool = True) -> bool:
    """
    Update screenscribe to latest version.
    
    Args:
        repo: GitHub repository in format "owner/repo"  
        to_latest: If True, update to latest release. If False, update to latest commit.
        
    Returns:
        True if successful, False otherwise
    """
    updater = GitHubUpdater(repo)
    
    if to_latest:
        return updater.update_to_latest_release()
    else:
        return updater.update_to_latest_commit()
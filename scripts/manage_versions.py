import sys
import os
import json
import logging
import requests
from typing import Dict, Optional

class VersionManager:
    def __init__(self, apps_root: str):
        self.apps_root = apps_root
        self.keep_versions = 10
        self.logger = self._init_logger()

    def _init_logger(self):
        logger = logging.getLogger("VersionManager")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def manage(self, action: str, target: Optional[str] = None, keep: int = 5):
        self.keep_versions = max(1, keep)
        for app in os.listdir(self.apps_root):
            path = os.path.join(self.apps_root, app)
            config_path = os.path.join(path, 'app.json')
            
            if not self._valid_app_path(path, config_path, target):
                continue

            if action == 'update':
                self._update_versions(app, config_path)
            elif action == 'remove':
                self._remove_versions(app, config_path)

    def _valid_app_path(self, path: str, config: str, target: Optional[str]) -> bool:
        return os.path.isdir(path) and os.path.isfile(config) and (not target or os.path.basename(path) == target)

    def _update_versions(self, app: str, config: str):
        self._process_versions(app, config, update=True)

    def _remove_versions(self, app: str, config: str):
        self._process_versions(app, config, update=False)

    def _process_versions(self, app: str, config: str, update: bool):
        try:
            with open(config, 'r') as f:
                data = json.load(f)

            if not self._valid_repo(data.get('gitURL/s')):
                return

            if update:
                result = self._fetch_new_versions(data)
                if not result['success']:
                    self.logger.error(f"Failed {app}: {result['message']}")
                    return
                data['versions'] = result['versions']
                self.logger.info(f"Updated {app}: {result['message']}")
            else:
                data['versions'] = []
                self.logger.info(f"Removed versions: {app}")

            self._save_config(config, data)

        except Exception as e:
            self.logger.error(f"Error processing {app}: {str(e)}")

    def _fetch_new_versions(self, data: Dict) -> Dict:
        repos = data.get('gitURL/s', [])
        repos = [repos] if isinstance(repos, str) else repos
        existing = {v['url'] for v in data.get('versions', [])}
        new_versions = []

        for repo in repos:
            if not self._valid_gh_url(repo):
                continue

            owner, repo_name = repo.rstrip('/').split('/')[-2:]
            headers = {'Authorization': f'token {os.environ.get("REPO_TOKEN")}'}

            try:
                response = requests.get(f'https://api.github.com/repos/{owner}/{repo_name}/releases', 
                                        headers=headers, timeout=10)
                if response.status_code != 200:
                    continue

                for release in response.json():
                    for asset in release.get('assets', []):
                        if asset['name'].lower().endswith(('.tipa', '.ipa')):
                            version = {
                                'version': release['tag_name'].lstrip('v'),
                                'date': release['published_at'].split('T')[0],
                                'size': asset['size'],
                                'url': asset['browser_download_url']
                            }
                            if version['url'] not in existing:
                                new_versions.append(version)

            except Exception as e:
                self.logger.error(f"API error: {str(e)}")

        versions = data.get('versions', []) + new_versions
        versions.sort(key=lambda x: x['date'], reverse=True)

        unique_versions = {}
        for version in versions:
            version_number = version['version']
            if version_number not in unique_versions:
                unique_versions[version_number] = version
        versions = list(unique_versions.values())

        versions = versions[:self.keep_versions]
        
        return {
            'success': True ,
            'message': f"Added {len(new_versions)} versions" if new_versions else "No new versions",
            'versions': versions
        }

    def _save_config(self, path: str, data: Dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def _valid_repo(self, repo) -> bool:
        if not repo:
            self.logger.warning("No repository information provided.")
            return False

        repos = repo if isinstance(repo, list) else [repo]
        valid = any(self._valid_gh_url(u) for u in repos)
        if not valid:
            self.logger.warning(f"Invalid GitHub URLs found: {repos}")
        return valid

    def _valid_gh_url(self, url: str) -> bool:
        return url.startswith(("https://github.com/", "http://github.com/"))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: manage_versions.py <action> [keep_versions] [app1,app2,...]")
        sys.exit(1)

    action = sys.argv[1].lower()
    keep_versions = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    targets = sys.argv[3].split(',') if len(sys.argv) > 3 else [None]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    apps_dir = os.path.join(current_dir, "..", "Apps")
    manager = VersionManager(apps_dir)
    
    for target in targets:
        manager.manage(action, target.strip() if target else None, keep_versions)
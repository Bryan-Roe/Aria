"""Automated Backup System for QAI Models, Configs, and Data"""

import hashlib
import json
import os
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class BackupManager:
    """Manages automated backups of training artifacts"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.backup_dir / "backup_manifest.json"
        self.load_manifest()

    def load_manifest(self):
        """Load backup manifest"""
        if self.manifest_file.exists():
            with open(self.manifest_file, "r") as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"backups": [], "last_backup": None}

    def save_manifest(self):
        """Save backup manifest"""
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def create_backup(
        self,
        include_models: bool = True,
        include_configs: bool = True,
        include_datasets: bool = False,
        include_logs: bool = True,
        compress: bool = True,
        description: str = "",
        incremental: bool = False,
    ) -> Dict:
        """Create comprehensive backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"qai_backup_{timestamp}"
        # Ensure uniqueness if multiple backups created within same second
        # Build set of existing backup names for O(1) lookup
        existing_names = {b.get("name") for b in self.manifest.get("backups", [])}
        suffix_counter = 2
        while backup_name in existing_names:
            backup_name = f"qai_backup_{timestamp}_{suffix_counter}"
            suffix_counter += 1
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        # Build map of previous file checksums if incremental requested
        previous_checksums: Dict[str, str] = {}
        if incremental and self.manifest["backups"]:
            # Use most recent backup entry (last in list) – supports either compressed or directory backups
            last_backup = self.manifest["backups"][-1]
            for entry in last_backup.get("files", []):
                # Legacy entries may be strings (no checksum)
                if isinstance(entry, dict):
                    previous_checksums[entry["path"]] = entry.get("checksum", "")
                elif isinstance(entry, str):
                    # Cannot compute checksum for legacy compressed backup – treat as changed
                    continue

        backup_info = {
            "name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "includes": {
                "models": include_models,
                "configs": include_configs,
                "datasets": include_datasets,
                "logs": include_logs,
            },
            "files": [],  # list[{'path': str, 'checksum': str, 'unchanged': bool}]
            "size_bytes": 0,
            "checksum": None,
            "incremental": incremental,
            "unchanged_files": 0,
            "changed_files": 0,
        }

        print(f"Creating backup: {backup_name}")

        # Backup models
        if include_models:
            models_src = Path("data_out/lora_training/lora_adapter")
            if models_src.exists():
                models_dst = backup_path / "models"
                models_dst.mkdir(parents=True, exist_ok=True)
                self._copy_directory(
                    models_src, models_dst, backup_info, previous_checksums, incremental
                )
                print("  ✓ Backed up models")

        # Backup configs
        if include_configs:
            configs = [
                "autotrain.yaml",
                "quantum_autorun.yaml",
                "evaluation_autorun.yaml",
                "batch_eval_config.yaml",
            ]
            configs_dst = backup_path / "configs"
            configs_dst.mkdir(parents=True, exist_ok=True)

            for config_file in configs:
                config_path = Path(config_file)
                if config_path.exists():
                    dst = configs_dst / config_file
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    # Use unified copy/link logic for incremental detection
                    self._copy_or_link(
                        config_path, dst, backup_info, previous_checksums, incremental
                    )

            print("  ✓ Backed up configs")

        # Backup datasets (optional - can be large)
        if include_datasets:
            datasets_src = Path("datasets")
            if datasets_src.exists():
                datasets_dst = backup_path / "datasets"
                datasets_dst.mkdir(parents=True, exist_ok=True)
                self._copy_directory(
                    datasets_src,
                    datasets_dst,
                    backup_info,
                    previous_checksums,
                    incremental,
                )
                print("  ✓ Backed up datasets")

        # Backup training logs
        if include_logs:
            logs_src = Path("data_out/autotrain")
            if logs_src.exists():
                logs_dst = backup_path / "logs"
                logs_dst.mkdir(parents=True, exist_ok=True)

                # Only backup JSON files (not large model files)
                for json_file in logs_src.rglob("*.json"):
                    rel_path = json_file.relative_to(logs_src)
                    dst = logs_dst / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    self._copy_or_link(
                        json_file, dst, backup_info, previous_checksums, incremental
                    )

                print("  ✓ Backed up logs")

        # Create backup metadata
        metadata = {
            "backup_info": backup_info,
            "system_info": {
                "python_version": self._get_python_version(),
                "pytorch_version": self._get_pytorch_version(),
                "cuda_available": self._check_cuda(),
            },
        }

        metadata_file = backup_path / "backup_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Compress if requested
        if compress:
            archive_path = self.backup_dir / f"{backup_name}.tar.gz"
            print("  Compressing backup...")

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_name)

            # Calculate archive checksum
            backup_info["checksum"] = self.calculate_checksum(archive_path)
            backup_info["compressed_path"] = str(archive_path)
            backup_info["compressed_size"] = archive_path.stat().st_size

            # Remove uncompressed directory
            shutil.rmtree(backup_path)

            print(f"  ✓ Compressed to {archive_path.name}")
            print(f"  Size: {backup_info['compressed_size'] / 1024 / 1024:.2f} MB")
        else:
            backup_info["path"] = str(backup_path)

        # Update manifest
        self.manifest["backups"].append(backup_info)
        self.manifest["last_backup"] = backup_info["timestamp"]
        self.save_manifest()

        print(f"✅ Backup complete: {backup_name}")
        return backup_info

    def _copy_directory(
        self,
        src: Path,
        dst: Path,
        backup_info: Dict,
        previous_checksums: Dict[str, str],
        incremental: bool,
    ):
        """Recursively copy directory and track files (supports incremental)"""
        for item in src.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src)
                dst_path = dst / rel_path
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                self._copy_or_link(
                    item, dst_path, backup_info, previous_checksums, incremental
                )

    def _copy_or_link(
        self,
        src_file: Path,
        dst_path: Path,
        backup_info: Dict,
        previous_checksums: Dict[str, str],
        incremental: bool,
    ):
        """Copy file or create hardlink if unchanged in incremental mode"""
        checksum = self.calculate_checksum(src_file)
        file_path_str = str(src_file)
        unchanged = False
        if incremental and previous_checksums.get(file_path_str) == checksum:
            # Attempt hardlink for efficiency
            try:
                os.link(src_file, dst_path)
                unchanged = True
            except Exception:
                shutil.copy2(src_file, dst_path)  # Fallback
        else:
            shutil.copy2(src_file, dst_path)
        backup_info["files"].append(
            {"path": file_path_str, "checksum": checksum, "unchanged": unchanged}
        )
        size = src_file.stat().st_size
        backup_info["size_bytes"] += size
        if unchanged:
            backup_info["unchanged_files"] += 1
        else:
            backup_info["changed_files"] += 1

    def _get_python_version(self) -> str:
        """Get Python version"""
        import sys

        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _get_pytorch_version(self) -> str:
        """Get PyTorch version"""
        try:
            import torch

            return torch.__version__
        except ImportError:
            return "Not installed"

    def _check_cuda(self) -> bool:
        """Check CUDA availability"""
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def list_backups(self) -> List[Dict]:
        """List all backups"""
        return self.manifest["backups"]

    def restore_backup(self, backup_name: str, target_dir: str = "."):
        """Restore backup to target directory"""
        backup_info = None
        for backup in self.manifest["backups"]:
            if backup["name"] == backup_name:
                backup_info = backup
                break

        if not backup_info:
            raise ValueError(f"Backup '{backup_name}' not found")

        print(f"Restoring backup: {backup_name}")

        if "compressed_path" in backup_info:
            archive_path = Path(backup_info["compressed_path"])

            if not archive_path.exists():
                raise FileNotFoundError(f"Backup archive not found: {archive_path}")

            # Verify checksum
            if backup_info.get("checksum"):
                current_checksum = self.calculate_checksum(archive_path)
                if current_checksum != backup_info["checksum"]:
                    raise ValueError("Backup checksum mismatch! File may be corrupted.")

            # Extract archive safely - filter to prevent path traversal attacks
            with tarfile.open(archive_path, "r:gz") as tar:
                # Python 3.12+ has built-in filter, for older versions we validate manually
                target_path = Path(target_dir).resolve()
                safe_members = []
                for member in tar.getmembers():
                    member_path = (target_path / member.name).resolve()
                    # Ensure extraction stays within target directory
                    if (
                        not str(member_path).startswith(str(target_path) + os.sep)
                        and member_path != target_path
                    ):
                        raise ValueError(
                            f"Attempted path traversal in tarfile: {member.name}"
                        )
                    safe_members.append(member)
                # Extract only validated members
                tar.extractall(
                    target_dir, members=safe_members
                )  # nosec B202 - members validated above

            print(f"✅ Backup restored to: {target_dir}")
        else:
            backup_path = Path(backup_info["path"])
            if backup_path.exists():
                shutil.copytree(backup_path, Path(target_dir) / backup_name)
                print(f"✅ Backup restored to: {target_dir}/{backup_name}")
            else:
                raise FileNotFoundError(f"Backup directory not found: {backup_path}")

    def delete_backup(self, backup_name: str):
        """Delete a backup"""
        backup_info = None
        backup_index = None

        for idx, backup in enumerate(self.manifest["backups"]):
            if backup["name"] == backup_name:
                backup_info = backup
                backup_index = idx
                break

        if not backup_info:
            raise ValueError(f"Backup '{backup_name}' not found")

        # Delete archive or directory
        if "compressed_path" in backup_info:
            archive_path = Path(backup_info["compressed_path"])
            if archive_path.exists():
                archive_path.unlink()
        elif "path" in backup_info:
            backup_path = Path(backup_info["path"])
            if backup_path.exists():
                shutil.rmtree(backup_path)

        # Remove from manifest
        self.manifest["backups"].pop(backup_index)
        self.save_manifest()

        print(f"✅ Deleted backup: {backup_name}")

    def cleanup_old_backups(self, keep_count: int = 5):
        """Keep only the most recent N backups"""
        if len(self.manifest["backups"]) <= keep_count:
            print(
                f"Only {len(self.manifest['backups'])} backups exist, no cleanup needed"
            )
            return

        # Sort by timestamp
        sorted_backups = sorted(
            self.manifest["backups"], key=lambda x: x["timestamp"], reverse=True
        )

        # Delete old backups
        to_delete = sorted_backups[keep_count:]
        for backup in to_delete:
            try:
                self.delete_backup(backup["name"])
                print(f"  Cleaned up: {backup['name']}")
            except Exception as e:
                print(f"  Failed to delete {backup['name']}: {e}")

        print(f"✅ Cleanup complete. Kept {keep_count} most recent backups")


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="QAI Backup Manager")
    parser.add_argument(
        "action",
        choices=["create", "list", "restore", "delete", "cleanup"],
        help="Action to perform",
    )
    parser.add_argument("--name", help="Backup name (for restore/delete)")
    parser.add_argument("--no-models", action="store_true", help="Exclude models")
    parser.add_argument("--no-configs", action="store_true", help="Exclude configs")
    parser.add_argument(
        "--include-datasets", action="store_true", help="Include datasets (large)"
    )
    parser.add_argument("--no-logs", action="store_true", help="Exclude logs")
    parser.add_argument("--no-compress", action="store_true", help="Skip compression")
    parser.add_argument("--description", default="", help="Backup description")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Perform incremental backup (hardlink unchanged files)",
    )
    parser.add_argument(
        "--target-dir", default=".", help="Target directory for restore"
    )
    parser.add_argument(
        "--keep", type=int, default=5, help="Number of backups to keep (cleanup)"
    )

    args = parser.parse_args()

    manager = BackupManager()

    if args.action == "create":
        backup_info = manager.create_backup(
            include_models=not args.no_models,
            include_configs=not args.no_configs,
            include_datasets=args.include_datasets,
            include_logs=not args.no_logs,
            compress=not args.no_compress,
            description=args.description,
            incremental=args.incremental,
        )
        print(f"\n📦 Backup ID: {backup_info['name']}")
        print(
            f"📁 Files: {len(backup_info['files'])} (changed: {backup_info['changed_files']}, unchanged: {backup_info['unchanged_files']})"
        )
        print(
            f"💾 Size: {backup_info.get('compressed_size', backup_info['size_bytes']) / 1024 / 1024:.2f} MB"
        )

    elif args.action == "list":
        backups = manager.list_backups()
        if not backups:
            print("No backups found")
        else:
            print(f"\n📋 Available Backups ({len(backups)}):\n")
            for backup in reversed(backups):
                size = backup.get("compressed_size", backup["size_bytes"]) / 1024 / 1024
                timestamp = datetime.fromisoformat(backup["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(f"  {backup['name']}")
                print(f"    Time: {timestamp}")
                print(f"    Size: {size:.2f} MB")
                print(f"    Files: {len(backup['files'])}")
                if backup["description"]:
                    print(f"    Desc: {backup['description']}")
                print()

    elif args.action == "restore":
        if not args.name:
            print("Error: --name required for restore")
        else:
            manager.restore_backup(args.name, args.target_dir)

    elif args.action == "delete":
        if not args.name:
            print("Error: --name required for delete")
        else:
            manager.delete_backup(args.name)

    elif args.action == "cleanup":
        manager.cleanup_old_backups(args.keep)

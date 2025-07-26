"""
Configuration Learning Manager

This script helps manage and update the configuration based on learning insights
from schema discovery iterations. It allows you to review new discoveries and
update the canonical configuration with improved field definitions.

Key Features:
- Review learning insights from schema discovery sessions
- Update canonical configuration with new field knowledge
- Merge multiple learning sessions into consolidated config updates
- Validate configuration changes before applying
"""

import os
import sys
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigLearningManager:
    """
    Manager for updating configuration based on schema discovery learning
    """
    
    def __init__(self):
        """Initialize the config learning manager"""
        self.project_root = project_root
        self.config_file = project_root / "llm_columns_canonical.yaml"
        self.learning_dir = project_root / "config" / "learning"
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        
    def discover_learning_files(self) -> List[str]:
        """Discover all learning insight files"""
        if not self.learning_dir.exists():
            return []
        
        learning_files = list(self.learning_dir.glob("schema_learning_*.json"))
        learning_files.sort()  # Sort by timestamp
        
        logger.info(f"Found {len(learning_files)} learning insight files")
        return [str(f) for f in learning_files]
    
    def load_learning_insights(self, learning_files: List[str]) -> Dict[str, Any]:
        """Load and consolidate learning insights from multiple files"""
        consolidated_insights = {
            "new_fields": [],
            "updated_statistics": [],
            "potential_relationships": [],
            "data_quality_insights": []
        }
        
        for file_path in learning_files:
            try:
                with open(file_path, 'r') as f:
                    learning_data = json.load(f)
                
                insights = learning_data.get("insights", {})
                
                # Consolidate insights
                for key in consolidated_insights.keys():
                    if key in insights:
                        consolidated_insights[key].extend(insights[key])
                
                logger.info(f"Loaded insights from {file_path}")
                
            except Exception as e:
                logger.warning(f"Could not load {file_path}: {e}")
        
        # Remove duplicates from new fields
        seen_fields = set()
        unique_new_fields = []
        for field in consolidated_insights["new_fields"]:
            field_name = field["field_name"]
            if field_name not in seen_fields:
                unique_new_fields.append(field)
                seen_fields.add(field_name)
        
        consolidated_insights["new_fields"] = unique_new_fields
        
        return consolidated_insights
    
    def load_current_config(self) -> Dict[str, Any]:
        """Load current canonical configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Could not load current config: {e}")
        
        # Return default structure if no config exists
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "fields": {}
        }
    
    def generate_config_updates(self, insights: Dict[str, Any], 
                              current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate configuration updates based on learning insights"""
        updates = {
            "new_field_definitions": {},
            "updated_field_statistics": {},
            "suggested_business_purposes": {},
            "data_quality_improvements": []
        }
        
        current_fields = current_config.get("fields", {})
        
        # Process new fields
        for new_field in insights.get("new_fields", []):
            field_name = new_field["field_name"]
            
            if field_name not in current_fields:
                # Generate suggested business purpose based on field name patterns
                suggested_purpose = self._suggest_business_purpose(field_name, new_field)
                
                updates["new_field_definitions"][field_name] = {
                    "data_type": new_field["data_type"],
                    "business_purpose": suggested_purpose,
                    "importance_tier": self._suggest_importance_tier(field_name, new_field),
                    "completeness": new_field["completeness"],
                    "unique_values": new_field["unique_values"],
                    "sample_values": new_field["sample_values"],
                    "business_rules": [],
                    "relationships": [],
                    "discovered_date": datetime.now().isoformat()
                }
        
        # Process updated statistics
        for stat_update in insights.get("updated_statistics", []):
            field_name = stat_update["field_name"]
            updates["updated_field_statistics"][field_name] = {
                "old_completeness": stat_update["old_completeness"],
                "new_completeness": stat_update["new_completeness"],
                "change_magnitude": abs(stat_update["new_completeness"] - stat_update["old_completeness"])
            }
        
        return updates
    
    def _suggest_business_purpose(self, field_name: str, field_data: Dict[str, Any]) -> str:
        """Suggest business purpose based on field name patterns"""
        field_lower = field_name.lower()
        
        # Common retail analytics field patterns
        if "sales" in field_lower or "revenue" in field_lower:
            return "Sales performance and revenue tracking"
        elif "location" in field_lower or "store" in field_lower:
            return "Location identification and geographic analysis"
        elif "priority" in field_lower or "score" in field_lower:
            return "Business priority and performance scoring"
        elif "date" in field_lower or "time" in field_lower:
            return "Temporal analysis and trend tracking"
        elif "category" in field_lower or "product" in field_lower:
            return "Product categorization and inventory analysis"
        elif "customer" in field_lower or "cust" in field_lower:
            return "Customer behavior and demographic analysis"
        elif "trend" in field_lower or "change" in field_lower:
            return "Performance trend and change analysis"
        else:
            return f"Analysis field for {field_name} - requires business context definition"
    
    def _suggest_importance_tier(self, field_name: str, field_data: Dict[str, Any]) -> int:
        """Suggest importance tier based on field characteristics"""
        field_lower = field_name.lower()
        completeness = field_data.get("completeness", 0)
        unique_ratio = field_data.get("unique_values", 0) / max(1, len(field_data.get("sample_values", [])))
        
        # Critical fields (tier 1)
        if any(keyword in field_lower for keyword in ["sales", "revenue", "location", "priority"]):
            return 1
        
        # Important fields (tier 2) 
        elif completeness > 0.8 and any(keyword in field_lower for keyword in ["date", "category", "score"]):
            return 2
        
        # Supplementary fields (tier 3)
        else:
            return 3
    
    def preview_config_changes(self, updates: Dict[str, Any]) -> str:
        """Generate a human-readable preview of proposed config changes"""
        preview = "CONFIGURATION UPDATE PREVIEW\n"
        preview += "=" * 50 + "\n\n"
        
        # New fields
        new_fields = updates.get("new_field_definitions", {})
        if new_fields:
            preview += f"NEW FIELDS TO ADD ({len(new_fields)}):\n"
            for field_name, field_def in new_fields.items():
                preview += f"  • {field_name}\n"
                preview += f"    Purpose: {field_def['business_purpose']}\n"
                preview += f"    Tier: {field_def['importance_tier']}, Completeness: {field_def['completeness']:.1%}\n"
                preview += f"    Type: {field_def['data_type']}, Unique Values: {field_def['unique_values']}\n\n"
        
        # Updated statistics
        updated_stats = updates.get("updated_field_statistics", {})
        if updated_stats:
            preview += f"FIELD STATISTICS UPDATES ({len(updated_stats)}):\n"
            for field_name, stat_update in updated_stats.items():
                change = stat_update["new_completeness"] - stat_update["old_completeness"]
                direction = "↑" if change > 0 else "↓"
                preview += f"  • {field_name}: {stat_update['old_completeness']:.1%} → {stat_update['new_completeness']:.1%} {direction}\n"
        
        # Data quality insights
        quality_insights = updates.get("data_quality_improvements", [])
        if quality_insights:
            preview += f"\nDATA QUALITY INSIGHTS ({len(quality_insights)}):\n"
            for insight in quality_insights:
                preview += f"  • {insight}\n"
        
        return preview
    
    def apply_config_updates(self, updates: Dict[str, Any], current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply updates to configuration"""
        updated_config = current_config.copy()
        
        # Ensure fields section exists
        if "fields" not in updated_config:
            updated_config["fields"] = {}
        
        # Add new fields
        new_fields = updates.get("new_field_definitions", {})
        for field_name, field_def in new_fields.items():
            updated_config["fields"][field_name] = field_def
            logger.info(f"Added new field definition: {field_name}")
        
        # Update statistics for existing fields
        updated_stats = updates.get("updated_field_statistics", {})
        for field_name, stat_update in updated_stats.items():
            if field_name in updated_config["fields"]:
                updated_config["fields"][field_name]["completeness"] = stat_update["new_completeness"]
                updated_config["fields"][field_name]["last_updated"] = datetime.now().isoformat()
                logger.info(f"Updated statistics for field: {field_name}")
        
        # Update metadata
        updated_config["last_updated"] = datetime.now().isoformat()
        updated_config["version"] = str(float(updated_config.get("version", "1.0")) + 0.1)
        
        return updated_config
    
    def save_updated_config(self, updated_config: Dict[str, Any]):
        """Save updated configuration to file"""
        # Create backup of current config
        if self.config_file.exists():
            backup_file = self.config_file.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
            import shutil
            shutil.copy2(self.config_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
        
        # Save updated config
        with open(self.config_file, 'w') as f:
            yaml.dump(updated_config, f, indent=2, default_flow_style=False)
        
        logger.info(f"Updated configuration saved to {self.config_file}")
    
    def archive_processed_learning_files(self, learning_files: List[str]):
        """Archive processed learning files"""
        archive_dir = self.learning_dir / "processed"
        archive_dir.mkdir(exist_ok=True)
        
        for file_path in learning_files:
            file_name = Path(file_path).name
            archive_path = archive_dir / file_name
            
            import shutil
            shutil.move(file_path, archive_path)
            logger.info(f"Archived {file_name} to processed directory")
    
    def run_config_update_cycle(self, auto_apply: bool = False) -> Dict[str, Any]:
        """Run complete configuration update cycle"""
        logger.info("Starting configuration update cycle")
        
        # Step 1: Discover learning files
        learning_files = self.discover_learning_files()
        if not learning_files:
            logger.info("No learning files found - nothing to update")
            return {"status": "no_updates", "message": "No learning files found"}
        
        # Step 2: Load and consolidate insights
        insights = self.load_learning_insights(learning_files)
        
        # Step 3: Load current config
        current_config = self.load_current_config()
        
        # Step 4: Generate updates
        updates = self.generate_config_updates(insights, current_config)
        
        # Step 5: Preview changes
        preview = self.preview_config_changes(updates)
        print(preview)
        
        # Step 6: Apply updates (with confirmation if not auto)
        if auto_apply or input("\nApply these configuration updates? (y/N): ").lower().startswith('y'):
            updated_config = self.apply_config_updates(updates, current_config)
            self.save_updated_config(updated_config)
            self.archive_processed_learning_files(learning_files)
            
            result = {
                "status": "success",
                "updates_applied": updates,
                "files_processed": len(learning_files),
                "new_fields_added": len(updates.get("new_field_definitions", {})),
                "stats_updated": len(updates.get("updated_field_statistics", {}))
            }
        else:
            result = {
                "status": "cancelled",
                "message": "Configuration updates cancelled by user"
            }
        
        return result


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Learning Manager")
    parser.add_argument("--auto-apply", action="store_true", 
                       help="Automatically apply updates without confirmation")
    parser.add_argument("--preview-only", action="store_true",
                       help="Only show preview of changes, don't apply")
    
    args = parser.parse_args()
    
    manager = ConfigLearningManager()
    
    if args.preview_only:
        # Just show preview
        learning_files = manager.discover_learning_files()
        if learning_files:
            insights = manager.load_learning_insights(learning_files)
            current_config = manager.load_current_config()
            updates = manager.generate_config_updates(insights, current_config)
            preview = manager.preview_config_changes(updates)
            print(preview)
        else:
            print("No learning files found for preview")
    else:
        # Run full update cycle
        result = manager.run_config_update_cycle(args.auto_apply)
        print(f"\nUpdate cycle result: {result}")


if __name__ == "__main__":
    main()

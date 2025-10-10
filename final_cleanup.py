"""
Final Cleanup - Remove Duplicate/Unnecessary Files
==================================================
Keeps only essential files for production
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Remove unnecessary files"""
    
    project_root = Path(__file__).parent
    
    print("🧹 Final Project Cleanup")
    print("="*60)
    
    # Files to remove (duplicates and unnecessary)
    files_to_remove = [
        # Duplicate poster fetchers (keep only the auto one)
        "fetch_all_posters_fast.py",
        "fetch_all_real_posters.py",
        "fetch_posters_multi.py",
        "fetch_posters_tmdb.py",
        
        # Test files
        "test_ann_working.py",
        "test_dataset.py",
        
        # Duplicate documentation (consolidate later)
        "FETCH_REAL_POSTERS_GUIDE.md",
        
        # Temporary/cache
        "__pycache__",
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "__pycache__",
        "scripts",  # If empty or unnecessary
    ]
    
    removed_count = 0
    
    # Remove files
    for file in files_to_remove:
        filepath = project_root / file
        if filepath.exists():
            if filepath.is_dir():
                shutil.rmtree(filepath)
                print(f"✅ Removed directory: {file}")
            else:
                filepath.unlink()
                print(f"✅ Removed file: {file}")
            removed_count += 1
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items.")
    print("\n📁 Remaining essential files:")
    print("  - api.py (FastAPI backend)")
    print("  - enhanced_recommendation_engine.py (AI engine)")
    print("  - fast_complete_loader.py (data loader)")
    print("  - fetch_posters_auto.py (poster fetcher)")
    print("  - optimize_posters.py (poster optimizer)")
    print("  - performance_optimizer.py (caching)")
    print("  - models/ (ANN models)")
    print("  - frontend/ (Netflix UI)")
    print("  - processed/ (datasets)")
    print("  - Documentation (*.md files)")

if __name__ == "__main__":
    cleanup_project()

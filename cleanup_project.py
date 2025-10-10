"""
Cleanup script to remove unnecessary files from the project
"""
import os
import shutil
from pathlib import Path

project_root = Path(__file__).parent

# Files to keep (core functionality)
KEEP_FILES = {
    # Core application files
    'api.py',
    'enhanced_recommendation_engine.py',
    'fast_complete_loader.py',
    'performance_optimizer.py',
    'real_movies_db_omdb.py',
    
    # Configuration
    'requirements.txt',
    '.gitignore',
    '.env.example',
    
    # Startup scripts
    'START_SYSTEM.bat',
    'start_local.bat',
    'run_local.py',
    
    # Documentation
    'README.md',
    'QUICK_START.md',
    'SYSTEM_READY.md',
    'GENRE_FILTERING_FIXED.md',
    'FINAL_SETUP.md',
    
    # Test files (useful for verification)
    'test_dataset.py',
    'test_ann_working.py',
}

# Directories to keep
KEEP_DIRS = {
    'models',
    'frontend',
    'processed',
    'data',
    'scripts',
    '.github',
    '.git',
}

# Files/directories to remove
REMOVE_PATTERNS = [
    # Old/duplicate test files
    'test_system.py',
    'test_fuzzy_system.py',
    'test_enhanced_system.py',
    'run_tests.py',
    
    # Old training scripts
    'train_production_ann.py',
    'process_complete_movielens_10m.py',
    
    # Trash directory
    '.trash',
    
    # Python cache
    '__pycache__',
    
    # Old documentation
    'README_LOCAL.md',
    
    # Processed full (if too large)
    # 'processed_full',
]

def cleanup():
    """Remove unnecessary files"""
    removed_count = 0
    
    print("🧹 Starting cleanup...")
    print("=" * 60)
    
    for pattern in REMOVE_PATTERNS:
        path = project_root / pattern
        
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"✅ Removed directory: {pattern}")
                else:
                    path.unlink()
                    print(f"✅ Removed file: {pattern}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {pattern}: {e}")
        else:
            print(f"⏭️  Skip (not found): {pattern}")
    
    print("=" * 60)
    print(f"✅ Cleanup complete! Removed {removed_count} items.")
    
    # Show remaining structure
    print("\n📁 Remaining project structure:")
    print("=" * 60)
    
    for item in sorted(project_root.iterdir()):
        if item.name.startswith('.') and item.name not in {'.gitignore', '.env.example', '.github'}:
            continue
        
        if item.is_dir():
            print(f"📂 {item.name}/")
        else:
            size_kb = item.stat().st_size / 1024
            print(f"📄 {item.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    cleanup()
    print("\n🎉 Project is clean and ready for GitHub!")

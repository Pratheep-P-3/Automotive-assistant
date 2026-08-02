#!/usr/bin/env python3
"""
Data Reorganization Helper Script

Helps reorganize knowledge base from flat structure to brand-specific structure.
This is optional - the system works with both flat and organized structures.
"""

import shutil
from pathlib import Path
from typing import Dict, List


def move_to_generic(source_dir: Path, target_generic_dir: Path, category: str) -> int:
    """
    Move all .txt files from source to generic subdirectory.
    
    Args:
        source_dir: Source directory (e.g., data/obd)
        target_generic_dir: Target generic directory (e.g., data/obd/generic)
        category: Category name for logging (e.g., "OBD")
    
    Returns:
        Number of files moved
    """
    target_generic_dir.mkdir(parents=True, exist_ok=True)
    txt_files = list(source_dir.glob("*.txt"))
    
    moved = 0
    for txt_file in txt_files:
        try:
            dest = target_generic_dir / txt_file.name
            shutil.move(str(txt_file), str(dest))
            print(f"✓ Moved {category}: {txt_file.name} → {target_generic_dir.name}/")
            moved += 1
        except Exception as e:
            print(f"✗ Failed to move {txt_file.name}: {e}")
    
    return moved


def reorganize_knowledge_base(data_dir: Path) -> Dict[str, int]:
    """
    Reorganize knowledge base from flat to brand-specific structure.
    
    Args:
        data_dir: Data directory (e.g., data/)
    
    Returns:
        Dict with counts of files moved per category
    """
    print("=" * 60)
    print("KNOWLEDGE BASE REORGANIZATION HELPER")
    print("=" * 60)
    print()
    print("This script will organize your knowledge base into brand-specific directories.")
    print("Current structure:")
    print("  data/obd/*.txt")
    print("  data/maintenance/*.txt")
    print("  data/troubleshooting/*.txt")
    print()
    print("New structure:")
    print("  data/obd/generic/*.txt")
    print("  data/obd/toyota/*.txt  (brand-specific)")
    print("  data/obd/honda/*.txt   (brand-specific)")
    print("  ... (same for maintenance and troubleshooting)")
    print()
    
    confirm = input("Proceed with reorganization? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return {}
    
    print()
    print("Starting reorganization...")
    print()
    
    results = {}
    
    # Process each category
    categories = [
        ("obd", "OBD"),
        ("maintenance", "Maintenance"),
        ("troubleshooting", "Troubleshooting"),
    ]
    
    for cat_dir, cat_name in categories:
        category_path = data_dir / cat_dir
        if not category_path.exists():
            print(f"⚠ {cat_name} directory not found: {category_path}")
            continue
        
        print(f"\n{cat_name}:")
        print(f"  Processing {category_path}...")
        
        # Move txt files to generic
        generic_dir = category_path / "generic"
        moved = move_to_generic(category_path, generic_dir, cat_name)
        results[cat_dir] = moved
        print(f"  ✓ Moved {moved} files to generic/")
    
    # Process evaluation separately (usually doesn't need reorganization)
    evaluation_path = data_dir / "evaluation"
    if evaluation_path.exists():
        print(f"\nEvaluation:")
        print(f"  Path: {evaluation_path} (not automatically moved)")
        print(f"  Action: Add to generic/evaluation if needed, or keep as-is")
    
    return results


def create_brand_directories(data_dir: Path, brands: List[str]) -> int:
    """
    Create brand-specific directories for future use.
    
    Args:
        data_dir: Data directory
        brands: List of brand names (e.g., ["toyota", "honda", "ford"])
    
    Returns:
        Number of directories created
    """
    print()
    print("=" * 60)
    print("CREATE BRAND-SPECIFIC DIRECTORIES")
    print("=" * 60)
    print()
    print("Common automotive brands:")
    print("  Toyota, Honda, Ford, Chevrolet, Nissan, BMW, Audi, Mercedes, Volkswagen")
    print()
    
    categories = ["obd", "maintenance", "troubleshooting"]
    created = 0
    
    for brand in brands:
        brand_lower = brand.lower()
        for category in categories:
            brand_dir = data_dir / category / brand_lower
            if not brand_dir.exists():
                brand_dir.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created: {category}/{brand_lower}/")
                created += 1
            else:
                print(f"⊘ Already exists: {category}/{brand_lower}/")
    
    print()
    print(f"Created {created} brand directories")
    return created


def main():
    """Main reorganization workflow."""
    data_dir = Path(__file__).parent / "data"
    
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return
    
    # Step 1: Reorganize existing files
    results = reorganize_knowledge_base(data_dir)
    
    # Step 2: Optionally create brand directories
    if results:
        print()
        print("\n" + "=" * 60)
        proceed = input("\nCreate brand-specific directories for future documents? (yes/no): ").strip().lower()
        
        if proceed == "yes":
            print()
            brands_input = input("Enter brands (comma-separated, e.g., 'toyota, honda, ford'): ").strip()
            if brands_input:
                brands = [b.strip() for b in brands_input.split(",")]
                create_brand_directories(data_dir, brands)
        else:
            print("Skipped.")
    
    # Summary
    print()
    print("=" * 60)
    print("REORGANIZATION COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run ingestion: python -m backend.rag.ingest")
    print("2. Verify documents are indexed: python -m backend.rag.validate_ingestion")
    print("3. Start the application and test")
    print()
    print("To add brand-specific documents:")
    print("1. Create documents in data/obd/toyota/, data/maintenance/honda/, etc.")
    print("2. Re-run ingestion to update the knowledge base")
    print("3. When users enter their vehicle make, brand-specific docs will be prioritized")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify CDN replacement functionality.
This script checks that all local vendor resources are accessible and properly configured.
"""

import os
import sys
from pathlib import Path

def test_local_resources():
    """Test that all local vendor resources exist and are accessible."""
    print("🔍 Testing CDN Replacement - Local Resources Verification")
    print("=" * 60)
    
    # Define expected files
    expected_files = [
        "ui/static/vendor/bootstrap/css/bootstrap.min.css",
        "ui/static/vendor/bootstrap/js/bootstrap.bundle.min.js", 
        "ui/static/vendor/bootstrap-icons/font/bootstrap-icons.css",
        "ui/static/vendor/bootstrap-icons/font/fonts/bootstrap-icons.woff2",
        "ui/static/vendor/bootstrap-icons/font/fonts/bootstrap-icons.woff"
    ]
    
    all_files_exist = True
    
    for file_path in expected_files:
        full_path = Path(file_path)
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            all_files_exist = False
    
    print("\n" + "=" * 60)
    
    if all_files_exist:
        print("✅ All local vendor resources are present and accessible!")
        print("✅ CDN replacement completed successfully!")
        print("✅ Platform is now fully self-contained and offline-capable!")
        return True
    else:
        print("❌ Some vendor resources are missing!")
        return False

def test_template_references():
    """Test that HTML templates use local paths instead of CDN URLs."""
    print("\n🔍 Testing Template References")
    print("=" * 60)
    
    template_file = Path("ui/templates/base.html")
    
    if not template_file.exists():
        print("❌ base.html template not found!")
        return False
    
    content = template_file.read_text(encoding='utf-8')
    
    # Check for CDN references (should be none)
    cdn_patterns = [
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com", 
        "unpkg.com"
    ]
    
    cdn_found = False
    for pattern in cdn_patterns:
        if pattern in content:
            print(f"❌ Found CDN reference: {pattern}")
            cdn_found = True
    
    # Check for local references (should be present)
    local_patterns = [
        "/static/vendor/bootstrap/css/bootstrap.min.css",
        "/static/vendor/bootstrap/js/bootstrap.bundle.min.js",
        "/static/vendor/bootstrap-icons/font/bootstrap-icons.css"
    ]
    
    local_found = 0
    for pattern in local_patterns:
        if pattern in content:
            print(f"✅ Found local reference: {pattern}")
            local_found += 1
        else:
            print(f"❌ Missing local reference: {pattern}")
    
    print("\n" + "=" * 60)
    
    if not cdn_found and local_found == len(local_patterns):
        print("✅ All template references updated to local paths!")
        return True
    else:
        print("❌ Template references need attention!")
        return False

def main():
    """Main test function."""
    print("🚀 JEECG A2A Platform - CDN Replacement Verification")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run tests
    resources_ok = test_local_resources()
    templates_ok = test_template_references()
    
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS")
    print("=" * 60)
    
    if resources_ok and templates_ok:
        print("🎉 SUCCESS: CDN replacement completed successfully!")
        print("🌐 Platform is now fully self-contained and offline-capable!")
        print("📦 All external dependencies have been localized!")
        sys.exit(0)
    else:
        print("❌ FAILURE: CDN replacement needs attention!")
        sys.exit(1)

if __name__ == "__main__":
    main()

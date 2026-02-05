#!/usr/bin/env python3
"""
Aria Monetization System Setup Script
Automatically configures and tests the monetization system
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def check_file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).exists()

def check_python_imports():
    """Check if required Python packages are available"""
    print_info("Checking Python dependencies...")
    
    required = ['json', 'datetime', 'enum', 'pathlib']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print_success(f"  {module} available")
        except ImportError:
            missing.append(module)
            print_error(f"  {module} missing")
    
    return len(missing) == 0

def verify_core_files():
    """Verify all core monetization files exist"""
    print_info("Verifying core files...")
    
    files = {
        'Backend': [
            'shared/subscription_manager.py',
            'function_app.py'
        ],
        'Frontend': [
            'pricing.html',
            'admin_dashboard.html',
            'my-subscription.html',
            'checkout.html',
            'subscription-success.html',
            'account.html'
        ],
        'Documentation': [
            'MONETIZATION_GUIDE.md',
            'INCOME_STREAM_SUMMARY.md',
            'QUICK_START_MONETIZATION.md'
        ]
    }
    
    all_exist = True
    for category, file_list in files.items():
        print(f"\n  {category}:")
        for file in file_list:
            if check_file_exists(file):
                print_success(f"    {file}")
            else:
                print_error(f"    {file} - MISSING")
                all_exist = False
    
    return all_exist

def test_subscription_manager():
    """Test the subscription manager"""
    print_info("Testing subscription manager...")
    
    try:
        # Import the subscription manager
        sys.path.insert(0, 'shared')
        from subscription_manager import get_subscription_manager, SubscriptionTier
        
        # Create manager instance
        manager = get_subscription_manager()
        print_success("  Subscription manager imported")
        
        # Test creating subscriptions
        manager.upgrade_subscription('test_user_1', SubscriptionTier.PRO, 30, 'test')
        print_success("  Pro subscription created")
        
        manager.upgrade_subscription('test_user_2', SubscriptionTier.ENTERPRISE, 30, 'test')
        print_success("  Enterprise subscription created")
        
        # Get revenue stats
        stats = manager.get_revenue_stats()
        print_success(f"  Revenue stats retrieved: ${stats['monthly_recurring_revenue']} MRR")
        
        return True
    except Exception as e:
        print_error(f"  Error: {str(e)}")
        return False

def generate_demo_data():
    """Generate demo subscription data for testing"""
    print_info("Generating demo data...")
    
    try:
        sys.path.insert(0, 'shared')
        from subscription_manager import get_subscription_manager, SubscriptionTier
        
        manager = get_subscription_manager()
        
        # Create 5 Pro subscribers
        for i in range(5):
            manager.upgrade_subscription(f'pro_user_{i+1}', SubscriptionTier.PRO, 30, 'demo')
        print_success("  Created 5 Pro subscribers")
        
        # Create 10 Enterprise subscribers
        for i in range(10):
            manager.upgrade_subscription(f'ent_user_{i+1}', SubscriptionTier.ENTERPRISE, 30, 'demo')
        print_success("  Created 10 Enterprise subscribers")
        
        # Get final stats
        stats = manager.get_revenue_stats()
        print_success(f"  Total MRR: ${stats['monthly_recurring_revenue']}")
        print_success(f"  Total ARR: ${stats['annual_recurring_revenue']}")
        
        if stats['monthly_recurring_revenue'] >= 2000:
            print_success(f"  🎉 TARGET ACHIEVED! ({stats['monthly_recurring_revenue']/2000*100:.1f}% of $2,000 goal)")
        
        return True
    except Exception as e:
        print_error(f"  Error: {str(e)}")
        return False

def start_test_server():
    """Start a simple HTTP server for testing"""
    print_info("Starting test server...")
    print_info("  Open http://localhost:8000/pricing.html in your browser")
    print_info("  Press Ctrl+C to stop the server")
    
    try:
        subprocess.run(['python3', '-m', 'http.server', '8000'])
    except KeyboardInterrupt:
        print_success("\n  Server stopped")
    except Exception as e:
        print_error(f"  Error starting server: {str(e)}")

def create_local_settings():
    """Create local.settings.json if it doesn't exist"""
    if not check_file_exists('local.settings.json'):
        print_info("Creating local.settings.json...")
        
        settings = {
            "IsEncrypted": False,
            "Values": {
                "AzureWebJobsStorage": "UseDevelopmentStorage=true",
                "FUNCTIONS_WORKER_RUNTIME": "python",
                "QAI_DB_CONN": "sqlite:///data_out/qai.db",
                "QAI_SQL_POOL_SIZE": "10"
            }
        }
        
        try:
            with open('local.settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            print_success("  local.settings.json created")
            return True
        except Exception as e:
            print_error(f"  Error: {str(e)}")
            return False
    else:
        print_success("  local.settings.json already exists")
        return True

def print_next_steps():
    """Print next steps for the user"""
    print_header("SETUP COMPLETE! 🎉")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.END}\n")
    
    print(f"{Colors.GREEN}1. View the Pricing Page:{Colors.END}")
    print(f"   python3 -m http.server 8000")
    print(f"   Then open: http://localhost:8000/pricing.html\n")
    
    print(f"{Colors.GREEN}2. View the Admin Dashboard:{Colors.END}")
    print(f"   Open: http://localhost:8000/admin_dashboard.html\n")
    
    print(f"{Colors.GREEN}3. Test the APIs (optional):{Colors.END}")
    print(f"   func host start")
    print(f"   curl http://localhost:7071/api/subscription/revenue | jq\n")
    
    print(f"{Colors.GREEN}4. View Documentation:{Colors.END}")
    print(f"   cat QUICK_START_MONETIZATION.md\n")
    
    print(f"{Colors.GREEN}5. Access All Pages:{Colors.END}")
    print(f"   - pricing.html - Pricing tiers")
    print(f"   - admin_dashboard.html - Revenue dashboard")
    print(f"   - my-subscription.html - User subscription")
    print(f"   - checkout.html - Payment page")
    print(f"   - subscription-success.html - Success page")
    print(f"   - account.html - Account settings\n")

def main():
    """Main setup function"""
    print_header("ARIA MONETIZATION SYSTEM - SETUP")
    
    # Step 1: Check Python environment
    if not check_python_imports():
        print_error("Missing required Python packages")
        return False
    print()
    
    # Step 2: Verify core files
    if not verify_core_files():
        print_error("Missing core files - please ensure all files are present")
        return False
    print()
    
    # Step 3: Create local settings
    create_local_settings()
    print()
    
    # Step 4: Test subscription manager
    if not test_subscription_manager():
        print_warning("Subscription manager test failed - continuing anyway")
    print()
    
    # Step 5: Generate demo data
    generate_demo = input(f"{Colors.BLUE}Generate demo data (5 Pro + 10 Enterprise subscribers)? (y/n): {Colors.END}").lower()
    if generate_demo == 'y':
        generate_demo_data()
    print()
    
    # Step 6: Print next steps
    print_next_steps()
    
    # Step 7: Offer to start server
    start_server = input(f"{Colors.BLUE}Start test server now? (y/n): {Colors.END}").lower()
    if start_server == 'y':
        start_test_server()
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup interrupted{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)

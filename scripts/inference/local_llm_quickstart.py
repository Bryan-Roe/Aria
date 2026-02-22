#!/usr/bin/env python3
"""
Aria Local LLM - Quick Start Menu
Simple menu to get started with local LLM options
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def print_header():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  ARIA LOCAL LLM - QUICK START".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝\n")

def menu():
    print("What would you like to do?\n")
    print("1. [S]  Setup LMStudio / LoRA (interactive wizard)")
    print("2. [T]  Test provider setup (validate config)")
    print("3. [I]  Run local inference (quick test)")
    print("4. [C]  Chat with local provider (interactive)")
    print("5. [D]  View documentation")
    print("6. [Q]  Quit")
    print()

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n>>> {description}\n")
    try:
        result = subprocess.run(cmd, shell=True, cwd=str(PROJECT_ROOT))
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    os.chdir(PROJECT_ROOT)
    
    while True:
        print_header()
        menu()
        
        choice = input("Enter choice (S/T/I/C/D/Q): ").strip().upper()
        
        if choice == "S":
            run_command(
                f"{sys.executable} scripts/setup_local_llm.py",
                "Running Setup Wizard..."
            )
        
        elif choice == "T":
            run_command(
                f"{sys.executable} scripts/test_local_llm.py",
                "Running Provider Tests..."
            )
        
        elif choice == "I":
            run_command(
                f"{sys.executable} scripts/local_inference.py",
                "Running Local Inference..."
            )
        
        elif choice == "C":
            print("\nStarting local chat (Ctrl+C to quit)\n")
            run_command(
                f"{sys.executable} src/chat/chat_cli.py --provider local",
                "Local Chat"
            )
        
        elif choice == "D":
            print("\n📖 Documentation Files:\n")
            print("1. [Q]  Quick Reference: LOCAL_LLM_QUICKREF.md")
            print("2. [F]  Full Guide: LOCAL_LLM_SETUP.md")
            print("3. [B]  Back to main menu")
            print()
            doc_choice = input("Choose (Q/F/B): ").strip().upper()
            
            if doc_choice == "Q":
                file = PROJECT_ROOT / "LOCAL_LLM_QUICKREF.md"
            elif doc_choice == "F":
                file = PROJECT_ROOT / "LOCAL_LLM_SETUP.md"
            else:
                continue
            
            if file.exists():
                print(f"\n{'='*70}\n")
                with open(file) as f:
                    content = f.read()
                    # Show first 100 lines
                    lines = content.split('\n')[:100]
                    print('\n'.join(lines))
                print(f"\n... (see {file.name} for full content)\n")
                print(f"{'='*70}\n")
                input("Press Enter to continue...")
        
        elif choice == "Q":
            print("\nGoodbye! 👋\n")
            break
        
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye! 👋\n")
        sys.exit(0)

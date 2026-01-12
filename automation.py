#!/usr/bin/env python3
"""
Small Automation System
-----------------------
A reliable automation system that validates input files, generates summaries,
and produces detailed logs with safe failure handling.

Author: Automation System
Date: 2026-01-12
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


# ANSI color codes for console output
class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class Logger:
    """Simple logger that writes to both console and file"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.logs = []
    
    def log(self, level: str, message: str, console_only: bool = False):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Color code based on level
        if level == "INFO":
            color = Colors.BLUE
        elif level == "SUCCESS":
            color = Colors.GREEN
        elif level == "WARNING":
            color = Colors.YELLOW
        elif level == "ERROR":
            color = Colors.RED
        else:
            color = ""
        
        # Print to console with color
        print(f"{color}{log_entry}{Colors.END}")
        
        # Store for file writing (unless console only)
        if not console_only:
            self.logs.append(log_entry)
    
    def save(self):
        """Save all logs to file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.logs))
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to save log file: {e}{Colors.END}")
            return False


class AutomationSystem:
    """Main automation system class"""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.txt', '.csv', '.json'}
    
    def __init__(self, input_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = None
        self.logger = None
        self.file_stats = {
            'total_files': 0,
            'total_size': 0,
            'total_lines': 0,
            'by_extension': {},
            'valid_files': [],
            'empty_files': [],
            'unreadable_files': []
        }
    
    def validate_folder(self) -> bool:
        """Validate that input folder exists and is accessible"""
        if not self.input_folder.exists():
            print(f"{Colors.RED}{Colors.BOLD}ERROR:{Colors.END} Input folder does not exist: {self.input_folder}")
            return False
        
        if not self.input_folder.is_dir():
            print(f"{Colors.RED}{Colors.BOLD}ERROR:{Colors.END} Path is not a directory: {self.input_folder}")
            return False
        
        if not os.access(self.input_folder, os.R_OK):
            print(f"{Colors.RED}{Colors.BOLD}ERROR:{Colors.END} No read permission for folder: {self.input_folder}")
            return False
        
        return True
    
    def validate_files(self) -> bool:
        """Validate files in the input folder"""
        self.logger.log("INFO", f"Scanning input folder: {self.input_folder}")
        
        try:
            all_files = [f for f in self.input_folder.iterdir() if f.is_file()]
            
            if not all_files:
                self.logger.log("ERROR", "Input folder is empty - no files found")
                return False
            
            self.logger.log("INFO", f"Found {len(all_files)} file(s) in input folder")
            
            # Filter for supported extensions
            supported_files = [f for f in all_files if f.suffix.lower() in self.SUPPORTED_EXTENSIONS]
            
            if not supported_files:
                self.logger.log("ERROR", 
                    f"No valid files found. Supported extensions: {', '.join(self.SUPPORTED_EXTENSIONS)}")
                return False
            
            # Validate each file
            for file_path in supported_files:
                self._process_file(file_path)
            
            # Check if we have at least one valid file
            if not self.file_stats['valid_files']:
                self.logger.log("ERROR", "No valid files found (all files are empty or unreadable)")
                return False
            
            # Log warnings for problematic files
            if self.file_stats['empty_files']:
                self.logger.log("WARNING", 
                    f"Found {len(self.file_stats['empty_files'])} empty file(s): " +
                    ', '.join([f.name for f in self.file_stats['empty_files']]))
            
            if self.file_stats['unreadable_files']:
                self.logger.log("WARNING", 
                    f"Found {len(self.file_stats['unreadable_files'])} unreadable file(s): " +
                    ', '.join([f.name for f in self.file_stats['unreadable_files']]))
            
            self.logger.log("SUCCESS", 
                f"Validation passed: {len(self.file_stats['valid_files'])} valid file(s) found")
            return True
            
        except PermissionError as e:
            self.logger.log("ERROR", f"Permission denied while scanning folder: {e}")
            return False
        except Exception as e:
            self.logger.log("ERROR", f"Unexpected error during file validation: {e}")
            return False
    
    def _process_file(self, file_path: Path):
        """Process a single file and collect statistics"""
        try:
            # Check if file is empty
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.file_stats['empty_files'].append(file_path)
                return
            
            # Try to read file and count lines
            line_count = 0
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        line_count = sum(1 for _ in f)
                except:
                    self.file_stats['unreadable_files'].append(file_path)
                    return
            except Exception:
                self.file_stats['unreadable_files'].append(file_path)
                return
            
            # File is valid - update statistics
            self.file_stats['valid_files'].append({
                'path': file_path,
                'name': file_path.name,
                'size': file_size,
                'lines': line_count,
                'extension': file_path.suffix.lower()
            })
            
            self.file_stats['total_files'] += 1
            self.file_stats['total_size'] += file_size
            self.file_stats['total_lines'] += line_count
            
            # Track by extension
            ext = file_path.suffix.lower()
            if ext not in self.file_stats['by_extension']:
                self.file_stats['by_extension'][ext] = {'count': 0, 'size': 0, 'lines': 0}
            
            self.file_stats['by_extension'][ext]['count'] += 1
            self.file_stats['by_extension'][ext]['size'] += file_size
            self.file_stats['by_extension'][ext]['lines'] += line_count
            
        except Exception as e:
            self.logger.log("WARNING", f"Error processing {file_path.name}: {e}")
            self.file_stats['unreadable_files'].append(file_path)
    
    def create_output_folder(self) -> bool:
        """Create timestamped output folder"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_folder = self.input_folder.parent / f"output_{timestamp}"
            self.output_folder.mkdir(exist_ok=True)
            
            self.logger.log("INFO", f"Created output folder: {self.output_folder}")
            return True
        except Exception as e:
            self.logger.log("ERROR", f"Failed to create output folder: {e}")
            return False
    
    def generate_summary(self) -> bool:
        """Generate summary file with statistics"""
        try:
            summary_path = self.output_folder / "summary.txt"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("AUTOMATION SYSTEM - SUMMARY REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Input Folder: {self.input_folder.absolute()}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("OVERALL STATISTICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total Valid Files: {self.file_stats['total_files']}\n")
                f.write(f"Total Size: {self._format_size(self.file_stats['total_size'])}\n")
                f.write(f"Total Lines: {self.file_stats['total_lines']:,}\n\n")
                
                if self.file_stats['by_extension']:
                    f.write("-" * 80 + "\n")
                    f.write("STATISTICS BY FILE TYPE\n")
                    f.write("-" * 80 + "\n")
                    for ext, stats in sorted(self.file_stats['by_extension'].items()):
                        f.write(f"\n{ext.upper()} Files:\n")
                        f.write(f"  Count: {stats['count']}\n")
                        f.write(f"  Total Size: {self._format_size(stats['size'])}\n")
                        f.write(f"  Total Lines: {stats['lines']:,}\n")
                
                f.write("\n" + "-" * 80 + "\n")
                f.write("FILE DETAILS\n")
                f.write("-" * 80 + "\n")
                for file_info in sorted(self.file_stats['valid_files'], key=lambda x: x['name']):
                    f.write(f"\n{file_info['name']}\n")
                    f.write(f"  Size: {self._format_size(file_info['size'])}\n")
                    f.write(f"  Lines: {file_info['lines']:,}\n")
                    f.write(f"  Type: {file_info['extension']}\n")
                
                if self.file_stats['empty_files'] or self.file_stats['unreadable_files']:
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("WARNINGS\n")
                    f.write("-" * 80 + "\n")
                    
                    if self.file_stats['empty_files']:
                        f.write(f"\nEmpty Files ({len(self.file_stats['empty_files'])}):\n")
                        for fp in self.file_stats['empty_files']:
                            f.write(f"  - {fp.name}\n")
                    
                    if self.file_stats['unreadable_files']:
                        f.write(f"\nUnreadable Files ({len(self.file_stats['unreadable_files'])}):\n")
                        for fp in self.file_stats['unreadable_files']:
                            f.write(f"  - {fp.name}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            self.logger.log("SUCCESS", f"Summary generated: {summary_path.name}")
            return True
            
        except Exception as e:
            self.logger.log("ERROR", f"Failed to generate summary: {e}")
            return False
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def run(self) -> int:
        """Main execution flow"""
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"{Colors.BOLD}AUTOMATION SYSTEM - Starting{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")
        
        # Step 1: Validate folder
        if not self.validate_folder():
            return 1
        
        # Step 2: Create output folder and initialize logger
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_output = self.input_folder.parent / f"output_{timestamp}"
        
        try:
            temp_output.mkdir(exist_ok=True)
            self.output_folder = temp_output
            log_path = self.output_folder / "automation.log"
            self.logger = Logger(log_path)
        except Exception as e:
            print(f"{Colors.RED}{Colors.BOLD}ERROR:{Colors.END} Failed to create output folder: {e}")
            return 2
        
        self.logger.log("INFO", "Automation system started")
        self.logger.log("INFO", f"Input folder: {self.input_folder.absolute()}")
        self.logger.log("INFO", f"Output folder: {self.output_folder.absolute()}")
        
        # Step 3: Validate files
        if not self.validate_files():
            self.logger.log("ERROR", "Validation failed - exiting")
            self.logger.save()
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED:{Colors.END} Validation errors occurred. Check log for details.\n")
            return 1
        
        # Step 4: Generate summary
        if not self.generate_summary():
            self.logger.log("ERROR", "Failed to generate summary")
            self.logger.save()
            return 2
        
        # Step 5: Save log
        self.logger.log("INFO", "Saving log file")
        if not self.logger.save():
            return 2
        
        # Success
        self.logger.log("SUCCESS", "Automation completed successfully", console_only=True)
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}SUCCESS:{Colors.END} Automation completed successfully!")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"\nOutput location: {Colors.BLUE}{self.output_folder.absolute()}{Colors.END}")
        print(f"  - summary.txt")
        print(f"  - automation.log\n")
        
        return 0


def main():
    """Entry point for the automation system"""
    if len(sys.argv) != 2:
        print(f"{Colors.RED}{Colors.BOLD}Usage:{Colors.END} python automation.py <input_folder>")
        print(f"\nExample: python automation.py example_input")
        return 1
    
    input_folder = sys.argv[1]
    
    try:
        automation = AutomationSystem(input_folder)
        exit_code = automation.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user{Colors.END}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}FATAL ERROR:{Colors.END} {e}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()

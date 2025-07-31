#!/usr/bin/env python3
"""
Log Report Generator for Okta User Creator
Generates daily/weekly reports for management review.
"""

import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
import glob

def parse_log_file(log_file_path):
    """Parse a single log file and extract key metrics."""
    stats = {
        'date': None,
        'successful_creations': 0,
        'duplicates': 0,
        'errors': 0,
        'total_processed': 0,
        'users_created': [],
        'error_details': [],
        'runtime_duration': None
    }
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract date from filename
        filename = os.path.basename(log_file_path)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            stats['date'] = date_match.group(1)
        
        # Count successes
        success_matches = re.findall(r' SUCCESS: Created Okta user (\S+) \(Ticket #(\d+)\)', content)
        stats['successful_creations'] = len(success_matches)
        stats['users_created'] = [(email, ticket) for email, ticket in success_matches]
        
        # Count duplicates
        duplicate_matches = re.findall(r' DUPLICATE: User (\S+) already exists', content)
        stats['duplicates'] = len(duplicate_matches)
        
        # Count errors
        error_matches = re.findall(r' (?:FAILED|NETWORK ERROR|UNEXPECTED ERROR): (.+)', content)
        stats['errors'] = len(error_matches)
        stats['error_details'] = error_matches
        
        # Extract runtime duration
        duration_match = re.search(r' Duration: (.+)', content)
        if duration_match:
            stats['runtime_duration'] = duration_match.group(1)
        
        # Total processed
        processed_match = re.search(r' Total users processed: (\d+)', content)
        if processed_match:
            stats['total_processed'] = int(processed_match.group(1))
            
    except Exception as e:
        print(f"Error parsing {log_file_path}: {e}")
    
    return stats

def generate_daily_report(date_str=None):
    """Generate a daily report for a specific date (defaults to today)."""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    log_file = os.path.join(log_dir, f'okta_automation_{date_str}.log')
    
    if not os.path.exists(log_file):
        return f"No log file found for {date_str}"
    
    stats = parse_log_file(log_file)
    
    report = f"""
 OKTA AUTOMATION DAILY REPORT - {date_str}
{'=' * 50}

 SUMMARY STATISTICS:
   Users Successfully Created: {stats['successful_creations']}
   Duplicate Users Skipped: {stats['duplicates']}
   Errors Encountered: {stats['errors']}
   Total Users Processed: {stats['total_processed']}
   Runtime Duration: {stats['runtime_duration'] or 'N/A'}

"""
    
    if stats['users_created']:
        report += " USERS CREATED:\n"
        for email, ticket in stats['users_created']:
            report += f"  • {email} (Ticket #{ticket})\n"
        report += "\n"
    
    if stats['error_details']:
        report += " ERROR DETAILS:\n"
        for error in stats['error_details'][:5]:  # Show first 5 errors
            report += f"  • {error}\n"
        if len(stats['error_details']) > 5:
            report += f"  ... and {len(stats['error_details']) - 5} more errors\n"
        report += "\n"
    
    report += f"""
 SUCCESS RATE: {(stats['successful_creations'] / max(stats['total_processed'], 1) * 100):.1f}%

 STATUS: {' HEALTHY' if stats['errors'] == 0 else ' ATTENTION NEEDED' if stats['errors'] < 3 else ' CRITICAL'}
"""
    
    return report

def generate_monthly_report(year=None, month=None):
    """Generate a comprehensive monthly report."""
    if not year or not month:
        now = datetime.now()
        year = now.year
        month = now.month
    
    month_name = datetime(year, month, 1).strftime('%B')
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    if not os.path.exists(log_dir):
        return "No logs directory found"
    
    # Get all days in the month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    current_date = datetime(year, month, 1)
    monthly_stats = {
        'total_users_created': 0,
        'total_duplicates': 0,
        'total_errors': 0,
        'days_with_activity': 0,
        'daily_breakdown': [],
        'all_users_created': [],
        'error_summary': defaultdict(int),
        'weekly_totals': [0, 0, 0, 0, 0],  # Up to 5 weeks
        'busiest_day': {'date': None, 'count': 0},
        'error_days': []
    }
    
    # Process each day of the month
    while current_date < next_month:
        date_str = current_date.strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'okta_automation_{date_str}.log')
        
        if os.path.exists(log_file):
            stats = parse_log_file(log_file)
            monthly_stats['total_users_created'] += stats['successful_creations']
            monthly_stats['total_duplicates'] += stats['duplicates']
            monthly_stats['total_errors'] += stats['errors']
            
            if stats['successful_creations'] > 0 or stats['errors'] > 0:
                monthly_stats['days_with_activity'] += 1
            
            # Track daily breakdown
            day_data = {
                'date': date_str,
                'day_name': current_date.strftime('%A'),
                'created': stats['successful_creations'],
                'duplicates': stats['duplicates'],
                'errors': stats['errors']
            }
            monthly_stats['daily_breakdown'].append(day_data)
            
            # Track busiest day
            if stats['successful_creations'] > monthly_stats['busiest_day']['count']:
                monthly_stats['busiest_day'] = {
                    'date': date_str,
                    'count': stats['successful_creations']
                }
            
            # Track error days
            if stats['errors'] > 0:
                monthly_stats['error_days'].append({
                    'date': date_str,
                    'errors': stats['errors'],
                    'details': stats['error_details'][:3]  # First 3 errors
                })
            
            # Add to weekly totals (week of month)
            week_of_month = (current_date.day - 1) // 7
            if week_of_month < 5:
                monthly_stats['weekly_totals'][week_of_month] += stats['successful_creations']
            
            # Collect all created users
            monthly_stats['all_users_created'].extend(stats['users_created'])
            
            # Categorize errors
            for error in stats['error_details']:
                if 'NETWORK ERROR' in error:
                    monthly_stats['error_summary']['Network Issues'] += 1
                elif 'DUPLICATE' in error:
                    monthly_stats['error_summary']['Duplicates'] += 1
                elif 'FAILED' in error:
                    monthly_stats['error_summary']['Creation Failures'] += 1
                else:
                    monthly_stats['error_summary']['Other Errors'] += 1
        
        current_date += timedelta(days=1)
    
    # Calculate working days (Mon-Fri)
    working_days = sum(1 for day in monthly_stats['daily_breakdown'] 
                      if day['day_name'] not in ['Saturday', 'Sunday'])
    
    # Generate comprehensive report
    report = f"""
 OKTA AUTOMATION MONTHLY REPORT
{month_name} {year}
{'=' * 70}

 EXECUTIVE SUMMARY:
   Total Users Created: {monthly_stats['total_users_created']}
   Duplicate Attempts: {monthly_stats['total_duplicates']}
   Total Errors: {monthly_stats['total_errors']}
  📅 Active Days: {monthly_stats['days_with_activity']}/{len(monthly_stats['daily_breakdown'])} days
  � Working Days: {working_days}
  
 PERFORMANCE METRICS:
   Daily Average: {monthly_stats['total_users_created'] / max(len(monthly_stats['daily_breakdown']), 1):.1f} users/day
   Working Day Average: {monthly_stats['total_users_created'] / max(working_days, 1):.1f} users/working day
   Success Rate: {(monthly_stats['total_users_created'] / max(monthly_stats['total_users_created'] + monthly_stats['total_errors'], 1) * 100):.1f}%
  ⚡ System Reliability: {((monthly_stats['days_with_activity'] - len(monthly_stats['error_days'])) / max(monthly_stats['days_with_activity'], 1) * 100):.1f}%

"""
    
    if monthly_stats['busiest_day']['date']:
        busiest_date = datetime.strptime(monthly_stats['busiest_day']['date'], '%Y-%m-%d')
        report += f" BUSIEST DAY: {busiest_date.strftime('%B %d, %Y')} ({monthly_stats['busiest_day']['count']} users)\n\n"
    
    # Weekly breakdown
    report += "📅 WEEKLY BREAKDOWN:\n"
    for i, week_total in enumerate(monthly_stats['weekly_totals']):
        if week_total > 0:
            report += f"  Week {i+1}: {week_total} users created\n"
    report += "\n"
    
    # Error analysis
    if monthly_stats['error_summary']:
        report += " ERROR ANALYSIS:\n"
        for error_type, count in monthly_stats['error_summary'].items():
            report += f"  • {error_type}: {count}\n"
        report += "\n"
    
    # Recent users created (last 15)
    if monthly_stats['all_users_created']:
        report += f" RECENT USERS CREATED ({len(monthly_stats['all_users_created'])} total):\n"
        recent_users = monthly_stats['all_users_created'][-15:]
        for email, ticket in recent_users:
            report += f"  • {email} (Ticket #{ticket})\n"
        if len(monthly_stats['all_users_created']) > 15:
            report += f"  ... and {len(monthly_stats['all_users_created']) - 15} more users\n"
        report += "\n"
    
    # Days with issues
    if monthly_stats['error_days']:
        report += f" DAYS WITH ISSUES ({len(monthly_stats['error_days'])} days):\n"
        for error_day in monthly_stats['error_days'][-5:]:  # Show last 5 error days
            error_date = datetime.strptime(error_day['date'], '%Y-%m-%d')
            report += f"  • {error_date.strftime('%b %d')}: {error_day['errors']} errors\n"
            for detail in error_day['details']:
                report += f"    - {detail[:80]}...\n"
        report += "\n"
    
    # Overall status assessment
    if monthly_stats['total_errors'] == 0:
        status = "🌟 EXCELLENT - No errors detected"
    elif monthly_stats['total_errors'] <= monthly_stats['total_users_created'] * 0.05:  # Less than 5% error rate
        status = " GOOD - Low error rate"
    elif monthly_stats['total_errors'] <= monthly_stats['total_users_created'] * 0.15:  # Less than 15% error rate
        status = " FAIR - Moderate error rate, monitor closely"
    else:
        status = " NEEDS ATTENTION - High error rate detected"
    
    report += f"""
 MONTHLY ASSESSMENT:
  Status: {status}
  Trend: {' Growing' if monthly_stats['total_users_created'] > 20 else ' Steady' if monthly_stats['total_users_created'] > 5 else ' Low Activity'}
  Recommendation: {'Continue current operation' if monthly_stats['total_errors'] <= 3 else 'Review error patterns and consider system improvements'}

 ACTION ITEMS:
  • {' No action required' if monthly_stats['total_errors'] == 0 else ' Investigate recurring error patterns'}
  • {' Performance is optimal' if monthly_stats['total_users_created'] / max(working_days, 1) >= 1 else ' Consider process optimization for higher throughput'}
  •  Schedule next month's review
"""
    
    return report

def generate_year_to_date_summary():
    """Generate a year-to-date summary for annual reviews."""
    current_year = datetime.now().year
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    if not os.path.exists(log_dir):
        return "No logs directory found"
    
    ytd_stats = {
        'total_users_created': 0,
        'total_errors': 0,
        'monthly_breakdown': [],
        'busiest_month': {'month': None, 'count': 0}
    }
    
    # Process each month of the current year
    for month in range(1, datetime.now().month + 1):
        month_start = datetime(current_year, month, 1)
        if month == 12:
            month_end = datetime(current_year + 1, 1, 1)
        else:
            month_end = datetime(current_year, month + 1, 1)
        
        month_users = 0
        month_errors = 0
        
        current_date = month_start
        while current_date < month_end:
            date_str = current_date.strftime('%Y-%m-%d')
            log_file = os.path.join(log_dir, f'okta_automation_{date_str}.log')
            
            if os.path.exists(log_file):
                stats = parse_log_file(log_file)
                month_users += stats['successful_creations']
                month_errors += stats['errors']
            
            current_date += timedelta(days=1)
        
        month_name = month_start.strftime('%B')
        ytd_stats['monthly_breakdown'].append({
            'month': month_name,
            'users': month_users,
            'errors': month_errors
        })
        
        ytd_stats['total_users_created'] += month_users
        ytd_stats['total_errors'] += month_errors
        
        if month_users > ytd_stats['busiest_month']['count']:
            ytd_stats['busiest_month'] = {
                'month': month_name,
                'count': month_users
            }
    
    report = f"""
 YEAR-TO-DATE SUMMARY - {current_year}
{'=' * 50}

 ANNUAL TOTALS:
   Total Users Created: {ytd_stats['total_users_created']}
   Total Errors: {ytd_stats['total_errors']}
   Busiest Month: {ytd_stats['busiest_month']['month']} ({ytd_stats['busiest_month']['count']} users)
   Monthly Average: {ytd_stats['total_users_created'] / max(len(ytd_stats['monthly_breakdown']), 1):.1f} users

📅 MONTHLY BREAKDOWN:
"""
    
    for month_data in ytd_stats['monthly_breakdown']:
        report += f"  {month_data['month']}: {month_data['users']} users, {month_data['errors']} errors\n"
    
    return report

def generate_weekly_report():
    """Generate a weekly summary report."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    if not os.path.exists(log_dir):
        return "No logs directory found"
    
    # Get last 7 days of logs
    end_date = datetime.now()
    weekly_stats = {
        'total_users_created': 0,
        'total_duplicates': 0,
        'total_errors': 0,
        'daily_breakdown': [],
        'all_users_created': []
    }
    
    for i in range(7):
        date = end_date - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'okta_automation_{date_str}.log')
        
        if os.path.exists(log_file):
            stats = parse_log_file(log_file)
            weekly_stats['total_users_created'] += stats['successful_creations']
            weekly_stats['total_duplicates'] += stats['duplicates']
            weekly_stats['total_errors'] += stats['errors']
            weekly_stats['daily_breakdown'].append({
                'date': date_str,
                'created': stats['successful_creations'],
                'errors': stats['errors']
            })
            weekly_stats['all_users_created'].extend(stats['users_created'])
    
    # Generate report
    start_date = (end_date - timedelta(days=6)).strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    report = f"""
 OKTA AUTOMATION WEEKLY REPORT
{start_date} to {end_date_str}
{'=' * 60}

 WEEKLY SUMMARY:
   Total Users Created: {weekly_stats['total_users_created']}
   Total Duplicates: {weekly_stats['total_duplicates']}
   Total Errors: {weekly_stats['total_errors']}
  📅 Days with Activity: {len(weekly_stats['daily_breakdown'])}

📅 DAILY BREAKDOWN:
"""
    
    for day in reversed(weekly_stats['daily_breakdown']):
        status_icon = "" if day['errors'] == 0 else "" if day['errors'] < 3 else ""
        report += f"  {day['date']}: {day['created']} created, {day['errors']} errors {status_icon}\n"
    
    if weekly_stats['all_users_created']:
        report += f"\n ALL USERS CREATED THIS WEEK ({len(weekly_stats['all_users_created'])}):\n"
        for email, ticket in weekly_stats['all_users_created'][-10:]:  # Show last 10
            report += f"  • {email} (Ticket #{ticket})\n"
        if len(weekly_stats['all_users_created']) > 10:
            report += f"  ... and {len(weekly_stats['all_users_created']) - 10} more users\n"
    
    avg_daily = weekly_stats['total_users_created'] / 7
    report += f"""
 PERFORMANCE METRICS:
   Average users/day: {avg_daily:.1f}
   Success rate: {((weekly_stats['total_users_created'] + weekly_stats['total_duplicates']) / max(weekly_stats['total_users_created'] + weekly_stats['total_duplicates'] + weekly_stats['total_errors'], 1) * 100):.1f}%
  ⚡ Automation health: {' EXCELLENT' if weekly_stats['total_errors'] == 0 else ' GOOD' if weekly_stats['total_errors'] < 5 else ' NEEDS ATTENTION'}
"""
    
    return report

def main():
    """Generate and display reports."""
    print("Okta Automation Log Report Generator")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Daily Report (today)")
        print("2. Daily Report (specific date)")
        print("3. Weekly Report (last 7 days)")
        print("4. Monthly Report (current month)")
        print("5. Monthly Report (specific month)")
        print("6. Year-to-Date Summary")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            print(generate_daily_report())
        elif choice == "2":
            date = input("Enter date (YYYY-MM-DD): ").strip()
            print(generate_daily_report(date))
        elif choice == "3":
            print(generate_weekly_report())
        elif choice == "4":
            print(generate_monthly_report())
        elif choice == "5":
            year = int(input("Enter year (YYYY): ").strip())
            month = int(input("Enter month (1-12): ").strip())
            print(generate_monthly_report(year, month))
        elif choice == "6":
            print(generate_year_to_date_summary())
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

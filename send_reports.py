#!/usr/bin/env python3
"""
Automated Report Sender for Okta User Creator
Sends daily/weekly/monthly reports to Slack channel automatically.
"""

import sys
from datetime import datetime, timedelta
from log_reporter import send_daily_report_to_slack, send_weekly_report_to_slack, send_monthly_report_to_slack

def send_daily_report():
    """Send today's daily report to Slack."""
    print("Sending daily report to Slack...")
    success = send_daily_report_to_slack()
    if success:
        print("Daily report sent successfully!")
    else:
        print("Failed to send daily report.")
    return success

def send_weekly_report():
    """Send weekly report to Slack."""
    print("Sending weekly report to Slack...")
    success = send_weekly_report_to_slack()
    if success:
        print("Weekly report sent successfully!")
    else:
        print("Failed to send weekly report.")
    return success

def send_monthly_report():
    """Send monthly report to Slack."""
    print("Sending monthly report to Slack...")
    success = send_monthly_report_to_slack()
    if success:
        print("Monthly report sent successfully!")
    else:
        print("Failed to send monthly report.")
    return success

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python send_reports.py [daily|weekly|monthly]")
        print("Examples:")
        print("  python send_reports.py daily    # Send today's daily report")
        print("  python send_reports.py weekly   # Send weekly summary")
        print("  python send_reports.py monthly  # Send monthly report")
        sys.exit(1)
    
    report_type = sys.argv[1].lower()
    
    if report_type == "daily":
        send_daily_report()
    elif report_type == "weekly":
        send_weekly_report()
    elif report_type == "monthly":
        send_monthly_report()
    else:
        print(f"Unknown report type: {report_type}")
        print("Valid options: daily, weekly, monthly")
        sys.exit(1)

if __name__ == "__main__":
    main()

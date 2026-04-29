from basketball_reference_web_scraper import client
import inspect

# List all available methods in client
print("Available client methods:")
for name in dir(client):
    if not name.startswith('_'):
        print(f"  - {name}")

# Check if team_schedule_for_month exists
if hasattr(client, 'team_schedule_for_month'):
    print("\n✓ team_schedule_for_month EXISTS")
else:
    print("\n✗ team_schedule_for_month DOES NOT EXIST")
# Okta User Creator

This tool automates the creation of new user accounts in Okta based on ticket information. It helps streamline the onboarding process by automatically creating Okta accounts with the correct user information.

## Features

- Automatically extracts user information from tickets
- Creates Okta user accounts with proper naming conventions
- Handles email generation based on user's name
- Includes safety features like test mode
- Provides clear feedback on creation status

## Setup

1. Clone this repository:
```bash
git clone https://gitlab.com/filevine/it-security/projects/user-create-automation.git
cd user-create-automation
```

2. Create a `config.py` file with your Okta credentials:
```python
OKTA_API_TOKEN = "your-api-token"
OKTA_ORG_URL = "your-okta-org-url"
```

3. Install required Python packages:
```bash
pip install requests
```

## Usage

1. Run in test mode (processes only the first user):
```bash
python okta_batch_create.py
```

2. Run for all users (after validating test mode works):
   - Open `okta_batch_create.py`
   - Change `test_mode=True` to `test_mode=False` at the bottom of the file
   - Run the script again

## Output Meanings

- ✅ Created: User was successfully created in Okta
- ⚠️ Already exists: User account already exists or has invalid data
- ❌ Failed: Creation failed (error details will be shown)

## Security Notes

- The `config.py` file is excluded from Git to protect sensitive credentials
- Always run in test mode first to validate changes
- Keep your Okta API token secure

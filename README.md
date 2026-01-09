# Travel Ticket Calendar v2

A program that automatically adds your flight/train/bus ticket as an event to your Google Calendar:

-   Runs in the background watching a folder.
-   When a ticket PDF is added to the folder the program scans it and uploads it to your Google Calendar

# Set up

## 1. Clone the repo

```bash
git clone https://github.com/MasterMynk/Travel-Ticket-Calendar-2.git
```

## 2. Install dependencies

```bash
cd Travel-Ticket-Calendar-2/
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## 3. Identify Required APIs/Credentials

1. **Google APIs**
    1. **Calendar API:** Used to create events on the calendar. Also used for checking if the event is already present
    2. **Drive API:** Used to upload the ticket pdf to the drive to attach it to the calendar event
2. **Google AI Studio:** Used to parse any ticket other than an IRCTC ticket
3. **RailRadar API:** Used to get train info from the train number when working with IRCTC tickets; Required for parsing IRCTC tickets

## 4. Google Cloud Console Setup for Calendar and Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. **Create a new project:**

    1. Click on `Select a project` or `<name of your previous project>` in the top left corner.
       ![Screenshot](readme_assets/select_a_project.jpg)
    2. In the modal window that opens click `New Project`
       ![Screenshot](readme_assets/new_project_modal.jpg)
    3. Give your project a name in the screen that shows up next
    4. Click `CREATE` and you're done
       ![Screenshot](readme_assets/create_project.jpg)
    5. Ensure that the project is selected and the name appears in the top left corner for the rest of the steps.
       ![Screenshot visually showing the indicator of the created project being selected](readme_assets/project_selected.jpg)

3. **Enable Google Calendar API:**

    1. In the search bar search for `calendar api`, click on the [first option](https://console.cloud.google.com/flows/enableapi?apiid=calendar-json.googleapis.com)
       ![Screenshot](readme_assets/google_calendar_api.jpg)
    2. Then on `Enable` to enable the API
       ![Screenshot](readme_assets/enable_calendar_api.jpg)

4. **Enable Google Drive API:**

    1. Go back and search for `google drive api`, click on the [first option](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com)
    2. Now click on `Enable` to enable it.
       ![Screenshot](readme_assets/enable_google_drive.jpg)

5. **Setup OAuth consent screen:**

    1. Go back and search for `OAuth consent screen` and on the [first option](https://console.cloud.google.com/apis/credentials/consent)
    2. Click on `Get Started`
       ![Screenshot](readme_assets/oauth_get_started.jpg)
    3. Enter any App Name and select your email address and then click `Next`
       ![Screenshot](readme_assets/app_info.jpg)
    4. Select `Audience` as External and click `Next`
       ![Screenshot](readme_assets/audience.jpg)
    5. Finish steps 3 and 4 and then click `Create`
       ![Screenshot](readme_assets/create.jpg)
    6. Now add an OAuth Client
       ![Screenshot](readme_assets/create_oauth_client.jpg)
    7. In the following screen choose `Desktop app` as the `Application type` and give it a name that you like
    8. Then click on `Create`
       ![Screenshot](readme_assets/desktop_app.jpg)
    9. In the modal window that pops up click on `Download JSON` and save the file as `credentials.json` into the `Travel-Ticket-Calendar-2` project folder you git cloned earlier
       ![Screenshot](readme_assets/download_json.jpg)
    10. Go to `Data Access` section present on the left panel
    11. Click on `Add or remove scopes` and add `https://www.googleapis.com/auth/calendar.events.owned` and `https://www.googleapis.com/auth/drive.file` and click on `Update`
        ![Screenshot](readme_assets/update_scope.jpg)
    12. Verify if both scopes are added and click `Save`
        ![Screenshot](readme_assets/save_scopes.jpg)
    13. Go to `Audience` section in the left panel
    14. Click on `+ Add users`
    15. Add your email as a test user and click `Save`
        ![Screenshot](readme_assets/add_test_user.jpg)
    16. Verify if your account is added as a test user
        ![Screenshot](readme_assets/verify_test_user_added.jpg)

-   **Do NOT share your `credentials.json` or `token.json` file (generated after running the script for the first time and logging in) with anyone**

## Google AI Studio Setup

1. Go to [Google AI Studio's API Keys section](https://aistudio.google.com/api-keys)
2. Click on `Create API key` in the top right corner
   ![Screenshot](readme_assets/create_key.jpg)
3. In the modal window that appears give your key a name and in the dropdown select `Import project` if your `Google Cloud Console` project is not visible here
   ![Screenshot](readme_assets/import_project.jpg)
4. Select your project from the panel that opens and click on `Import`
   ![Screenshot](readme_assets/select_project.jpg)
5. Click on `Create key` and your key is generated
   ![Screenshot](readme_assets/create_key_final.jpg)
6. Now create a file called `gemini_credentials.json` in `Travel-Ticket-Calendar-2` folder and paste the key in there in this format

```json
{ "api_key": "AIzaSyC6Doa9ho9aSAGNlePTY7psS1kPw-f6bXo" }
```

## RailRadar API setup

1. Go to [RailRadar website](https://railradar.in/)
2. Sign up for an account
3. Verify the account through an email they should send you after sign up
4. Create a file called `rail_radar_credentials.json` in `Travel-Ticket-Calendar-2` folder and paste the key in there in this format

```json
{ "X-API-Key": "rr_fc7daqttoc3sjmcfag8xveeq6yo8aqpj" }
```

# Usage

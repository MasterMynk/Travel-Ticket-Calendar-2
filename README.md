# Travel Ticket Calendar v2 with Gemini AI Integration

A program that automatically adds your flight/train/bus ticket as an event to your Google Calendar:

-   Runs in the background watching a folder.
-   When a ticket PDF is added to the folder the program scans it and uploads it to your Google Calendar
-  Sends a notification to your system to indicate success/failure

## Table of Contents

1. [Improvements and reason for rewrite](#improvements-over-previous-attempt-and-why-the-re-write)
2. [Setup](#setup)
   1. [Clone the repo](#1-clone-the-repo)
   2. [Install Dependencies](#2-install-dependencies)
   3. [Purpose of different APIs used in this project](#3-identify-required-apiscredentials)
   4. [Cloud Console setup](#4-google-cloud-console-setup-for-calendar-and-drive-api)
   5. [Google AI Studio setup](#5-google-ai-studio-setup)
   6. [RailRadar setup](#6-railradar-api-setup)
3. [Usage](#usage--configuration)

## Improvements over previous attempt and why the re-write

* **Ease of use improvements:** The script now watches a folder, detects an addition and automatically uploads it to the calendar. NO manual intervention needed. You just get a cute notification on your system when the ticket is parsed and uploaded
* **Versatility improvements:** Can handle any type of ticket (bus/flight/train) thrown at it due to integration with Gemini
* **Robustness improvements:** Handles many different types of errors effectively. Knowing when to let go of something and knowing when to quit instead of constantly nagging you till the procedure is complete like the last version did
* **Codebase improvements:** Much more maintainable and hierarchial code as compared to v1. Highly object oriented with almost every class receiving its own dedicated module

* **Why the rewrite?**
   * The codebsae of v1 was highly unmaintainable; New features would take unreasonable effort to add.
   * Interactions with v1 were very clunky and not streamlined; Having to supply details through the commandline is a very poor design
   * Limited set of tickets could be parsed; For each new ticket encounted I'd have to painstakingly add a new parser

# Setup

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

**Dependencies:**
   1. Google libraries for Google APIs and Google Gemini
   2. `pypdf` for reading IRCTC tickets
   3. `requests` for RailRadar API
   4. `watchdog` for efficient system-level folder monitoring
   5. `plyer` to send notifications

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

## 5. Google AI Studio Setup

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

## 6. RailRadar API setup

1. Go to [RailRadar website](https://railradar.in/)
2. Sign up for an account
3. Verify the account through an email they should send you after sign up
4. Create a file called `rail_radar_credentials.json` in `Travel-Ticket-Calendar-2` folder and paste the key in there in this format

```json
{ "X-API-Key": "rr_fc7daqttoc3sjmcfag8xveeq6yo8aqpj" }
```

# Usage & Configuration
* After the setup running the program is as simple as running the following commands from within the project directory

```bash
source venv/bin/activate
python ./main.py
```

* The program then runs indefinitely unless terminated by pressing `Ctrl+C` or some other way

* To configure the program a `config.toml` file can be provided which the program will look for upon startup in `~/.config/Travel Ticket Calendar/`

```toml
# $HOME/.config/Travel Ticket Calendar/config.toml

gapi_credentials_path="<Folder containing main.py that you're running>/credentials.json"
gapi_token_path="<Folder containing main.py>/token.json"
rail_radar_credentials_path="<Folder containing main.py>/rail_radar_credentials.json"
ai_model_credentials_path="<Folder containing main.py>/gemini_credentials.json"

cache_folder="/home/<your username>/.cache/Travel Ticket Calendar/"
# cache_folder="C:\\Users\\<your username>\\.cache\\Travel Ticket Calendar\\" on Windows

ticket_folder="/home/<your username>/travels/"
# cache_folder="C:\\Users\\<your username>\\travels\\" on Windows

log_folder="<Some Folder where logs should be stored>/" # The default value for this is None and the logs are printed to stdout in that case

calendar_id="primary"
reminder_notification_type="popup"
event_color="Banana"
max_retries_for_network_requests=7
ai_model="gemini-2.5-flash-lite"

[cache_data_refresh_time]
magnitude=1
unit="weeks"

[file_transfer_timeout]
magnitude=10
unit="seconds"

[file_transfer_polling_interval]
magnitude=250
unit="milliseconds"

[[reminders]]
magnitude=30
unit="minutes"

[[reminders]]
magnitude=2
unit="hours"

[[reminders]]
magnitude=1
unit="weeks"

[[traveller]]
name=["john doe", "john", "doe john"]
color="Banana"

[[traveller]]
name="mark doe"
color="Grape
```

* These are all the options you can configure with the configuration file
* The first 4 keys can be used to configure the locations of your credential files
* `ticket_folder` Specifies which folder the program will monitor
* Setting of a `log_folder` will result in the logs being put in a separate file instead of on `stdout` -- Very useful when running as a startup script
* Logs are put in different file with names like `log_10_01_2026.txt`
* `reminder_notification_type` can only take values `popup` or `email`
* `event_color` can only take values:
   1. `Lavendar`
   1. `Sage`
   1. `Grape`
   1. `Flamingo`
   1. `Banana`
   1. `Tangerine`
   1. `Peacock`
   1. `Graphite`
   1. `Blueberry`
   1. `Basil`
   1. `Tomato`
* `[[reminders]]` can be added as many times as you like and will determine the reminders to attach to the Google Event
* The `unit` field of a reminder can only take units:
   1. `days`
   1. `seconds`
   1. `microseconds`
   1. `milliseconds`
   1. `minutes`
   1. `hours`
   1. `weeks`
* `[[traveller]]` allows you to specify colors for different people you could possibily have tickets of
* Each `[[traveller]]` list element must contain 2 types: `name` and `color`
* `color` can only take types `event_color` can take
* `name` can be a string or a list of strings specifying all the different permuatations somebody's name could appear in a ticket
* If not specified `event_color` will be used as the event color by default

* **It is NOT necessary to supply all of these fields. Fields that are not supplied will assume their default values and the above configuration file represents those defaults**
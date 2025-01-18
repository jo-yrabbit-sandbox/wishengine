# Hello, create your own TG bot!

This template repo allows you to create your own Telegram bot which integrates with our API infrastructure.
Follow the onboarding instructions below to obtain access.

## Prerequisites

* Obtain your bot token from @BotFather on Telegram
* Have admin access to your own Github organization so that you can add Github secrets to it

## How to start

1. If you don't already have your own Github organization, log in to Github and create one `MY_GITHUB_ORG_NAME`

2. Choose your bot name `MY_BOT_NAME`
    * Bot Naming Requirements:
      - Bot names must be unique across all organizations
      - Names should be descriptive (e.g., "weather-bot", "reminder-bot")
      - Only lowercase letters, numbers, and hyphens allowed
      - Must start with a letter

3. Inform API server admin:
    * `MY_GITHUB_ORG_NAME`
    * `MY_BOT_NAME`

4. Clone this template repo into a blank directory `MY_BOT_NAME`
```sh
cd ~/proj  # Go to your project directory
git clone https://github.com/tee-gee-bots/test-bot.git MY_BOT_NAME
cd MY_BOT_NAME
```

5. Add the following GitHub secret:
    * `TELEGRAM_TOKEN` (obtain this from @BotFather on Telegram)

6. Set Workflow permissions for BOTH your organization AND your new repo
    * Navigate to your organization > Settings > Actions (left column) > General
      * Select "Read and write permissions"
      * Check "Allow GitHub Actions to create and approve pull requests"
    * Navigate to your new repo and do the same

7. Make your first source code change. Note that this name is the unique name you chose above, not necessarily the same name you gave it on Telegram - the name on telegram can always be changed to your liking. But `MY-BOT-NAME` is the unique handle that will be used within the deployed infrastructure, logs, etc.
```python
# src/bot.py
MY_BOT_NAME='test-bot'  # Update me first!
```

8. Push your changes
```sh
git status  # View your changes
git add src/bot.py  # Stage your changed file for commit
git commit -m "Updated bot name"  # Make your first commit
git push  # Push your change to repo
```

9. Confirm that deployment is triggered in Github Actions. If not, contact API server admin for help.

### Deployment

The bot automatically deploys when you:
* Push to main branch
* Manually trigger Github Actions workflow

Under the hood, the API server admin maintains a reusable workflow which gets called every time you trigger deployment.
When you provide `MY_GITHUB_ORG_NAME` and `MY_BOT_NAME`, the API server admins will create a IAM policy/role that allows your bot repo to use this deployment workflow.

### Logs and Monitoring

Logs are available in AWS CloudWatch under `/ecs/[environment]/[MY_BOT_NAME]/*`. Contact API server admin for access.

## Repository structure
```
├── .github/
│   └── workflows/
│       └── deploy.yml    # Deployment workflow
├── src/
│   ├── __init__.py
│   └── bot.py           # Main bot code
├── mock-api-server/
│   └── bot.py           # Main bot code
├── .gitignore
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Container configuration
├── README.md            # This doc
└── requirements.txt     # Python dependencies
```

## Development
It is always best practice to test your changes locally before you deploy.

The expected behavior for this template test bot is to respond to commands: `/start`, `/ping` when you chat with it in Telegram.

There are several ways to test locally:
* Local testing
* Docker build testing
  * Standalone
  * With connection to API server
* Docker-compose with mock api  # Host a mock api at localhost

### Local testing
1. Activate your virtual environment
```sh
# If this is your first time, create your virutal environment
cd ~/proj/MY_BOT_NAME  # Go to your repo top directory
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt  # Install dependencies

# If you already created your virtual environment `venv` already, just activate it
cd ~/proj/MY_BOT_NAME  # Go to your repo top directory
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Set environment variables
This step is only necessary for local testing. If deploying using Github Actions, your secrets will be used instead
```sh
export TELEGRAM_TOKEN="your-token-here"
```

3. Run the bot. Ctrl+C to stop it
```sh
python src/bot.py
```
4. Confirm you can interact with your bot on Telegram

### Docker build testing

1. Create a .env file for local testing only. Don't commit this file!
```sh
# .env
TELEGRAM_TOKEN=your_bot_token_here
API_ENDPOINT=http://your-api-server-public-address.com:5000
```
2. Build the image
```sh
# Build with a tag for easy reference
docker build -t my-test-bot .

# You can verify the image was created
docker images | grep my-test-bot
```

3. Run the container
```sh
# Run with environment variables from .env file
docker run --env-file .env my-test-bot
```

4. Debug commands
```sh
# Run with interactive shell instead of starting the bot
docker run -it --env-file .env my-test-bot /bin/bash

# Check logs
docker logs container_id

# Run with attached output
docker run --env-file .env -it my-test-bot
```
5. Confirm you can interact with your bot on Telegram

### Docker-compose with mock api  
Host a mock api at localhost
1. Create a .env file for local testing only. Include the mock api endpoint. Don't commit this file!
```sh
# .env
TELEGRAM_TOKEN=your_bot_token_here
API_ENDPOINT=http://mock-api:4010
```
2. Run docker-compose to bring up both bot and mock api server
```sh
docker-compose build
docker-compose up

# To stop them
docker-compose down
```
3. Check if mock api server is running (should return `healthy`)
```sh
# We exposed port 5000 to public
curl http://localhost:5000/health
```
4. Check if mock api server is accessible from inside the bot container
```sh
# We exposed port 4010 internally (5000 should fail)
docker-compose exec bot curl http://mock-api:4010/health
```
5. Debug commands
```sh
# Check if service is running
docker-compose ps

# Check logs
docker-compose logs mock-api
```
6. Confirm you can interact with your bot on Telegram

## Reference

Here are some tutorials to help get you started. The easiest example was the "echo-bot" which will parrot back whatever you say to it.
* [https://core.telegram.org/bots/tutorial#echo-bot](https://core.telegram.org/bots/tutorial#echo-bot)
* [https://gitlab.com/Athamaxy/telegram-bot-tutorial/-/blob/main/TutorialBot.py](https://gitlab.com/Athamaxy/telegram-bot-tutorial/-/blob/main/TutorialBot.py)
* [https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py)

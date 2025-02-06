# How is MCO today?

An automated bot called [@howismcotoday](https://x.com/howismcotoday) on [X](x.com), which scrapes the MCO Departures Board for upcoming departures and produces a scoring metric for how well the airport is operating. Posts an updated score every 1.5 hours.

A **good** hour is defined currently as 50% or more of scheduled departures are on-time.

A **bad** hour is defined currently as 50% or less of scheduled departures are on-time.

In the future, the bot will add functionality to pull TSA wait times and build a more robust scoring system. For now though, this is a little webscraper to twitter pipeline. :)


## 🧍‍♂️ Authors

- [@cruzdariel](https://www.github.com/cruzdariel)


## 🔐 Environment Variables

To run this project, you will need to add the following environment variables to your `keys/secrets.sh` file:

- `API_KEY`

- `API_SECRET`

- `ACCESS_TOKEN`

- `ACCESS_SECRET`

Before running the application, you need to load the variables into the environment by running 'source ./keys/secrets.sh', or wherever your secrets file is in the terminal.

If you are operating in an isolated secure environment and do not need to encrypt your keys, pass the keys through as variables directly in `app.py`.

You can access keys from X's [Developer Portal](https://developer.twitter.com/en/portal/petition/essential/basic-info).

## 🔄 Dependencies
Run `pip install bs4 tweepy requests` to install all the necessary modules to run this program.
- Beautiful Soups, for the web scraper `pull_data()`
- Tweeepy, a wrapper for interacting with X's API (you could also interact with it directly using requests to call X's V2 enpoint or another wrapper [here](https://docs.x.com/x-api/tools-and-libraries/overview#python))

## 📝 Notes

- X has a limit on Free developer accounts where **apps can only post 17 tweets every 24 hours.** The app runs every 1.5 hours, which averages out to 16 tweets per day. If the app runs into an error, it will look through the header of the error returned by X's API and pull every reset time for different rate limits, take the highest reset time, return the time in seconds between now and the reset time, and force the app to wait that amount of time before trying again. If you have a paid account or do not require this redunancy, feel free to remove it at the end of the script.
- The web scraper function `pull_data()` locates the table with flights and extracts each row as a list inside a larger list `flights`. Depending on how your airport's website is designed, you may need to change the behavior of the web scraper. Learn more about using Beautiful Soups [here](https://realpython.com/beautiful-soup-web-scraper-python/).

## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://dariel.us/)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/darielc)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/darieltweet)


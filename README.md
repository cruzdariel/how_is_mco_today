# How is MCO today?

An automated bot called [@howismcotoday](https://x.com/howismcotoday) on [X](x.com), which scrapes the MCO Departures Board for upcoming departures and produces a scoring metric for how well the airport is operating. Posts an updated score every 1.5 hours.

In the future, the bot will add functionality to pull TSA wait times and build a more robust scoring system. For now though, this is a little webscraper to twitter pipeline. :)


## 🧍‍♂️ Authors

- [@cruzdariel](https://www.github.com/cruzdariel)


## 🧮 The scoring model
The current scoring model represents a simple fraction: 

$$\text{Score V1} = \frac{\text{No. of On Time Departures}}{\text{No. of Total Departures}}$$

However, in future updates the scoring model will be replaced by a more nuanced calculation. In the planned version 2 of the scoring model, the bot will take into account counts of flight delays in addition to TSA wait time averages for both TSA Precheck and general checkpoints. The scoting model in the next update will likely be:

$$\text{Score V2}=a\left(1-\left(\frac{1}{1+e^{\left(-70\left(\frac{C}{O+D+C}\right)+3\right)}}-\frac{1}{1+e^{3}}\right)\right)+b\left(1-\left(\frac{1}{1+e^{\left(-15\left(\frac{D}{O+D+C}\right)+3\right)}}-\frac{1}{1+e^{3}}\right)\right)+c\left(1-\left(\frac{1}{1+e^{\left(-0.1\left(G-50\right)\right)}}-\frac{1}{1+e^{5}}\right)\right)+d\left(1-\left(\frac{1}{1+e^{\left(-0.1\left(P-15\right)\right)}}-\frac{1}{1+e^{1.5}}\right)\right)$$

Where:
- $$\alpha{} = \text{Weight of On-Time Flights}$$
- $$\beta{} = \text{Weight of Delayed/Cancelled Flights}$$
- $$\gamma{} = \text{Weight of TSA General Wait Times}$$
- $$\delta{} = \text{Weight of TSA PreCheck Wait Times}$$
- $$O = \text{No. of On Time Departures}$$
- $$D = \text{No. of Delayed Departures}$$
- $$C = \text{No. of Cancelled Departures}$$
- $$W_x = \text{Average wait for TSA PreCheck or General (in minutes)}$$
- $$f(W_x) = \frac{W_x}{W_x+k}$$, where $$k = \text{Historic Average Wait (in minutes)}$$

You can find a visualization of this equation in [Demos](https://www.desmos.com/calculator/lzmoy6q9rm).

Although this next update will be much better than a simple count of on time flights over total flights, there is still [work left to be done](https://www.youtube.com/watch?v=fY7l2pcxdHM). In future editions, I want to calculate the average length of delay for each delayed flight, and weigh longer delays more than shorter delays in the calculation. I feel this is a fairer scoring metric than the current metric, which is a simple count of delayed flights.


## ▶️ Running the app
### 🔐 Environment Variables

To run this project, you will need to add the following environment variables to your `keys/secrets.sh` file:

- `API_KEY`

- `API_SECRET`

- `ACCESS_TOKEN`

- `ACCESS_SECRET`

Before running the application, you need to load the variables into the environment by running `source ./keys/secrets.sh`, or wherever your secrets file is in the terminal.

If you are operating in an isolated secure environment and do not need to encrypt your keys, pass the keys through as variables directly in `app.py`.

You can access keys from X's [Developer Portal](https://developer.twitter.com/en/portal/petition/essential/basic-info).

### 🔄 Dependencies
Run `pip install bs4 tweepy requests` to install all the necessary modules to run this program.
- Beautiful Soups, for the web scraper `pull_data()`
- Tweeepy, a wrapper for interacting with X's API (you could also interact with it directly using requests to call X's V2 enpoint or another wrapper [here](https://docs.x.com/x-api/tools-and-libraries/overview#python))

## 📝 Notes

- X has a limit on Free developer accounts where **apps can only post 17 tweets every 24 hours.** The app runs every 1.5 hours, which averages out to 16 tweets per day. If the app runs into an error, it will look through the header of the error returned by X's API and pull every reset time for different rate limits, take the highest reset time, return the time in seconds between now and the reset time, and force the app to wait that amount of time before trying again. If you have a paid account or do not require this redunancy, feel free to remove it at the end of the script.
- The web scraper function `pull_data()` locates the table with flights and extracts each row as a list inside a larger list `flights`. Depending on how your airport's website is designed, you may need to change the behavior of the web scraper. Learn more about using Beautiful Soups [here](https://realpython.com/beautiful-soup-web-scraper-python/).
- I am running this on a Linux remote machine hosted at the University of Chicago, using `tmux` to keep the `app.py` file running persistently after I disconnect. You can use any virtual machine environment that can run python3 and has a command line interface that can run tmux (or screen). I've seen people use [Amazon EC2 Free Tier](https://aws.amazon.com/ec2/?did=ft_card&trk=ft_card).

## 🔜 What's Next
Here are some ideas I have in store for future versions of this X bot:
- [ ] Store updates in a .csv file for future analysis and to act as an open source database for other researchers
- [X] In addition to flights, scrape TSA wait times for all terminals
- [ ] Adjust the scoring system to incorporate TSA wait times (longer waits, lower score)
- [ ] Adjust the scoring system to give more weight based on length of delays (more delayed flights ding the score more than say a 1-2 minute delay)
- [X] Add a function to return poorly operating airlines at MCO, call them out on X updates. (sorry Spirit!)
- [ ] Add a function to return delays to certain cities, appending them to posts if multiple flights are delayed that are departing to a single airport
- [ ] Eventually, after enough data is collected, compare scores to averages on the same day in the prior month in posts
- [ ] Add a function that checks if the FAA has issued an airport event on the [National Airspace System Status](https://nasstatus.faa.gov/list) and appends the delay average to tweets if one is issued for MCO.

## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://dariel.us/)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/darielc)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/darieltweet)


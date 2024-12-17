# RGC Data Engineering Task

## Task

Build a dashboard that acts as a portfolio analyser.

Please use whatever tools you are familiar and comfortable with but bear in mind the notes in the [Implementation](TASK.md#implementation) section below.

You will find some hints and guidance in the [HINTS](HINTS.md) file.

## Inputs

The portfolio analyser will accept a csv file containing the portfolio as a timeseries.

The portfolio will be for S&P500 stocks and long only, no shorts. It will be tested with the portfolio found in the [input folder](input/portfolio.csv).

The timeseries will be indexed on date, the stock tickers are the columns and the **closing position** for that date is the value.

e.g.

```
Date,AAPL,ABBV,ALL,BA,BIIB,COP,DE,DVN,EL,EQT,GOOGL,HII,INTC,KDP,MSFT,NEE,NFLX,PAYC,PFE,QRVO,ROP,SMCI,TSLA,UAL
2024-08-30,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2024-09-03,0,0,0,0,0,32,0,9,20,0,0,22,0,0,0,0,3,0,2,0,23,0,0,0
2024-09-04,13,0,0,0,32,0,11,0,0,0,18,11,0,0,0,0,0,30,0,0,49,0,0,0
2024-09-05,24,0,4,0,54,0,28,0,18,0,51,0,36,0,0,16,21,0,0,0,88,0,0,0
2024-09-06,0,27,0,0,65,0,66,3,39,0,90,0,83,0,0,0,64,3,0,0,80,0,0,0
```

## Outputs

Show the P&L of the portfolio, a graph of the P&L over time and a table containing the top 5 winners and bottom 5 losers for the portfolio.

## Implementation

Please ensure your code works as is, we will make some effort to rectify any issues but the expectation is your code will run on a Windows 11 machine running Python 3.10.

If special steps are required to run the dashboard, please document them (e.g. change directory to run the dashboard).

Functionality is more important than looks, we would prefer a functioning dashboard that doesn't look brilliant instead of a flashy dashboard that doesn't work.

Comments and documentation in the code are optional - if your code is clear and concise none should be required.

## Assessment Criteria

* Project structure - your code and any resources are structured in a relatively standard way
* Python knowledge - you demonstrate a good knowledge of the Python programming language and the package ecosystem
* Error handling - how does your code handle non-existent stocks or malformed data
* Pandas knowledge - good use of pandas when processing data, vectorise operations as much as possible, knowledge of multi-indexes and timeseries functions
* Data structure - importing data and processing it for use in a sensible structure
* Performance - caching of data, efficient data processing operations
* User experience - as mentioned above, the look of the dashboard is not important but a user should still be able to use it in a relatively intuitive manner

## Extra Credit

These considerations go above and beyond the basic assessment criteria and will be noted when reviewing your solution.

* Different file formats to upload - Excel, parquet
* Containerisation - Dockerfile present, builds and runs
* Currency localisation - convert the data to pounds, euros, other currencies
* Additional indices - FTSE, EuroStoxx
* Execution price provided - Allow the user to provide the execution price the stock was traded at
* Additional metrics/analysis - What other information would be of interest to someone analysing their portfolio
* API - add an api endpoint that can be used to submit the portfolio and get results

import random

import pandas as pd
from portfolio_analytics.common.filesystem import PORTFOLIO_SAMPLES_DIR


# Function to generate mock data
def generate_portfolio_data(start_date, end_date, tickers, base_range=(0, 200)):
    # Generate a list of dates
    date_range = pd.date_range(start=start_date, end=end_date, freq="B")
    data = []

    for date in date_range:
        # Generate random holdings for each ticker
        row = [date] + [random.randint(base_range[0], base_range[1]) for _ in tickers]
        data.append(row)

    # Create DataFrame
    columns = ["Date"] + tickers
    portfolio_df = pd.DataFrame(data, columns=columns)
    return portfolio_df


# Define parameters
start_date = "2018-01-01"
end_date = "2024-12-16"
# fmt: off
existing_tickers = ["AAPL", "ABBV", "ALL", "BA", "BIIB", "COP", "DE", "DVN", "EL", "EQT",
                    "GOOGL", "HII", "INTC", "KDP", "MSFT", "NEE", "NFLX", "PAYC", "PFE",
                    "QRVO", "ROP", "SMCI", "TSLA", "UAL"]
# fmt: on
# Additional FTSE 100 and EURO STOXX 50 tickers
new_tickers = ["HSBA.L", "BP.L", "SHEL.L", "DHL.DE", "SAP.DE", "BNP.PA"]
all_tickers = existing_tickers + new_tickers

# Generate data
portfolio_data = generate_portfolio_data(start_date, end_date, all_tickers)

# Save to CSV
output_file = PORTFOLIO_SAMPLES_DIR / "sample_portfolio_extended.csv"
portfolio_data.to_csv(output_file, index=False)

print(f"Mock portfolio data generated and saved to {output_file}.")

import re
import pandas as pd
from collections import defaultdict, Counter

def extract_currency_data(text):
    # Define patterns for currencies and card numbers
    currency_patterns = {
        'EUR': r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)欧元',
        'DKK': r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)丹麦克朗',
        'SEK': r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)瑞典克朗',
        'USD': r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)美元',
        'CNY': r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)元'
    }
    date_pattern = r'(\d{1,2}月\d{1,2}日)'

    # Initialize lists to store results
    transactions = []

    # Find all matches of date, card number, and amounts
    for match in re.finditer(rf'({date_pattern}).+?({"|".join(currency_patterns.values())})', text):
        date = match.group(1)
        for currency, pattern in currency_patterns.items():
            amount_match = re.search(pattern, match.group(0))
            if amount_match:
                amount = amount_match.group(1).replace(',', '')
                amount = float(amount)
                transactions.append((date, currency, amount))

    return transactions

def summarize_transactions(transactions):
    summary = defaultdict(lambda: defaultdict(float))
    daily_transactions_count = defaultdict(int)

    for date, currency, amount in transactions:
        summary[date][currency] += amount
        daily_transactions_count[date] += 1

    return summary, daily_transactions_count

# Initialize the text variable
text = """
"""


# Extracting the data
transactions = extract_currency_data(text)

# Summarizing the transactions
summary, daily_transactions_count = summarize_transactions(transactions)

# Converting summary to a DataFrame for better readability
data = []
for date in summary:
    amounts = {currency: summary[date].get(currency, 0) for currency in ['SEK', 'EUR', 'DKK', 'USD','CNY']}
    data.append([date, amounts['SEK'], amounts['EUR'], amounts['DKK'], amounts['USD'], amounts['CNY'], daily_transactions_count[date]])

df = pd.DataFrame(data, columns=['Date', 'SEK', 'EUR', 'DKK', 'USD', 'CNY',  'NumberofTransactions'])
df_sorted = df.sort_values(by=['Date'])

# Displaying the DataFrame
print(df_sorted)

# Summarizing total amounts by currency
total_summary = {currency: sum(summary[date][currency] for date in summary) for currency in ['SEK', 'EUR', 'DKK', 'USD', 'CNY']}

print("\nTotal Amounts by Currency:")
for currency, amount in total_summary.items():
    print(f"{currency}: {amount}")

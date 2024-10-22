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
尾号6020(副)卡6月8日02:14POS支出(消费Albert Heijn 1567 AMSTERDAM)8.54欧元。 尾号6020(副)卡6月9日04:35POS支出(消费Ah To Go 5870 Amsterdam)17.50欧元。 尾号6020(副)卡6月9日05:13POS支出(消费IJssalon Tofani AMSTERDAM)4欧元。 尾号6020(副)卡6月9日18:14POS支出(消费PRIMARK DAMRAK AMSTERDAM)153.80欧元。 尾号6020(副)卡6月9日18:19POS支出(消费Albert Heijn 5614 AMSTERDAM)6.60欧元。 尾号6020(副)卡6月9日19:38网上银行支出(消费)389.37欧元。尾号6020(副)卡6月10日00:07网上银行支出(消费)37.50欧元。尾号6020(副)卡6月10日02:01POS支出(消费Albert Heijn 2213 AMSTERDAM)8.43欧元。 尾号6020(副)卡6月10日15:09POS支出(消费Back to Black Amsterdam)7.24欧元。 尾号6020(副)卡6月10日15:37POS支出(消费Albert Heijn 1676 AMSTERDAM)2.09欧元。 尾号6020(副)卡6月10日22:00POS支出(消费Albert Heijn 2207 S-GRAVENHAGE)3.59欧元。 尾号6020(副)卡6月10日23:27POS支出(消费Albert Heijn 1473 S-GRAVENHAGE)15.06欧元。 尾号6020(副)卡6月11日04:51POS支出(消费Albert Heijn 1671 S-GRAVENHAGE)6.89欧元。 尾号6020(副)卡6月11日21:50POS支出(消费Bij Lotje Den Haag)3.50欧元。 尾号6020(副)卡6月12日00:16POS支出(消费Gvc Kiosk Doorloop Den Haag)5.99欧元。 尾号6020(副)卡6月12日00:46POS支出(消费Ah To Go 5825 Rotterdam Cs)7.75欧元。 尾号6020(副)卡6月12日02:19POS支出(消费Jumbo Delft Bastiaansp Delft)1.77欧元。 尾号6020(副)卡6月12日03:47POS支出(消费Albert Heijn 1051 S-GRAVENHAGE)6.22欧元。 尾号6020(副)卡6月12日08:41网上银行支出(消费)151.65欧元。尾号6020(副)卡6月12日17:56网上银行支出(消费)466.16欧元。尾号6020(副)卡6月12日19:14POS支出(消费CCV*Starbucks 10 CS S GRAVENHAGE)6.16欧元。 尾号6020(副)卡6月12日20:52POS支出(消费Albert Heijn 1311 UTRECHT)1.14欧元。 尾号6020(副)卡6月12日21:34POS支出(消费St.Ned.Spoorwegmuseu UTRECHT)12.50欧元。 尾号6020(副)卡6月12日22:51POS支出(消费Albert Heijn 2204 UTRECHT)4.59欧元。 尾号6020(副)卡6月13日04:15POS支出(消费Albert Heijn 2204 UTRECHT)4.59欧元。 尾号6020(副)卡6月13日16:45POS支出(消费Albert Heijn 5703 AMSTERDAM)7.30欧元。 尾号6020(副)卡6月13日17:36POS支出(消费Lockerpoint Luggage St Amsterdam)9欧元。 尾号6020(副)卡6月13日21:46网上银行支出(消费)19.75欧元。尾号6020(副)卡6月13日23:40POS支出(跨行消费Van Gogh Museum EnterprisAmsterd)318.29元。尾号6020(副)卡6月14日20:08POS支出(消费Albert Heijn 5703 AMSTERDAM)6.05欧元。 尾号6020(副)卡6月14日20:09POS支出(消费Albert Heijn 5703 AMSTERDAM)2.60欧元。 尾号6020(副)卡6月14日21:01POS支出(消费LSP*Luuks Coffee Amsterdam)4.75欧元。 尾号6020(副)卡6月15日04:43POS支出(消费Ah To Go 5870 Amsterdam)4.05欧元。 尾号6020(副)卡6月15日06:10网上银行支出(消费)5,701.06美元。尾号6020(副)卡6月15日21:38POS支出(消费Albert Heijn 1035 AMSTERDAM)3.39欧元。 尾号6020(副)卡6月15日22:29POS支出(消费CCV*Kafenion AMSTERDAM)4.50欧元。 尾号6020(副)卡6月16日00:51POS支出(消费ALBERT HEIJN 2209 Amsterdam)1.24欧元。 尾号6020(副)卡6月16日01:01POS支出(跨行消费PANDORA Amsterdam Leid Amsterd)304.71元。尾号6020(副)卡6月16日04:02POS支出(消费Albert Heijn 1080 AMSTERDAM)13.73欧元。  尾号6020(副)卡6月16日22:08POS支出(消费DSB APP Taastrup)17.80丹麦克朗。尾号6020(副)卡6月17日01:32POS支出(消费DSB APP Taastrup)17.80丹麦克朗。尾号4938(副)卡6月17日18:32POS支出(消费NETTO FIOLSTRED K*BENHAVN K)7.06丹麦克朗。尾号4938(副)卡6月17日18:41POS支出(消费CONDITORI LA GL K*BENHAVN K)98.83丹麦克朗。尾号4938(副)卡6月17日22:45POS支出(消费Buka ApS Koebenhavn)38丹麦克朗。尾号4938(副)卡6月17日22:53POS支出(消费Buzz Kaffebar ApS Kobenhavn K)32丹麦克朗。尾号4938(副)卡6月17日23:01POS支出(消费KRISTINEDAL KOBENHAVN S)125丹麦克朗。尾号4938(副)卡6月17日23:25POS支出(消费STARBUCKS INDUS K*BENHAVN V)59.53丹麦克朗。尾号4938(副)卡6月18日02:07POS支出(消费NETTO FEM*REN K*BENHAVN S)40.25丹麦克朗。 尾号4938(副)卡6月18日21:45POS支出(消费F*TEX FOOD S*LV K*BENHAVN K)38.29丹麦克朗。尾号4938(副)卡6月18日21:53POS支出(消费Zettle_* Tradition Sho Kobenhavn K)50丹麦克朗。尾号4938(副)卡6月18日22:13POS支出(消费SP LA CABRA FREDERIKSBE)34丹麦克朗。尾号4938(副)卡6月18日22:27POS支出(消费Illum A/S Koebenhavn)154丹麦克朗。尾号4938(副)卡6月18日22:31POS支出(消费ORIGINAL COFFEE ILLUM KOBENHAVN K)20丹麦克朗。尾号4938(副)卡6月18日23:55POS支出(消费NETTO FEM*REN K*BENHAVN S)33.95丹麦克朗。尾号4938(副)卡6月19日15:59POS支出(消费STARBUCKS RADHU K*BENHAVN V)59.53丹麦克朗。尾号4938(副)卡6月19日19:52POS支出(消费IMEXdj Aps Herlev)194丹麦克朗。尾号4938(副)卡6月19日19:53POS支出(消费emmerys 510 Koebenhavn)63丹麦克朗。尾号4938(副)卡6月19日23:17POS支出(消费Pressbyran Malmoe SoedergMalmoe)37瑞典克朗。尾号4938(副)卡6月19日23:28POS支出(消费LeDante shop Malmo)79瑞典克朗。尾号4938(副)卡6月20日01:07POS支出(消费SKA STN MALMO C HaSSLEHOLM)34.80瑞典克朗。尾号4938(副)卡6月20日01:38POS支出(消费5 FLOWERS FOOD LUND)139瑞典克朗。尾号4938(副)卡6月20日03:56POS支出(消费NETTO FEM*REN K*BENHAVN S)8.03丹麦克朗。尾号4938(副)卡6月20日15:56POS支出(消费NETTO RADHUSPLA K*BENHAVN K)39.35丹麦克朗。尾号4938(副)卡6月20日16:01POS支出(消费STARBUCKS RADHU K*BENHAVN V)65.58丹麦克朗。尾号4938(副)卡6月20日18:01POS支出(消费MOMO WOK BOX KOBENHAVN K)109丹麦克朗。尾号6020(副)卡6月20日19:51POS支出(消费DSB APP Taastrup)42丹麦克朗。尾号4938(副)卡6月20日20:48POS支出(消费Forsea Helsingoer ApS Helsingoer)4丹麦克朗。 尾号4938(副)卡6月20日20:53POS支出(消费Forsea Helsingoer ApS Helsingoer)53丹麦克朗。尾号4938(副)卡6月20日22:05POS支出(消费CHENS DUMPLINGS HELSINGBORG)159瑞典克朗。尾号4938(副)卡6月20日23:05POS支出(消费SOFIERO HELSINGBORG)155瑞典克朗。尾号4938(副)卡6月20日23:20POS支出(消费SOFIERO SLOTTSRESTAURANG HELSINGBORG)58瑞典克朗。 尾号4938(副)卡6月21日00:04POS支出(消费SKA STN HELSINGBORG C HaSSLEHOLM)245瑞典克朗。尾号4938(副)卡6月21日01:53POS支出(消费Coop365 Kastrupvej Kastrup)13丹麦克朗。 尾号4938(副)卡6月21日02:04POS支出(消费OK PLUS KASTRUP K*BENHAVN S)83.95丹麦克朗。尾号4938(副)卡6月21日02:08POS交易撤销(消费OK PLUS KASTRUP K*BENHAVN S)83.95丹麦克朗。 尾号4938(副)卡6月21日02:28POS支出(消费NETTO FEM*REN K*BENHAVN S)29.95丹麦克朗。尾号4938(副)卡6月21日08:16POS支出(消费SKA BLIPPA HASSLEHOLM)31瑞典克朗。 尾号4938(副)卡6月21日19:21POS支出(消费Taste of Taiwan Koebenhavn)45丹麦克朗。尾号4938(副)卡6月21日20:21POS支出(消费Hoppes Cafe & Bar Koebenhavn)223丹麦克朗。尾号4938(副)卡6月21日20:41POS支出(消费LAGKAGEHUSET A/ K*BENHAVN K)73.37丹麦克朗。 尾号4938(副)卡6月21日20:53POS支出(消费7-ELEVEN B005 K*BENHAVN K)62丹麦克朗。
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

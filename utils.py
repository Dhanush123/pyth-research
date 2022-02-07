import csv 

PRICE_FEED_SYMBOL = 'ETH-USD'

def init_csv_writer(filename, fields):
    with open(filename, 'w', encoding='utf-8') as csvfile: 
      csv.writer(csvfile).writerow(fields) 

def save_to_csv(filename, fields_data):
    with open(filename, 'a+', encoding='utf-8') as csvfile: 
      csv.writer(csvfile).writerow(fields_data) 
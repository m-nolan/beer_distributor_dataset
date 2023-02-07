import numpy as np
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

BEER_DIST_URL = r"https://www.findmeabrewery.com/distributors/"
DIST_FILE_NAME = 'beer_distributor_data.csv'

def get_dist_url_data( dist_url=BEER_DIST_URL ):
    page = requests.get(dist_url)
    return BeautifulSoup(page.content,"html.parser")

def proc_dist_url_data( dist_url_data ):
    # MESSY but gets us a list.
    state_list = dist_url_data.find_all('h2',text=re.compile('Beer Distributors in *'))
    data_list = []
    for state_h2 in state_list:
        state_name = re.findall('^Beer Distributors in (.+?)$',state_h2.text)[0]
        data_list.append(state_name)
        state_data_list = []
        dist_entry_list = []
        next_elem = state_h2.next_sibling
        while True:
            if next_elem is None or next_elem.name == 'h2':
                state_data_list.append(dist_entry_list)
                dist_entry_list = []
                break
            if next_elem.text == r'\n':
                next_elem = next_elem.next_sibling
                # continue
            if next_elem.name == 'h3' and len(dist_entry_list) > 0:
                state_data_list.append(dist_entry_list)
                dist_entry_list = []
            dist_entry_list.append(next_elem.text)
            next_elem = next_elem.next_sibling
        data_list.append(state_data_list)
    return data_list

def clean_dist_entry( dist_entry ):
    return [de for de in dist_entry if de != '\n']

def proc_dist_entry( dist_entry ):
    name = dist_entry[0]
    addr_full = dist_entry[1]
    website = dist_entry[2] if len(dist_entry) > 2 else np.nan
    if isinstance(website,str):
        website = website.replace('\n','').replace('- ','').strip()
    addr, phone = addr_full.split(' - ')
    addr_street, addr_city, addr_state_zip = addr.split(', ')
    try:
        addr_state, addr_zip = addr_state_zip.split(' ',1) # catch the odd BC distributor
    except:
        print(addr_state_zip)
    return name.strip(), addr_street.strip(), addr_city.strip(), addr_state.strip(), addr_zip.strip(), phone.strip(), website

def proc_data_list( data_list ):
    dist_df = pd.DataFrame(columns=['Name','Address','State','Phone','Website'])
    for entry in data_list:
        if isinstance(entry,str):
            state_name = entry
        elif isinstance(entry,list):
            for dist_entry in entry:
                if len(dist_entry) < 2:
                    continue
                dist_entry = clean_dist_entry(dist_entry)
                name, addr, city, state_abbr, zip_code, phone, website = proc_dist_entry(dist_entry)
                dist_entry_dict = {
                    'Name': [name],
                    'Address': [addr],
                    'City': [city],
                    'State': [state_name],
                    'State Abbr': [state_abbr],
                    'Zip': [zip_code],
                    'Phone': [phone],
                    'Website': [website],
                }
                dist_df = pd.concat([dist_df,pd.DataFrame.from_dict(dist_entry_dict)],ignore_index=False)
    dist_df.index = np.arange(len(dist_df))
    return dist_df

def save_dist_df( dist_df, file_name=DIST_FILE_NAME ):
    dist_df.to_csv(file_name)

def main():
    dist_url_data = get_dist_url_data()
    data_list = proc_dist_url_data(dist_url_data)
    dist_df = proc_data_list(data_list)
    save_dist_df(dist_df)

if __name__ == "__main__":
    main()
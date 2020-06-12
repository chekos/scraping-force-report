import pandas as pd
from selenium import webdriver
from pathlib import Path
from datetime import datetime as dt 
today = dt.today().strftime("%Y-%m-%d")

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent
CHROMEDRIVER_PATH = THIS_DIR.joinpath("./../../notebooks/chromedriver")
INTERIM_DATA = THIS_DIR.joinpath("./../../data/interim/")
PROCESSED_DATA = THIS_DIR.joinpath("./../../data/processed/")

BASE_URL = "http://force.nj.com"

browser = webdriver.Chrome(CHROMEDRIVER_PATH)
# Compile list police dept of options from dropdown menu
browser.get(BASE_URL)

police_depts_list = browser.find_element_by_id("mylist")
police_depts = police_depts_list.find_elements_by_tag_name("option")

depts_list = []
for dept in police_depts:
    dept_info = {}
    dept_info['name'] = dept.get_attribute("innerHTML").strip()
    dept_info['relative_url'] = dept.get_attribute("value")
    depts_list.append(dept_info)

def get_likelihood_numbers(div_name = 'left'):
    race_breakdown = browser.find_element_by_class_name("racial_breakdown")
    div = race_breakdown.find_element_by_class_name(div_name)
    based_on = div.find_element_by_class_name("important_num2").get_property("innerHTML").strip()
    likelihood = div.find_element_by_class_name("important_num1").get_property("innerHTML").strip()
    return (based_on, likelihood)

def get_flagging_officer_numbers():
    early_warning = browser.find_element_by_class_name("earlywarning")
    elements = early_warning.find_elements_by_class_name("important_num_red2")
    if len(elements) == 6:
        first_city = elements[0].get_property("innerHTML")
        first_city_n = elements[1].get_property("innerHTML")
        second_city = elements[2].get_property("innerHTML")
        second_city_n = elements[3].get_property("innerHTML")
        third_city = elements[4].get_property("innerHTML")
        third_city_n = elements[5].get_property("innerHTML")
    return (first_city, first_city_n, second_city, second_city_n, third_city, third_city_n)

for dept in depts_list:
    # go to page
    browser.get(BASE_URL + dept['relative_url'])
    
    # get likelihood numbers
    # by population
    try:
        (prop, number) = get_likelihood_numbers('left')
        dept[prop] = number
    except:
        dept['population'] = 'Not found'
    # by arrests
    try:
        (prop, number) = get_likelihood_numbers('right')
        dept[prop] = number
    except:
        dept['arrests'] = 'Not found'
    
    # get no of officers that would be flagged in other cities
    try:
        (first_city, first_city_n, second_city, second_city_n, third_city, third_city_n) = get_flagging_officer_numbers()
        dept[first_city] = first_city_n
        dept[second_city] = second_city_n
        dept[third_city] = third_city_n
    except:
        dept['Los Angeles'] = 'Not found'
        dept['New York City'] = 'Not found'
        dept['Chicago'] = 'Not found'
    
data = pd.DataFrame(depts_list)
data['full_url'] = BASE_URL + data['relative_url']

data.to_csv(INTERIM_DATA / f'rough-scrape-data-{today}.csv', encoding = 'utf-8', index = False)
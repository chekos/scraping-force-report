import pandas as pd
from selenium import webdriver
from pathlib import Path
from datetime import datetime as dt
import time

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
time.sleep(2)

police_depts_list = browser.find_element_by_id("mylist")
police_depts = police_depts_list.find_elements_by_tag_name("option")

depts_list = []
for dept in police_depts:
    dept_info = {}
    dept_info["name"] = dept.get_attribute("innerHTML").strip()
    dept_info["relative_url"] = dept.get_attribute("value")
    depts_list.append(dept_info)


def get_incidents_table():
    """Retrieve the incidents table presented by default in each police depts page.
        
    Returns
    -------
    table : pd.DataFrame
       table containing `n_rows` officers per dept
    """
    incidents_table = browser.find_element_by_id("incidents_table").get_property(
        "outerHTML"
    )
    table = pd.read_html(incidents_table)[0]
    voi = [col for col in table if "Unnamed" not in col]
    return table[voi]


def get_number_of_total_rows():
    sentence = browser.find_element_by_id("incidents_table_info").get_property(
        "innerHTML"
    )
    n_rows = int(sentence.split(" of ")[-1].split()[0])
    return n_rows


def change_table_length(n):
    browser.find_element_by_xpath(
        f"//select[@name='incidents_table_length']/option[text()='{n}']"
    ).click()


# render the first page in case it takes a bit to load
browser.get(BASE_URL + depts_list[0]["relative_url"])
time.sleep(2)
for dept in depts_list[:5]:
    browser.get(BASE_URL + dept["relative_url"])
    try:
        print("changing table length...")
        change_table_length(100)
        total_n_rows = get_number_of_total_rows()
        n_rounds = (total_n_rows // 100) + 1
        print(f"Getting table for {dept['name']}: {total_n_rows} entries.")
        tables = []
        for page in range(n_rounds):
            print(f"round {page}/{n_rounds}")
            tables.append(get_incidents_table())
            browser.find_element_by_id("incidents_table_next").click()
        df = pd.concat(tables)
        clean_name = (
            dept["name"]
            .replace(", ", "-")
            .lower()
            .replace("&amp;", "_")
            .replace(" ", "-")
            .replace("-_-", "_")
            .replace("'", "")
            .replace("&nbsp;", "")
        )
        df.to_csv(
            PROCESSED_DATA / f"use_of_force_incidents---{clean_name}.csv",
            encoding="utf-8",
            index=False,
        )
    except:
        pass

browser.close()

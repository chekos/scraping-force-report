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


def get_likelihood_numbers(div_name="left"):
    """Retrieves 'likelihood of use of force' numbers from force.nj.com website. These numbers are in 2 divs inside the 'race_breakdown' div.

    Parameters
    ----------
    div_name : str, optional
        Either the left or the right div, by default 'left'

    Returns
    -------
    touple : touple
        A touple containing the property name and likelihood number (text) for either the 'left' or 'right' div.
    """
    race_breakdown = browser.find_element_by_class_name("racial_breakdown")
    div = race_breakdown.find_element_by_class_name(div_name)
    based_on = (
        div.find_element_by_class_name("important_num2")
        .get_property("innerHTML")
        .strip()
        .replace(",", "")
    )
    likelihood = (
        div.find_element_by_class_name("important_num1")
        .get_property("innerHTML")
        .strip()
        .replace(",", "")
    )
    more_or_less = (
        div.find_elements_by_class_name("important_num2")[-1]
        .get_property("innerHTML")
        .strip()
    )
    return (based_on, likelihood, more_or_less)


def get_flagging_officer_numbers():
    """Retrieve the 'number of officers that would be flagged in other agencies' from force.nj.com website. These numbers are inside the 'earlywarning' div.

    Returns
    -------
    touple : touple
        A six-part touple containing the city name and number for Los Angeles, New York City, and Chicago.
    """
    early_warning = browser.find_element_by_class_name("earlywarning")
    elements = early_warning.find_elements_by_class_name("important_num_red2")
    if len(elements) == 6:
        first_city = (
            elements[0]
            .get_property("innerHTML")
            .strip()
            .replace("'s", "")
            .replace("'", "")
        )
        first_city_n = elements[1].get_property("innerHTML").strip()
        second_city = (
            elements[2]
            .get_property("innerHTML")
            .strip()
            .replace("'s", "")
            .replace("'", "")
        )
        second_city_n = elements[3].get_property("innerHTML").strip()
        third_city = (
            elements[4]
            .get_property("innerHTML")
            .strip()
            .replace("'s", "")
            .replace("'", "")
        )
        third_city_n = elements[5].get_property("innerHTML").strip()
    return (
        first_city,
        first_city_n,
        second_city,
        second_city_n,
        third_city,
        third_city_n,
    )


def get_average_number_of_officers():
    """Retrieve the average number of full time officers in police dept.

    Returns
    -------
    n : str
       `innerHTML` of right div in the town_info div.
    """
    pd_info = browser.find_element_by_class_name("pd_info")
    town_info = pd_info.find_element_by_class_name("town_description")
    return (
        town_info.find_element_by_class_name("right")
        .find_element_by_class_name("town_label")
        .get_property("innerHTML")
    )


def get_rate_of_force():
    """Retrieve the rate of force ('this dept uses force at a rate higher than X other depts').
        
    Returns
    -------
    sentnce : str
       `innerHTML` of h3 inside the rank_five_years section.
    """
    rank_five_years = browser.find_element_by_id("rank_five_years")
    rate_of_force_sentence = rank_five_years.find_element_by_class_name(
        "third_label"
    ).get_property("innerHTML")
    clean_sentence = (
        " ".join(rate_of_force_sentence.split())
        .replace('<div class="important_num2">', "")
        .replace("</div>", "")
    )
    return clean_sentence


def get_pd_info():
    """Retrieve the rate of force ('this dept uses force at a rate higher than X other depts').
        
    Returns
    -------
    sentnce : str
       `innerHTML` of h3 inside the rank_five_years section.
    """
    pd_info = browser.find_element_by_class_name("pd_info")
    h1 = pd_info.find_element_by_class_name("biggest_hed").get_property("innerHTML")
    second_label = pd_info.find_element_by_class_name("second_label").get_property(
        "innerHTML"
    )
    patrol_area = (
        pd_info.find_element_by_class_name("town_description")
        .find_element_by_class_name("left")
        .find_element_by_class_name("town_label")
        .get_property("innerHTML")
    )

    return (h1, second_label, patrol_area)


# render the first page in case it takes a bit to load
browser.get(BASE_URL + depts_list[0]["relative_url"])
time.sleep(2)

for dept in depts_list:
    # go to page
    browser.get(BASE_URL + dept["relative_url"])

    print(f"Getting info for {dept['name']}")

    # get likelihood numbers
    # by population
    try:
        (prop, number, more_or_less) = get_likelihood_numbers("left")
        dept[prop] = number
        dept["more_or_less_pop"] = (
            more_or_less if "likely" in more_or_less else "Not found"
        )
    except:
        dept["population"] = "Not found"
        dept["more_or_less_pop"] = "Not found"
    # by arrests
    try:
        (prop, number, more_or_less) = get_likelihood_numbers("right")
        dept[prop] = number
        dept["more_or_less_arrests"] = (
            more_or_less if "likely" in more_or_less else "Not found"
        )
    except:
        dept["arrests"] = "Not found"
        dept["more_or_less_arrests"] = "Not found"

    # get no of officers that would be flagged in other cities
    try:
        (
            first_city,
            first_city_n,
            second_city,
            second_city_n,
            third_city,
            third_city_n,
        ) = get_flagging_officer_numbers()
        dept[first_city.lower().replace(" ", "_")] = first_city_n
        dept[second_city.lower().replace(" ", "_")] = second_city_n
        dept[third_city.lower().replace(" ", "_")] = third_city_n
    except:
        dept["Los Angeles".lower().replace(" ", "_")] = "Not found"
        dept["New York City".lower().replace(" ", "_")] = "Not found"
        dept["Chicago".lower().replace(" ", "_")] = "Not found"

    # get average no of officers in police dept
    try:
        ave_n = get_average_number_of_officers()
        dept["average_full_time_officers"] = ave_n.split(": ")[-1]
    except:
        dept["average_full_time_officers"] = "Not found"

    # rate of force
    try:
        rate_of_force = get_rate_of_force()
        dept["rate_of_force"] = rate_of_force
    except:
        dept["rate_of_force"] = "Not found"

    # pd info (town, county, patrol area)
    try:
        (name, county, patrol_area) = get_pd_info()
        dept["town_name"] = name
        dept["county"] = county
        dept["patrol_area"] = patrol_area
    except:
        dept["town_name"] = "Not found"
        dept["county"] = "Not found"
        dept["patrol_area"] = "Not found"

browser.close()
data = pd.DataFrame(depts_list)
data["full_url"] = BASE_URL + data["relative_url"]

data.to_csv(
    PROCESSED_DATA / f"force-nj-scrape-data-{today}.csv", encoding="utf-8", index=False
)

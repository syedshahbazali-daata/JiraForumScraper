import requests
from xextract import String
from datetime import datetime, timedelta
from lxml import html
import json
from art import *

# ASCII Art
art = text2art("Jira Forum Scraper", font="small")
print(art)

# Add the No of Days as you want
no_of_days = int(input("Please Enter No of Days: "))


def create_date_string():
    start_date = datetime.now()
    end_date = start_date - timedelta(days=no_of_days)

    return f"{end_date.strftime('%m%d%y')}_{start_date.strftime('%m%d%y')}"


file_name_slug = f"jira_forum_{create_date_string()}"


def get_recent_date(day_of_week):
    # already formatted date
    if "-" in day_of_week:
        return day_of_week
    # Yesterday
    if "yesterday" in day_of_week.lower():
        return (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")

    if "ago" in day_of_week.lower():
        # current date
        return datetime.now().strftime("%m-%d-%Y")

    # Create a dictionary to map day names to their corresponding integer values (0=Monday, 6=Sunday)
    days_of_week = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    # Get the current date
    current_date = datetime.now()

    # Find the integer value of the input day
    input_day_value = days_of_week.get(day_of_week)

    if input_day_value is not None:
        # Calculate the difference in days between the input day and the current day
        day_difference = (current_date.weekday() - input_day_value) % 7

        # Calculate the date of the most recent occurrence of the input day
        recent_date = current_date - timedelta(days=day_difference)

        # Format the date as "m-d-yyyy" and return it as a string
        formatted_date = recent_date.strftime("%m-%d-%Y")
        return formatted_date
    else:
        return "Invalid day of the week"


def days_until_date(input_date):
    # Define the format of the input date string
    date_format = "%m-%d-%Y"

    try:
        # Convert the input date string to a datetime object
        input_datetime = datetime.strptime(input_date, date_format)

        # Get the current date
        current_datetime = datetime.now()

        # Calculate the time difference between the input date and the current date
        time_difference = current_datetime - input_datetime

        # Extract the number of days from the time difference
        days_difference = time_difference.days

        return int(days_difference)
    except ValueError:
        return "Invalid date format"


# Get the Text from the Xpath
def article_scraper(article_data: list):
    def get_texts_from_xpath(xpath_of_element):
        elements = String(xpath=xpath_of_element).parse_html(page)
        links = [str(element).strip() for element in elements]
        return links

    def get_text_from_xpath(xpath_of_element):
        try:
            element = String(xpath=xpath_of_element).parse_html(page)[0]

            return str(element).strip()
        except:
            return ""

    url = article_data[0]
    article_published_date = article_data[1]
    no_of_likes = article_data[2]

    response = requests.get(url)

    page = str(response.text)

    # Get the Article ID
    try:
        article_id = url.split("/")[-1]
    except:
        print("Error in getting article id")
        article_id = url

    # Get the Article Title , User_Name , Tags , Deployment Type , Product Plan , Category , Details

    title = get_text_from_xpath('//div[@class="atl-page-title"]//h1')
    user_name = get_text_from_xpath('//a[@class="atl-avatar-name-date__username atl-author-url"]')
    tags = get_texts_from_xpath('//ul[@class="atl-tags-list"]//li/a')
    deployment_type = get_text_from_xpath('//div[@id="deployment"]//span')
    product_plan = get_text_from_xpath('//div[@id="product"]//span')
    category = get_text_from_xpath('//li[@class="atl-breadcrumbs__crumb"][4]/a')

    tree = html.fromstring(page)
    details = tree.xpath('(//div[@itemprop="text"])[1]//*')
    details = [str(detail.text).strip() for detail in details if detail.text is not None]
    details = " ".join(details).strip()

    return {
        "title": title,
        "user": user_name,
        "likes": no_of_likes,
        "date": article_published_date,
        "id": article_id,
        "category": category,
        "deployment_type": deployment_type,
        "product_plan": product_plan,
        "tags": tags,
        "details": details,
        "source_url": url
    }


# Page No
page_no = 1
keep_running = True
all_articles_data = []

for scraping_type in ["1", "2"]:

    if scraping_type == "1":
        scraping_section = "questions"
    else:
        scraping_section = "discussions"

    print(f"{scraping_section.title()} Start Scraping")

    while keep_running:
        if scraping_type == "1":
            page_url = f"https://community.atlassian.com/t5/Jira-Service-Management/qa-p/jira-service-desk-questions/page/{page_no}?sort=recent"
        else:
            page_url = f"https://community.atlassian.com/t5/Jira-Service-Management/bd-p/jira-service-desk-discussions/page/{page_no}?sort=recent"

        response = requests.get(page_url)

        if response.status_code != 200:
            print(f"Failed to fetch the page. Status code: {response.status_code}")
            break

        page_source = str(response.text)

        # total number of sections
        no_of_articles = len(String(xpath='//li[@class="atl-post-list__tile"]').parse_html(page_source))

        for single_article in range(1, no_of_articles + 1):
            article_xpath = f"(//li[@class='atl-post-list__tile'])[{single_article}]"

            # checking featured post or not

            try:
                featured_post = String(xpath=f"{article_xpath}//span[text()='Featured']").parse_html(page_source)[0]

                continue  # skip the featured post
            except:
                pass

            # article link

            base_url = "https://community.atlassian.com"
            article_link = base_url + str(
                String(xpath=f"{article_xpath}//h3/a", attr="href").parse_html(page_source)[0])
            published_date = str(
                String(xpath=f"{article_xpath}//span[@class='atl-post-metric']").parse_html(page_source)[0]).strip()

            no_of_likes = str(
                String(xpath=f"{article_xpath}//*[@data-tooltip='Likes']/..").parse_html(page_source)[0]).strip()

            # conversion
            published_date = get_recent_date(published_date)

            # days difference
            days_difference = days_until_date(published_date)

            if days_difference <= no_of_days:
                all_articles_data.append([article_link, published_date, no_of_likes])


            else:
                keep_running = False
                break

        if no_of_articles == 0:
            keep_running = False
            break

        # increment page no
        page_no += 1



        print(f"Page no {page_no} links scraped")

# Scraping the articles
all_json_response = []
print(f"Total articles Found: {len(all_articles_data)} of last {no_of_days} days")
for scraping_index, single_article_data in enumerate(all_articles_data):
    print(f"Scraping article {scraping_index + 1} of {len(all_articles_data)}")

    json_response = article_scraper(single_article_data)
    all_json_response.append(json_response)

# Saving the data in json file
with open(f"{file_name_slug}.json", "w") as f:
    json.dump(all_json_response, f, indent=4)

print("Finished scraping")

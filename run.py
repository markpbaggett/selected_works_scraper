import requests
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Add stuff we'll need later
save_path = "selected_works"
my_csv = "trace.csv"
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(executable_path=os.path.abspath("/home/mark/.virtualenvs/heather_selected_works/bin/chromedriver"),   chrome_options=chrome_options)


class SelectedWork:
    def __init__(self, line):
        self.title = line[0]
        self.url = line[1]
        self.published = line[2]
        self.state = line[3]
        self.count = line[4]

    def __repr__(self):
        return f"A selected work called {self.title}."

    def create_metadata_record(self, directory):
        driver.get(self.url)
        work_details = driver.find_element_by_css_selector("div.work-details")
        print(f"Scraping metadata for {self.title}.")
        with open(f"{save_path}/{directory}/metadata.txt", "w") as metadata:
            metadata.write(work_details.text)
        return

    def grab_pdf(self, directory):
        r = requests.get(f"{self.url}/download/")
        if r.status_code == 200:
            print(f"Downloading PDF for {self.title}.")
            with open(f"{save_path}/{directory}/stamped.pdf", 'wb') as work:
                work.write(r.content)
        return

    def create_container(self):
        dir_name = self.url.replace("http://works.bepress.com/", "").replace("/", "__")
        try:
            os.mkdir(f"{save_path}/{dir_name}")
            return dir_name
        except:
            print(f"{dir_name} with state {self.state} already exists!")
            return None


def main():
    with open(my_csv) as csv_file:
        selected_works_reader = csv.reader(csv_file, delimiter='|')
        for row in selected_works_reader:
            if row[1].startswith("http://works.bepress.com/"):
                new_work = SelectedWork(row)
                if new_work.state != "withdrawn":
                    q = new_work.create_container()
                    if q is not None:
                        new_work.grab_pdf(q)
                        new_work.create_metadata_record(q)


if __name__ == "__main__":
    main()

import requests
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import yaml
from time import sleep
from urllib3.exceptions import ProtocolError


# Add stuff we'll need later
settings = yaml.load(open("config.yml", "r"))
save_path = settings["output_directory"]
my_csv = settings["csv"]
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(executable_path=os.path.abspath(settings["chrome_path"]),   chrome_options=chrome_options)


class SelectedWork:
    def __init__(self, line):
        self.title = line[0]
        self.url = line[1]
        self.published = line[2]
        self.state = line[3]
        self.count = line[4]
        self.statuscode = 404

    def __repr__(self):
        return f"A selected work called {self.title}."

    def create_metadata_record(self, directory):
        if self.statuscode == 200:
            try:
                driver.get(self.url)
                work_details = driver.find_element_by_css_selector("div.work-details")
                print(f"Scraping metadata for {self.title} at {directory}.")
                with open(f"{save_path}/{directory}/metadata.txt", "w") as metadata:
                    metadata.write(work_details.text)
            except (ProtocolError, AttributeError):
                with open(f"error.log", "a") as error_log:
                    error_log.write(f"Connection refused with {self.statuscode} on metadata"
                                    f" for {directory} aka {self.title}.")
            except:
                with open(f"error.log", "a") as error_log:
                    error_log.write(f"Connection refused with {self.statuscode} on metadata"
                                    f" for {directory} aka {self.title}.")
                sleep(3)
                self.create_metadata_record(directory)
        return

    def grab_pdf(self, directory):
        r = requests.get(f"{self.url}/download/")
        if r.headers["Content-Type"] == "application/pdf; charset=utf-8":
            try:
                if r.status_code == 200:
                    self.statuscode = r.status_code
                    print(f"Downloading PDF for {self.title} at {directory}.")
                    with open(f"{save_path}/{directory}/stamped.pdf", 'wb') as work:
                        work.write(r.content)
            except requests.exceptions.ConnectionError:
                self.statuscode = r.status_code
                with open(f"error.log", "a") as error_log:
                    error_log.write(f"Connection refused with {r.status_code} on pdf for {directory} aka {self.title}.")
                sleep(3)
                self.grab_pdf(directory)
            except requests.ConnectionError as e:
                self.statuscode = r.status_code
                with open("error.log", "a") as error_log:
                    error_log.write(f"Failed as {e}. Connection refused with {r.status_code} on pdf for {directory} aka {self.title}.")
        else:
            with open(f"error.log", "a") as error_log:
                error_log.write(f"No PDF for {directory}.\n")
        return

    def create_container(self):
        dir_name = self.url.replace("http://works.bepress.com/", "").replace("/", "__")
        try:
            print(f"Creating directory {dir_name}.")
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

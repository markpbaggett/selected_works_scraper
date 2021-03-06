import requests
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import yaml
from time import sleep
from urllib3.exceptions import ProtocolError, LocationValueError
from subprocess import call


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
        self.bad_record = False
        self.dir_name = ""

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
                log_file.write(f"\tSuccessfully harvested metadata for {self.title} at {directory}.\n")
            except (ProtocolError, AttributeError):
                self.bad_record = True
                log_file.write(f"\tConnection refused with {self.statuscode} on metadata for {directory} "
                               f"aka {self.title}.\n")
            except:
                log_file.write(f"\tConnection refused with {self.statuscode} on metadata for {directory} "
                               f"aka {self.title}.\n")
                sleep(3)
                self.create_metadata_record(directory)
        return

    def grab_pdf(self, directory):
        try:
            r = requests.get(f"{self.url}/download/", verify=False)
            # print(r.headers)
            content_type = None
            if r.headers["Content-Type"]:
                content_type = r.headers["Content-Type"]
            if content_type == "application/pdf; charset=utf-8":
                try:
                    if r.status_code == 200:
                        self.statuscode = r.status_code
                        print(f"Downloading PDF for {self.title} at {directory}.")
                        with open(f"{save_path}/{directory}/stamped.pdf", 'wb') as work:
                            work.write(r.content)
                        log_file.write(f"\tSuccessfully downloaded PDF for {self.title} at {directory}.\n")
                    else:
                        print(f"\tCould not download PDF.  Failed with {r.status_code}.\n")
                        self.bad_record = True
                        log_file.write(f"\tFailed to download PDF for {self.title} with {r.status_code}.\n")
                except requests.exceptions.ConnectionError:
                    self.statuscode = r.status_code
                    self.bad_record = True
                    log_file.write(f"\tConnection refused with {r.status_code} on pdf for {directory} "
                                   f"aka {self.title}.\n")
                    sleep(3)
                    self.grab_pdf(directory)
                except requests.ConnectionError as e:
                    self.statuscode = r.status_code
                    self.bad_record = True
                    log_file.write(f"\tFailed as {e}. Connection refused with {r.status_code} on pdf for {directory} "
                                   f"aka {self.title}.\n")
            else:
                log_file.write(f"\tNo PDF for {directory}.\n")
                self.bad_record = True
        except requests.exceptions.ConnectionError:
            log_file.write(f"\tCould not download PDF for {directory}. Requests ConnectionError exception.\n")
            self.bad_record = True
        except LocationValueError:
            log_file.write(f"\tCould not download PDF for {directory}. No host specfied exception.\n")
            self.bad_record = True
        except KeyError:
            log_file.write(f"\tCould not download PDF for {directory}. Key Error.\n")
            self.bad_record = True
        return

    def create_container(self):
        self.dir_name = self.url.replace("http://works.bepress.com/", "").replace("/", "__")
        try:
            os.mkdir(f"{save_path}/{self.dir_name}")
            print(f"Creating directory {self.dir_name}.")
            log_file.write(f"Created directory for {self.dir_name}.\n")
            return self.dir_name
        except:
            print(f"{self.dir_name} with state {self.state} already exists!")
            return None

    def cleanup_work(self):
        call(f"rm -rf {save_path}/{self.dir_name}/", shell=True)
        log_file.write(f"\tRemoving directory {self.dir_name}.\n")


class LogFile:
    def __init__(self, name):
        self.name = name

    def write(self, message):
        with open(self.name, "a") as log:
            log.write(message)
        return


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
                        if new_work.bad_record is True:
                            new_work.cleanup_work()


# Our Log
log_file = LogFile("works.log")

if __name__ == "__main__":
    main()

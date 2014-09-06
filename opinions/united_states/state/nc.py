"""Scraper for North Carolina Supreme Court
CourtID: nc
Court Short Name: N.C.
Reviewer:
History:
    2014-05-01: Created by Brian Carver
    2014-08-04: Rewritten by Jon Andersen with complete backscraper
"""

import re
from datetime import date
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://appellate.nccourts.org/opinions/?c=sc&year=%s' % date.today().year
        self.back_scrape_iterable = range((date.today().year - 1), 1997, -1)
        self.my_download_urls = []
        self.my_case_names = []
        self.my_docket_numbers = []
        self.my_summaries = []
        self.my_neutral_citations = []
        self.my_precedential_statuses = []

    def _get_case_dates(self):
        case_dates = []
        case_date = None
        precedential_status = "Published"
        date_cleaner = "\d+ \w+ [12][90]\d\d"
        path = '//table//tr'
        for row_el in self.html.xpath(path):
            # Examine each row. If it contains the date, we set that as
            # the current date. If it contains a case, we parse it.
            try:
                date_nodes = row_el.xpath('.//strong/text()')
                date_str = date_nodes[0]
                if date_nodes:
                    date_str = re.search(date_cleaner,
                                         date_str, re.MULTILINE).group()
                    case_date = datetime.strptime(date_str, '%d %B %Y').date()
                    # When a new date header appears, switch to Precedential
                    precedential_status = "Published"
                    continue     # Row contained just the date, move on
            except:
                # Not a date header
                pass

            path = "./td[contains(., 'Unpublished Opinions - Rule 30e')]"
            if row_el.xpath(path):
                precedential_status = "Unpublished"
                continue   # When this header appears, switch to Nonprecedential

            if (precedential_status == "Published"):
                urls = row_el.xpath('./td/span/span[1]/@onclick')
                # Like: viewOpinion("http://appellate.nccourts.org/opinions/?c=1&amp;pdf=31511")
                if (len(urls) != 1 or urls[0].find('viewOpinion') != 0):
                    continue    # Only interested in cases with a download link
                download_url = urls[0][13:-2]

                path = "./td/span/span[contains(@class,'title')]/text()"
                txt = row_el.xpath(path)[0]
                (case_name, neutral_cit, dock_num) = self.parse_title(txt)

                summary = ""
                path = "./td/span/span[contains(@class,'desc')]/text()"
                summaries = row_el.xpath(path)
                if (len(summaries) == 1):
                    # Not all cases have a summary
                    summary = summaries[0]

                if (case_name.strip() == ""):
                    continue    # A few cases are missing a name

                case_dates.append(case_date)
                self.my_download_urls.append(download_url)
                self.my_case_names.append(case_name)
                self.my_docket_numbers.append(dock_num)
                self.my_summaries.append(summary)
                self.my_neutral_citations.append(neutral_cit)
                self.my_precedential_statuses.append(precedential_status)

            elif (precedential_status == "Unpublished"):
                for span in row_el.xpath('./td/span'):
                    if 'onclick' not in span.attrib.keys():
                        continue
                    download_url = span.attrib['onclick'][13:-2]

                    txt = span.text_content().strip()
                    (case_name, neutral_cit, dock_num) = self.parse_title(txt)
                    if (case_name.strip() == ""):
                        continue    # A few cases are missing a name
                    case_dates.append(case_date)
                    self.my_download_urls.append(download_url)
                    self.my_case_names.append(case_name)
                    self.my_docket_numbers.append(dock_num)
                    self.my_summaries.append("")
                    self.my_neutral_citations.append(neutral_cit)
                    self.my_precedential_statuses.append(precedential_status)

        return case_dates

    # Parses case titles like:
    # Fields v. Harnett Cnty., 367 NC 12 (13-761)
    # Clark v. Clark,  (13-612)
    def parse_title(self, txt):
        name_and_citation = txt.rsplit('(', 1)[0].strip()
        dock_num = txt.rsplit('(', 1)[1].strip().strip(')')
        case_name = name_and_citation.rsplit(",", 1)[0].strip()
        neutral_cit = name_and_citation.rsplit(",", 1)[1].strip()
        return (case_name, neutral_cit, dock_num)

    def _get_download_urls(self):
        return self.my_download_urls

    def _get_case_names(self):
        return self.my_case_names

    def _get_docket_numbers(self):
        return self.my_docket_numbers

    def _get_summaries(self):
        return self.my_summaries

    def _get_neutral_citations(self):
        return self.my_neutral_citations

    def _get_precedential_statuses(self):
        return self.my_precedential_statuses

    def _download_backwards(self, year):
        self.url = 'http://appellate.nccourts.org/opinions/?c=sc&year=%s' % year
        self.html = self._download()

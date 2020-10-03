from selenium import webdriver
import argparse
from scrap import UdmScraper

def parse_command_line_args():
    parser = argparse.ArgumentParser(description="""
        parse udemy search parameters
        """)

    parser.add_argument('--keyword', type=str, required=True, help="""
        enter the keyword you want to search for
        """)

    parser.add_argument('--pages', type=int, required=True, help="""
        enter the number of pages you want to search
        """)

    return vars(parser.parse_args())

if __name__ == "__main__":

    search_keys = parse_command_line_args()

    # initialize selenium webdriver - pass latest chromedriver path to webdriver.Chrome()
    driver = webdriver.Chrome('./chromedriver')
    main_link = 'https://www.udemy.com'
    driver.get(main_link)

    UdmScraper = UdmScraper(driver, **search_keys)
    UdmScraper.set_lang()
    UdmScraper.scrap_links()
    UdmScraper.make_Df()
    UdmScraper.preprocessing()
    UdmScraper.saveDf()



import pandas as pd
import time
import sqlalchemy
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import psycopg2
import lxml
import requests

class UdmScraper():
    def __init__(self, driver, **kwargs):
        self.driver = driver
        self.keyword = kwargs['keyword']
        self.pages = kwargs['pages']

    def set_lang(self):
        driver = self.driver
        driver.implicitly_wait(5)
        language = driver.find_element_by_css_selector('option[value="en_US"]')
        language.click()
        driver.implicitly_wait(5)
        time.sleep(1)

    def scrap_links(self):
        driver = self.driver
        keyword = self.keyword
        pages = self.pages

        for page in range(1, pages+1):
            page_link = "https://www.udemy.com/courses/{}/?p={}".format(keyword, page)
            driver.get(page_link)
            driver.implicitly_wait(10)
            course_link_elements = driver.find_elements_by_css_selector(
                '.course-list--container--3zXPS > .popover--popover--t3rNO.popover--popover-hover--14ngr > a')
            print('강의 링크를 수집중입니다. (현재페이지에서 {}개 링크 수집, 진행률 : {}/{})'.format(len(course_link_elements), page, pages))
            # element ->  link string으로 변경
            course_links = [link.get_attribute('href') for link in course_link_elements]
        print('강의 링크를 모두 수집하여 크롬 드라이브를 종료합니다.')
        driver.quit()
        # links -> csv 파일로 저장
        course_links = pd.DataFrame(course_links, columns=['link'])
        course_links.to_csv('links_{}.csv'.format(keyword))


    def make_Df(self):
        keyword = self.keyword
        titles = []
        subtitles = []
        stars = []
        ratings = []
        enrolls = []
        links = []

        course_links = pd.read_csv('links_{}.csv'.format(keyword))

        for course_link in course_links['link']:
            headers = {"Accept-Language": "en-US,en;q=0.5"}
            html = requests.get(course_link, headers=headers)
            soup = BeautifulSoup(html.text, 'lxml')
            try:
                print('title :', soup.select_one('.udlite-heading-xl.clp-lead__title').get_text())
                titles.append(soup.select_one('.udlite-heading-xl.clp-lead__title').get_text())
                print('subtitle :', soup.select_one('.udlite-text-md.clp-lead__headline').get_text())
                subtitles.append(soup.select_one('.udlite-text-md.clp-lead__headline').get_text())
                print('enroll :', soup.select_one('div[data-purpose="enrollment"]').get_text())
                enrolls.append(soup.select_one('div[data-purpose="enrollment"]').get_text())
                print('star :', soup.select_one('span.udlite-heading-sm.star-rating--rating-number--3lVe8').get_text())
                stars.append(soup.select_one('span.udlite-heading-sm.star-rating--rating-number--3lVe8').get_text())
                print('rating :', soup.select_one('span.star-rating--star-wrapper--2eczq').next_sibling)
                ratings.append(soup.select_one('span.star-rating--star-wrapper--2eczq').next_sibling)
                links.append(course_link)

                udemy_df = pd.DataFrame(list(zip(titles, subtitles, enrolls, stars, ratings, links)), columns= \
                    ['Title', 'Summary', 'Enrollment', 'Stars', 'Rating', 'Link'])
                print('데이터 프레임을 완성했습니다. csv파일에 추가합니다.')
                udemy_df.to_csv('udemy_df_{}.csv'.format(keyword), index=False, mode='w')
                print('파일을 수정했습니다.')

            except Exception as e:
                print(course_link)
                print('수집을 실패했습니다. - ', e)
                continue

            print('데이터를 생성하고 있습니다.(진행률 : {}/{})'.format(len(udemy_df), len(course_links)))

    def preprocessing(self):
        keyword = self.keyword
        udemy_df = pd.read_csv('udemy_df_{}.csv'.format(keyword))
        print('문자 타입 전처리를 시작합니다.')
        udemy_df['Title'] = [str(title.replace('\n', '')) for title in udemy_df['Title']]
        udemy_df['Summary'] = [str(summary.replace('\n', '')) for summary in udemy_df['Summary']]
        udemy_df['Enrollment'] = [int(enroll.replace(',', '').replace('\n', '').replace('student', '').replace('s', ''))
                                  for enroll in udemy_df['Enrollment']]
        udemy_df['Stars'] = [float(star) for star in udemy_df['Stars']]
        udemy_df['Rating'] = [int(rating[2:-8].strip().replace(',', '')) for rating in udemy_df['Rating']]
        print('문자 타입 전처리가 완료되었습니다.')
        udemy_df.to_csv('udemy_df_{}.csv'.format(keyword), index=False, mode='w')

    def saveDf(self):
        keyword = self.keyword
        udemy_df = pd.read_csv('udemy_df_{}.csv'.format(keyword))

        # postgresql 서버 DB와 연결합니다.
        engine = create_engine("postgresql://postgres:0000@localhost:5433/postgres")
        engine.execute("DROP TABLE IF EXISTS public.udemy_class_test_{};".format(keyword))
        udemy_df.to_sql(name='udemy_{}'.format(keyword),
                        con=engine,
                        schema='public',
                        if_exists='replace',
                        dtype={
                            'title': sqlalchemy.types.TEXT(),
                            'summary': sqlalchemy.types.TEXT(),
                            'enrollment': sqlalchemy.types.INTEGER(),
                            'stars': sqlalchemy.types.FLOAT(),
                            'rating': sqlalchemy.types.INTEGER(),
                            'link': sqlalchemy.types.Text()
                        })
        print('postgreSQL(:5433) 서버에 데이터 전송을 완료하였습니다.')

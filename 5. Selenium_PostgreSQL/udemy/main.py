from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
#from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import sqlalchemy
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import psycopg2
import lxml
import requests
import os

#option = Options()
# 알림창 끄기
option = webdriver.ChromeOptions()
option.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 2
})

#option.add_argument('headless')
#option.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
option.add_argument('disable-gpu')
option.add_argument('disable-infobars')

def StartScrap(keyword, pages):
    global drive
    drive = webdriver.Chrome(options=option, executable_path=r'/Users/swsong/PycharmProjects/scrapper/chromedriver')
    main_link = 'https://www.udemy.com'
    drive.get(main_link)
    drive.implicitly_wait(10)
    language = drive.find_element_by_css_selector('option[value="en_US"]')
    language.click()
    drive.implicitly_wait(5)
    return ScrapLinks(keyword, pages)

def ScrapLinks(keyword, pages):
    global links
    links = []
    for page in range(1,pages):
        key_link = "https://www.udemy.com/courses/{}/?p={}".format(keyword,page)
        drive.get(key_link)
        drive.implicitly_wait(10)
        course_links = drive.find_elements_by_css_selector('.course-list--container--3zXPS > .popover--popover--t3rNO.popover--popover-hover--14ngr > a')
        print('강의 링크를 수집중입니다. (현재페이지에서 {}개 링크 수집, 진행률 : {}/{})'.format(len(course_links),page,pages-1))
        for i in range(len(course_links)):
            links.append(course_links[i].get_attribute('href'))
    print('강의 링크를 모두 수집하여 크롬 드라이브를 종료합니다.')
    drive.quit()
    list_df = pd.DataFrame(links, columns=['list'])
    list_df.to_csv('links', index=False)
    return makeDf()

def makeDf(links):
    titles = []
    subtitles = []
    stars = []
    ratings = []
    enrolls = []
    link_list = []
    i = 0
    links =  pd.read_csv('{}'.format(links))
    for course_link in links['list']:
        html = requests.get(course_link)
        soup = BeautifulSoup(html.text, 'lxml')
        try:
            print('title :',soup.select_one('.udlite-heading-xl.clp-lead__title').get_text())
            titles.append(soup.select_one('.udlite-heading-xl.clp-lead__title').get_text())
            print('subtitle :',soup.select_one('.udlite-text-md.clp-lead__headline').get_text())
            subtitles.append(soup.select_one('.udlite-text-md.clp-lead__headline').get_text())
            print('enroll :',soup.select_one('div[data-purpose="enrollment"]').get_text())
            enrolls.append(soup.select_one('div[data-purpose="enrollment"]').get_text())
            print('star :',soup.select_one('span.udlite-heading-sm.star-rating--rating-number--3lVe8').get_text())
            stars.append(soup.select_one('span.udlite-heading-sm.star-rating--rating-number--3lVe8').get_text())
            print('rating :',soup.select_one('span.star-rating--star-wrapper--2eczq.star-rating--dark-background--Rqadv').next_sibling)
            ratings.append(soup.select_one('span.star-rating--star-wrapper--2eczq.star-rating--dark-background--Rqadv').next_sibling)
            link_list.append(course_link)
            global udemy_df
            udemy_df = pd.DataFrame(list(zip(titles, subtitles, enrolls, stars, ratings, link_list)), columns= \
                ['Title', 'Summary', 'Enrollment', 'Stars', 'Rating', 'Link'])
            print('데이터 프레임을 완성했습니다. csv파일에 추가합니다.')
            udemy_df.to_csv('udemy_df_temp.csv', index=False, mode='w')
            print('파일을 수정했습니다.')

        except Exception as e:
            print(course_link)
            print('수집을 실패했습니다. - ', e)
            continue
        i += 1
        print('데이터를 생성하고 있습니다.(진행률 : {}/{})'.format(i,len(links)))


    # udemy_df 정렬

    preprocessing()

def preprocessing(keyword):
    udemy_df = pd.read_csv(keyword)
    print('문자 타입 전처리를 시작합니다.')
    udemy_df['Title'] = [str(title.replace('\n','')) for title in udemy_df['Title']]
    udemy_df['Summary'] = [str(summary.replace('\n','')) for summary in udemy_df['Summary']]
    udemy_df['Enrollment'] = [int(enroll[:-10].replace(',','').replace('\n','')) for enroll in udemy_df['Enrollment']]
    udemy_df['Stars'] = [float(star) for star in udemy_df['Stars']]
    udemy_df['Rating'] = [int(rating[2:-8].strip().replace(',','')) for rating in udemy_df['Rating']]
    print('문자 타입 전처리가 완료되었습니다.')
    saveDf(udemy_df)

def saveDf(udemy_df):
    engine = create_engine("postgresql://postgres:0000@localhost:5433/postgres")
    engine.execute("DROP TABLE IF EXISTS public.udemy_tech;")
    udemy_df.to_sql(name='udemy_tech',
                    con = engine,
                    schema = 'public',
                    if_exists= 'replace',
                    dtype = {
                        'title': sqlalchemy.types.TEXT(),
                        'summary': sqlalchemy.types.TEXT(),
                        'enrollment': sqlalchemy.types.INTEGER(),
                        'stars': sqlalchemy.types.FLOAT(),
                        'rating': sqlalchemy.types.INTEGER(),
                        'link': sqlalchemy.types.Text()
                    })
    print('postgreSQL(:5433) 서버에 데이터 전송을 완료하였습니다.')

if __name__ == '__main__':
    #keyword = input('검색할 키워드를 입력하세요 : ')
    #pages = int(input('검색할 페이지 수를 입력하세요 : '))
    #StartScrap(keyword, pages)
    #file = input('탐색할 링크 파일 경로를 입력하세요 : ')
    #makeDf(file)
    df = input('정제할 데이터 경로를 입력하세요 : ')
    preprocessing(df)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/

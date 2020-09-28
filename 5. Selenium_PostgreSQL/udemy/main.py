from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import time
import sqlalchemy
from sqlalchemy import create_engine
import psycopg2

def StartScrap(keyword, pages):
    global drive
    drive = webdriver.Chrome(executable_path=r'/Users/swsong/PycharmProjects/scrapper/chromedriver')
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
    makeDf()

def makeDf():
    titles = []
    subtitles = []
    stars = []
    ratings = []
    enrolls = []
    i = 0
    for course_link in links:
        drive.get(course_link)
        wait = WebDriverWait(drive, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".udlite-text-md.clp-lead__headline")))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".styles--rating-wrapper--5a0Tr")))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-purpose="enrollment"]')))

        titles.append(drive.find_element_by_css_selector('.udlite-heading-xl.clp-lead__title').text)
        subtitles.append(drive.find_element_by_css_selector('.udlite-text-md.clp-lead__headline').text)
        temp_, star_, rating_ = drive.find_element_by_css_selector('.styles--rating-wrapper--5a0Tr').text.split('\n')
        stars.append(star_)
        ratings.append(rating_)
        enrolls.append(drive.find_element_by_css_selector('div[data-purpose="enrollment"]').text)
        i += 1
        print('데이터를 생성하고 있습니다.(진행률 : {}/{})'.format(i,len(links)))
    global udemy_df
    udemy_df = pd.DataFrame(list(zip(titles,subtitles,enrolls,stars,ratings,links)), columns = \
        ['Title','Summary','Enrollment','Stars','Rating','Link'])
    # udemy_df 정렬

    preprocessing()

def preprocessing():
    print('문자 타입 전처리를 시작합니다.')
    udemy_df['Rating'] = [int(rating[1:-8].strip().replace(',','')) for rating in udemy_df['Rating']]
    udemy_df['Enrollment'] = [int(enroll[:-9].replace(',','')) for enroll in udemy_df['Enrollment']]
    udemy_df['Stars'] = [float(star) for star in udemy_df['Stars']]
    print('문자 타입 전처리가 완료되었습니다.')
    saveDf()

def saveDf():
    engine = create_engine("postgresql://postgres:0000@localhost:5433/postgres")
    engine.execute("DROP TABLE IF EXISTS public.udemy_tech;")
    udemy_df.to_sql(name='udemy_tech',
                    con = engine,
                    schema = 'public',
                    if_exists= 'replace',
                    dtype = {
                        'Title': sqlalchemy.types.TEXT(),
                        'Summary': sqlalchemy.types.TEXT(),
                        'Enrollment': sqlalchemy.types.INTEGER(),
                        'Stars': sqlalchemy.types.FLOAT(),
                        'Rating': sqlalchemy.types.INTEGER(),
                        'Link': sqlalchemy.types.Text()
                    })
    print('postgreSQL(:5433) 서버에 데이터 전송을 완료하였습니다.')
    drive.quit()

if __name__ == '__main__':
    keyword = input('검색할 키워드를 입력하세요 : ')
    pages = int(input('검색할 페이지 수를 입력하세요 : '))
    StartScrap(keyword, pages)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

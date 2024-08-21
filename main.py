import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import boto3
import time

def handler(event=None, context=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = "/opt/chrome/chrome"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
    chrome_options.add_argument('window-size=1392x1150')
    chrome_options.add_argument("disable-gpu")

    service = Service("/opt/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get('https://www.38.co.kr/html/fund/index.htm?o=k')

    name =  []
    industry = []
    representative = []
    revenue = [] #매출액
    netProfit = [] #순이익
    totalOfferedShares = [] #총공모주식수

    cnt = 0 # 15 번째 까지만 들고오자
    while(cnt < 15):
        for i in range(1, 31):
            #각 공모주 별 디테일 페이지 조회
            detail = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[1]/a'.format(i)
            detail_button = driver.find_element(By.XPATH, detail)
            detail_button.click()
            time.sleep(1)

            # 각 속성별 태그 정의
            nameTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[2]/tbody/tr[1]/td[2]/a/b/font'
            industryTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[2]/tbody/tr[3]/td[2]'
            representativeTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[2]/tbody/tr[4]/td[2]'
            revenueTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[2]/tbody/tr[8]/td[2]'
            netProfitTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[2]/tbody/tr[9]/td[2]'
            totalOfferedSharesTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[1]/td[2]'

            try:
                nameText = driver.find_element(By.XPATH, nameTag)
                industryText = driver.find_element(By.XPATH, industryTag)
                representativeText = driver.find_element(By.XPATH, representativeTag)
                revenueText = driver.find_element(By.XPATH, revenueTag)
                netProfitText = driver.find_element(By.XPATH, netProfitTag)
                totalOfferedSharesText = driver.find_element(By.XPATH, totalOfferedSharesTag)

                # 가져온 데이터 배열에 붙이기
                name.append(nameText.text)
                industry.append(industryText.text)
                representative.append(representativeText.text)
                revenue.append(revenueText.text)
                netProfit.append(netProfitText.text)
                totalOfferedShares.append(totalOfferedSharesText.text)

                driver.back()
            except NoSuchElementException:
                break

        try:
            next_button = driver.find_element(By.LINK_TEXT, "[다음]")
            next_button.click()
            cnt += 1
        except NoSuchElementException:
            break

    driver.close()
    cols = ['name', 'industry', 'representative', 'revenue', 'netProfit', 'totalOfferedShares']

    data = pd.DataFrame(columns = cols)
    data['name'] = name
    data['industry'] = industry
    data['representative'] = representative
    data['revenue'] = revenue
    data['netProfit'] = netProfit
    data['totalOfferedShares'] = totalOfferedShares

    data =  data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)


    # 임시 파일 경로 설정
    file_path = '/tmp/ipo_detail.csv'
    data.to_csv(file_path, index=False, encoding='utf-8-sig')

    # S3 버킷에 업로드
    s3 = boto3.client('s3')
    bucket = 'ipo-alarm-project'

    s3.upload_file(file_path, bucket, 'ipo_detail.csv')

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "success"

            }
        ),
    }

if __name__ == '__main__':
    handler()

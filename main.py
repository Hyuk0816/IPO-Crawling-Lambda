import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import boto3

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

    driver.get('https://www.38.co.kr/html/fund/index.htm?o=nw')

    name = []
    listingDate = []
    currentPrice = []
    changeFromPreviousDay = [] #전일비
    offeringPrice  = [] #공모가
    changeRateFromOfferingPrice  = [] #공모가대비 등락률
    openingPrice = [] #시초가
    openingPriceToOfferingPrice  = [] # 시초/공모)
    closingPriceOnFirstDay = [] #첫날종가

    cnt = 0 # 15 번째 까지만 들고오자
    while(cnt < 25):
        for i in range(1, 21):
            #다음 누르기 버튼
            next_button = driver.find_element(By.LINK_TEXT, "[다음]")

            #각 속성별 태그 정의
            nameTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[1]'.format(i)
            listingDateTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[2]'.format(i)
            currentPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[3]'.format(i)
            changeFromPreviousDayTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[4]'.format(i)
            offeringPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[5]'.format(i)
            changeRateFromOfferingPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[6]'.format(i)
            openingPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[7]'.format(i)
            openingPriceToOfferingPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[8]'.format(i)
            closingPriceOnFirstDayTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[9]'.format(i)

            try:
                nameText = driver.find_element(By.XPATH, nameTag).text
                listingDateText = driver.find_element(By.XPATH, listingDateTag).text
                currentPriceText = driver.find_element(By.XPATH, currentPriceTag).text
                changeFromPreviousDayText = driver.find_element(By.XPATH, changeFromPreviousDayTag).text
                offeringPriceText = driver.find_element(By.XPATH, offeringPriceTag).text
                changeRateFromOfferingPriceText = driver.find_element(By.XPATH, changeRateFromOfferingPriceTag).text
                openingPriceText = driver.find_element(By.XPATH, openingPriceTag).text
                openingPriceToOfferingPriceText = driver.find_element(By.XPATH, openingPriceToOfferingPriceTag).text
                closingPriceOnFirstDayText = driver.find_element(By.XPATH, closingPriceOnFirstDayTag).text

                # 가져온 데이터 배열에 붙이기
                name.append(nameText)
                listingDate.append(listingDateText)
                currentPrice.append(currentPriceText)
                changeFromPreviousDay.append(changeFromPreviousDayText)
                offeringPrice.append(offeringPriceText)
                changeRateFromOfferingPrice.append(changeRateFromOfferingPriceText)
                openingPrice.append(openingPriceText)
                openingPriceToOfferingPrice.append(openingPriceToOfferingPriceText)
                closingPriceOnFirstDay.append(closingPriceOnFirstDayText)


            except NoSuchElementException:
                break

        try:
            next_button = driver.find_element(By.LINK_TEXT, "[다음]")
            next_button.click()
            cnt += 1
        except NoSuchElementException:
            break

    driver.close()
    cols = ['name', 'listingDate', 'currentPrice', 'changeFromPreviousDay', 'offeringPrice', 'changeRateFromOfferingPrice', 'openingPrice', 'openingPriceToOfferingPrice','closingPriceOnFirstDay']

    data = pd.DataFrame(columns=cols)

    data['name'] = name
    data['listingDate'] = listingDate
    data['currentPrice'] = currentPrice
    data['changeFromPreviousDay'] = changeFromPreviousDay
    data['offeringPrice'] = offeringPrice
    data['changeRateFromOfferingPrice'] = changeRateFromOfferingPrice
    data['openingPrice'] = openingPrice
    data['openingPriceToOfferingPrice'] = openingPriceToOfferingPrice
    data['closingPriceOnFirstDay'] = closingPriceOnFirstDay

    data =  data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # listingDate의 /를 -로 변경
    data['listingDate'] = data['listingDate'].str.replace('/', '-', regex=False)

    # %가 들어가는 모든 컬럼에서 % 제거
    percentage_columns = ['changeFromPreviousDay', 'changeRateFromOfferingPrice', 'openingPriceToOfferingPrice']
    for col in percentage_columns:
        data[col] = data[col].str.replace('%', '', regex=False)

    # 임시 파일 경로 설정
    file_path = '/tmp/listing_shares.csv'
    data.to_csv(file_path, index=False, encoding='utf-8-sig')

    # S3 버킷에 업로드
    s3 = boto3.client('s3')
    bucket = 'ipo-alarm-project'

    s3.upload_file(file_path, bucket, 'listing_shares.csv')

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

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

    driver.get("https://www.38.co.kr/html/fund/index.htm?o=k")

    name = [] #td1
    date = [] #td2
    confirmPrice = [] #td3
    IPOPrice = [] #td4
    competitionRate = [] #td5
    securities = [] #td6

    cnt = 0 # 15 번째 까지만 들고오자
    while(cnt < 15):
        for i in range(1, 31):
            # 각 속성별 태그 정의
            nameTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[1]'.format(i)
            dateTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[2]'.format(i)
            confirmPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[3]'.format(i)
            IPOPriceTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[4]'.format(i)
            competitionRateTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[5]'.format(i)
            securitiesTag = '/html/body/table[3]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[4]/tbody/tr[2]/td/table/tbody/tr[{0}]/td[6]'.format(i)

            try:
                # tr 은 다음 행 30번까지 있다
                nameText = driver.find_element(By.XPATH, nameTag)
                dateText = driver.find_element(By.XPATH, dateTag)
                confirmPriceText = driver.find_element(By.XPATH, confirmPriceTag)
                IPOPriceText = driver.find_element(By.XPATH, IPOPriceTag)
                competitionRateText = driver.find_element(By.XPATH, competitionRateTag)
                securitiesText = driver.find_element(By.XPATH, securitiesTag)

                # 가져온 데이터 배열에 붙이기
                name.append(nameText.text)
                date.append(dateText.text)
                confirmPrice.append(confirmPriceText.text)
                IPOPrice.append(IPOPriceText.text)
                competitionRate.append(competitionRateText.text)
                securities.append(securitiesText.text)

            except NoSuchElementException:
                break

        try:
            next_button = driver.find_element(By.LINK_TEXT, "[다음]")
            next_button.click()
            cnt += 1
        except NoSuchElementException:
            break

    driver.close()
    cols = ['name', 'date', 'confirmPrice', 'IPOPrice', 'competitionRate', 'securities']

    data = pd.DataFrame(columns=cols)
    data['name'] = name
    data['date'] = date
    data['confirmPrice'] = confirmPrice
    data['IPOPrice'] = IPOPrice
    data['competitionRate'] = competitionRate
    data['securities'] = securities

    # date 컬럼을 start_date와 end_date로 나누기
    data[['start_date', 'end_date']] = data['date'].str.split('~', expand=True)
    data.drop(columns=['date'], inplace=True)

    # 현재 연도 가져오기
    current_year = datetime.now().year

    # start_date에 10:00 추가
    data['start_date'] = data['start_date'].str.strip() + ' 10:00'

    # end_date 수정: 원래 연도와 월, 일을 유지하고 현재 연도와 16:00 추가
    data['end_date'] = data['end_date'].str.strip()
    data['end_date'] = data.apply(lambda row: f"{row['start_date'][:4]}.{row['end_date']} 16:00", axis=1)
   # data['end_date'] = data['end_date'].apply(lambda x: f"{current_year}.{x[0:]} 16:00")

    # 공백 제거
    data =  data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
   # data = data.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # 임시 파일 경로 설정
    file_path = '/tmp/ipo_data.csv'
    data.to_csv(file_path, index=False, encoding='utf-8-sig')

    # S3 버킷에 업로드
    s3 = boto3.client('s3')
    bucket = 'ipo-data-csv'

    s3.upload_file(file_path, bucket, 'ipo_data.csv')

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

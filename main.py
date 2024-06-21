from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import requests
from bs4 import BeautifulSoup

app = FastAPI()

class LottoData(BaseModel):
    date: str
    num1: int
    num2: int
    num3: int
    num4: int
    num5: int
    num6: int
    bonus: int

def load_lotto_data():
    return pd.read_csv('lotto_result.csv', encoding='utf-8-sig')

def get_latest_lotto_data():
    url = 'https://dhlottery.co.kr/common.do?method=main'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    latest_draw_no = int(soup.find('strong', id='lottoDrwNo').text)
    latest_date = soup.find('p', class_='desc').text.strip().split(' ')[0]

    numbers = [int(num.text) for num in soup.select('span.ball_645')]
    num1, num2, num3, num4, num5, num6, bonus = numbers[:6], numbers[6]

    # 수정함: numpy 타입을 int로 변환
    latest_lotto_data = {
        'date': latest_date, 
        'num1': int(num1), 
        'num2': int(num2),
        'num3': int(num3),
        'num4': int(num4),
        'num5': int(num5),
        'num6': int(num6),
        'bonus': int(bonus),
    }

    return latest_lotto_data

def update_lotto_data():
    data = load_lotto_data()
    last_date = data['date'].max()

    latest_lotto_data = get_latest_lotto_data()
    latest_date = latest_lotto_data['date']

    if latest_date > last_date:
        new_row = pd.DataFrame([latest_lotto_data])
        updated_data = pd.concat([data, new_row], ignore_index=True)
        updated_data.to_csv('lotto_result.csv', index=False, encoding='utf-8-sig')
        print(f"최신 로또 번호가 업데이트 되었습니다. 새로운 날짜: {latest_date}")
    else:
        print("최신 날짜 로또번호가 이미 포함되어 있습니다.")

def calculate_probabilities(counter):
    total = sum(counter.values())
    return {num: count / total for num, count in counter.items()}

def generate_lotto_number():
    data = load_lotto_data()
    lotto_columns = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    num1_counts = Counter(data['num1'])
    
    transition_counts = {col: defaultdict(Counter) for col in lotto_columns[1:]}
    for _, row in data.iterrows():
        for i in range(len(lotto_columns) - 1):
            current_col = lotto_columns[i]
            next_col = lotto_columns[i + 1]
            transition_counts[next_col][row[current_col]][row[next_col]] += 1

    # print(transition_counts)

    lotto_numbers = []
    num1_probabilities = calculate_probabilities(num1_counts)
    num1 = np.random.choice(list(num1_probabilities.keys()), p=list(num1_probabilities.values()))
    lotto_numbers.append(num1)
    used_numbers = set(lotto_numbers)

    for i in range(1, len(lotto_columns)):
        prev_num = lotto_numbers[-1]
        next_col = lotto_columns[i]
        next_num_probabilities = calculate_probabilities(transition_counts[next_col][prev_num])

        # print(prev_num)
        # print(next_col)
        # print(next_num_probabilities)

        valid_next_nums = [num for num in next_num_probabilities.keys() if num not in used_numbers]
        if not valid_next_nums:
            break
        valid_next_probabilities = [next_num_probabilities[num] for num in valid_next_nums]
        total_prob = sum(valid_next_probabilities)
        valid_next_probabilities = [prob / total_prob for prob in valid_next_probabilities]

        # print(valid_next_nums)
        # print(total_prob)
        # print(valid_next_probabilities)

        next_num = np.random.choice(valid_next_nums, p=valid_next_probabilities)
        lotto_numbers.append(next_num)
        used_numbers.add(next_num)

    return [int(num) for num in lotto_numbers]  # 수정함: numpy 타입을 기본 Python 타입으로 변환

@app.get("/")
def read_root():
    return {"message": "안녕하세요! FastAPI로 만든 로또 번호 생성기입니다."}

@app.get("/generate")
def generate():
    numbers = generate_lotto_number()
    return {"numbers": numbers}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

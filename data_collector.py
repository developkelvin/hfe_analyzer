from openpyxl import load_workbook
import os
import sys
import pymysql
from env_setting import host, user, password, db, charset


class DataCollector:

    def __init__(self, name_eng, name_kor='', age=''):
        self.dir_name = os.getcwd().replace('\\', '/') + '/' + name_eng
        self.name_kor = name_kor
        self.age = age

        self.get_connection()

    def get_connection(self):
        is_conn_success = False
        while not is_conn_success:
            try:
                self.conn = pymysql.connect(host=host,
                                            user=user,
                                            password=password,
                                            db=db,
                                            charset='utf8',
                                            cursorclass=pymysql.cursors.DictCursor)
            except Exception as e:
                print("db connection exception occures")
                print(e)
                continue

            if self.conn is not None:
                is_conn_success = True

    def db_disconnect(self):
        self.conn.close()

    def __del__(self):
        self.db_disconnect()

    def read_excel(self, file_path, num_of_ex, hand_side, box_size):
        try:
            experiment_excel = load_workbook(self.dir_name + '/' + file_path)
            data_sheet = experiment_excel['Sheet1']

            data_list = list()
            multiple_cells = data_sheet['A1':'G6']

            for m_idx, row in enumerate(multiple_cells):
                if m_idx == 0:
                    continue
                detail = dict()
                for idx, cell in enumerate(row):
                    if idx == 0:
                        detail['idx'] = cell.value
                    elif idx == 1:
                        detail['x-rect'] = cell.value
                    elif idx == 2:
                        detail['y-rect'] = cell.value
                    elif idx == 3:
                        detail['x-thumb'] = cell.value
                    elif idx == 4:
                        detail['y-thumb'] = cell.value
                    elif idx == 5:
                        detail['distance_1'] = cell.value
                    elif idx == 6:
                        detail['distance_2'] = cell.value

                data_list.append(detail)

            print(data_list)
        except PermissionError as pe:
            print(pe, file_path)
        except Exception as e:
            print(e, file_path)

    def get_all_file_list(self):
        file_list = os.listdir(self.dir_name)
        print(file_list)

        return file_list

    def insert_userinfo(self, eng_name, kor_name, age):
        sql = 'INSERT INTO '


    def parsing_name(self, filename):
        # 사람이름_(손방향)(홧수)_사이즈.xlsx
        pure_filename = filename.replace('.xlsx', '')

        splited_filename = pure_filename.split('_')

        eng_name = splited_filename[0]
        hand_side_merged = splited_filename[1]
        # 왼손/오른손 여부
        hand_side = hand_side_merged[:-1]
        if hand_side == 'left':
            hand_side = '0'
        elif hand_side == 'right':
            hand_side = '1'
        # 실험 회차
        num_of_ex = hand_side_merged[-1]
        # 상자 크기
        box_size = splited_filename[2]

        return num_of_ex, hand_side, box_size

    def run_collector(self):

        file_list = self.get_all_file_list()

        for file_name in file_list:
            # 회차, 왼손/오른손, 박스사이즈 리턴
            num_of_ex, hand_side, box_size = self.parsing_name(filename=file_name)

            print(num_of_ex, hand_side, box_size)

            self.read_excel(file_name, num_of_ex=num_of_ex, hand_side=hand_side, box_size=box_size)


if __name__ == '__main__':

    # 사용자 정보를 먼저 입력함
    name_eng = input("영문 이름(폴더명)을 입력하세요. [mandatory]\n")
    if name_eng == '' or name_eng is None:
        print("필수 입력 항목을 입력하지 않았습니다.")
        sys.exit(1)
    name_kor = input("한국 이름을 입력하세요. [optional]\n")
    age = input("나이를 입력하세요. [optional]\n")

    print("폴더 내의 엑셀 파일을 스캔합니다.\n")

    collector = DataCollector(name_eng=name_eng)

    collector.run_collector()

from openpyxl import load_workbook
import os
import sys
import pymysql
from env_setting import host, user, password, db, charset

VERSION = '0.0.2'
TEST_MODE = True


class DataCollector:

    def __init__(self, name_eng, name_kor='', age=0):
        self.get_connection()
        self.dir_name = os.getcwd().replace('\\', '/') + '/' + name_eng

        self.user_idx = self.insert_userinfo(name_eng=name_eng, name_kor=name_kor, age=age)

    def get_connection(self):
        is_conn_success = False
        while not is_conn_success:
            try:
                self.conn = pymysql.connect(host=host,
                                            user=user,
                                            password=password,
                                            db=db,
                                            charset=charset,
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

    def read_excel(self, file_path, ex_sequence, hand_side, box_size):
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

                data_list.append((detail['idx'], detail['x-rect'],detail['y-rect'],detail['x-thumb'],detail['y-thumb'],detail['distance_1'],detail['distance_2']))

            print(data_list)

        except PermissionError as pe:
            print(pe, file_path)
        except Exception as e:
            print(e, file_path)

        if TEST_MODE:
            sql = 'INSERT INTO hfe_data_test(ex_sequence, hand_side, box_size, user_idx, box_num, x_rect, y_rect, x_thumb, y_thumb, distance_1, distance_2 ) VALUES (' + ex_sequence + ', ' + hand_side + ', ' + box_size + ', ' + str(self.user_idx) + ',%s ,%s, %s, %s, %s, %s, %s)'
        else:
            sql = 'INSERT INTO hfe_data(ex_sequence, hand_side, box_size, box_num, x_rect, y_rect, x_thumb, y_thumb, distance_1, distance_2 ) VALUES (' + ex_sequence + ', '+ hand_side+', '+ box_size+',%s ,%s, %s, %s, %s, %s, %s)'

        try:
            print(sql)
            conn = self.conn
            cursor = conn.cursor()
            cursor.executemany(sql, data_list)
            conn.commit()
        except pymysql.err.MySQLError as mse:
            print(mse)
        except Exception as e:
            print(e)
        finally:
            cursor.close()

    def get_all_file_list(self):
        file_list = os.listdir(self.dir_name)
        print(file_list)

        return file_list

    def insert_userinfo(self, name_eng, name_kor, age):

        if TEST_MODE:
            sql = 'INSERT INTO hfe_user_test(age, name_kor, name_eng) VALUES (%s, %s, %s)'
            get_user_idx_sql = 'SELECT user_idx FROM hfe_user_test WHERE name_eng = %s'
        else:
            sql = 'INSERT INTO hfe_user(age, name_kor, name_eng) VALUES (%s, %s, %s)'
            get_user_idx_sql = 'SELECT user_idx FROM hfe_user WHERE name_eng = %s'


        user_idx = 0
        try:
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute(sql, (age, name_kor, name_eng))
            cursor.execute(get_user_idx_sql, (name_eng,))
            user_idx = cursor.fetchone()['user_idx']
            conn.commit()
        except pymysql.err.MySQLError as mse:
            print(mse)
            sys.exit(1)
        except Exception as e:
            print(e)
        finally:
            cursor.close()

        return user_idx

    def insert_ex_data(self):
        pass


    def parsing_name(self, filename):
        # 사람이름_(손방향)(홧수)_사이즈.xlsx
        pure_filename = filename.replace('.xlsx', '')

        splited_filename = pure_filename.split('_')

        eng_name = splited_filename[0]
        hand_side_merged = splited_filename[1]
        # 왼손/오른손 여부
        hand_side = hand_side_merged[:-1]
        if hand_side.lower() == 'left':
            hand_side = '0'
        elif hand_side.lower() == 'right':
            hand_side = '1'
        # 실험 회차
        ex_sequence = hand_side_merged[-1]
        # 상자 크기
        box_size = splited_filename[2]

        return ex_sequence, hand_side, box_size

    def run_collector(self):

        file_list = self.get_all_file_list()

        for file_name in file_list:
            # 회차, 왼손/오른손, 박스사이즈 리턴
            ex_sequence, hand_side, box_size = self.parsing_name(filename=file_name)

            print(ex_sequence, hand_side, box_size)

            self.read_excel(file_name, ex_sequence=ex_sequence, hand_side=hand_side, box_size=box_size)


if __name__ == '__main__':

    # 사용자 정보를 먼저 입력함
    name_eng = input("영문 이름(폴더명)을 입력하세요. [mandatory]\n")
    if name_eng == '' or name_eng is None:
        print("필수 입력 항목을 입력하지 않았습니다.")
        sys.exit(1)
    name_kor = input("한국 이름을 입력하세요. [optional]\n")
    age = input("나이를 입력하세요. [optional]\n")

    print("폴더 내의 엑셀 파일을 스캔합니다.\n")

    collector = DataCollector(name_eng=name_eng, name_kor=name_kor, age=age)

    collector.run_collector()

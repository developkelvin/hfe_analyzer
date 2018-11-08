import math
import pandas as pd
import matplotlib.pyplot as plt


class HFEAnalyzer:
    def __init__(self):
        # load whole data
        data = pd.read_csv('data/convert_mm_data_correct.csv',
                           names=['data_idx', 'ex_sequence', 'box_num', 'x_rect', 'y_rect', 'x_thumb', 'y_thumb',
                                  'distance_1', 'distance_2', 'hand_side', 'box_size', 'user_idx'])
        # filtering missed data
        data_missed = data[data['distance_2'] < 0]

        # filtered by btn_no
        self.btn1_data = data_missed[data_missed['box_num'] == 1]
        self.btn2_data = data_missed[data_missed['box_num'] == 2]
        self.btn3_data = data_missed[data_missed['box_num'] == 3]
        self.btn4_data = data_missed[data_missed['box_num'] == 4]
        self.btn5_data = data_missed[data_missed['box_num'] == 5]

        self.data = data
        self.data_missed = data_missed
        self.btn_size_list = [33, 35, 37, 39, 53, 55, 57, 59, 73, 75, 77, 79, 93, 95, 97, 99]

    def get_total_accuracy(self):
        error_rate = len(self.data_missed.index) / len(self.data.index)
        accuracy = 1 - error_rate
        print('accuracy :', round(accuracy, 3))
        print('error_rate :', round(error_rate, 3))

    def get_accuracy(self, target_data, box_size, num_of_total_data):
        height = box_size // 10
        width = box_size % 10
        correct_data = target_data[(target_data['x_thumb'] > -width / 2) & (target_data['x_thumb'] < width / 2) & (
                target_data['y_thumb'] > -height / 2) & ((target_data['y_thumb'] < height / 2))]
        num_of_correct = len(correct_data.index)
        num_of_total = len(target_data.index)
        num_of_miss = num_of_total - num_of_correct
        accuracy = 1 - (num_of_miss / num_of_total_data)
        print("Accuracy :", round(accuracy,3))
        #print('원래 오타 수 :', num_of_total)
        #print('보정 후 정타로 변환된 수 :', num_of_correct)

    # 만약 x, y축 각각 메디안/평균이 양수면 감소시키고 음수면 증가시킴
    def move_coord(self, target_data, dx, a, box_size, num_of_total_data, mode='median'):
        dy = a * dx
        x_val = 0
        y_val = 0

        if mode == 'median':
            x_val = target_data['x_thumb'].median()
            y_val = target_data['y_thumb'].median()
        elif mode == 'average':
            x_val = target_data['x_thumb'].mean()
            y_val = target_data['y_thumb'].mean()

        if x_val > 0:
            moved_data_x = target_data['x_thumb'] - dx
        elif x_val <= 0:
            moved_data_x = target_data['x_thumb'] + dx

        if y_val > 0:
            moved_data_y = target_data['y_thumb'] - dy
        elif y_val <= 0:
            moved_data_y = target_data['y_thumb'] + dy

        moved_data = pd.DataFrame({'x_thumb': moved_data_x, 'y_thumb': moved_data_y})
        self.get_accuracy(moved_data, box_size, num_of_total_data)

        return moved_data

    def get_statistics(self, box_num, box_size, hand_side, type='all'):

        data = self.data
        if type == 'all':
            data_filtered = data[
                (data['box_num'] == box_num) & (data['box_size'] == box_size) & (data['hand_side'] == hand_side)]
        elif type == 'miss':
            data_filtered = data[
            (data['box_num'] == box_num) & (data['box_size'] == box_size) & (data['hand_side'] == hand_side) & (data['distance_2'] < 0)]
        elif type == 'correct':
            data_filtered = data[
                (data['box_num'] == box_num) & (data['box_size'] == box_size) & (data['hand_side'] == hand_side) & (
                            data['distance_2'] >= 0)]
        else:
            print('wrong type parameter')
            return

        x_avg = data_filtered['x_thumb'].mean()
        x_sd = data_filtered['x_thumb'].std()
        x_median = data_filtered['x_thumb'].median()

        y_avg = data_filtered['y_thumb'].mean()
        y_sd = data_filtered['y_thumb'].std()
        y_median = data_filtered['y_thumb'].median()

        print("box_num :", box_num, "box_size :", box_size, "hand_side :", '왼손' if hand_side == 0 else '오른손')
        print("x 중앙값 :", x_median)
        print("x 표준편차 :", x_sd)
        print("x 평균 :", x_avg)
        print("y 중앙값 :", y_median)
        print("y 표준편차 :", y_sd)
        print("y 평균 :", y_avg)

        X = data_filtered['x_thumb'].values.reshape(-1, 1)
        y = data_filtered['y_thumb']
        plt.scatter(X, y)
        plt.axhline(0)
        plt.axvline(0)
        a = (box_size // 10)
        b = (box_size % 10)
        # lines for button
        plt.hlines(y=a / 2, xmin=-b / 2, xmax=b / 2, color='black')
        plt.hlines(y=-a / 2, xmin=-b / 2, xmax=b / 2, color='black')
        plt.vlines(x=b / 2, ymin=-a / 2, ymax=a / 2, color='black')
        plt.vlines(x=-b / 2, ymin=-a / 2, ymax=a / 2, color='black')

        plt.show()

        return {'x_avg': x_avg, 'x_sd': x_sd, 'x_median': x_median, 'y_avg': y_avg, 'y_sd': y_sd, 'y_median': y_median}

    # learning rate : 원점 방향으로 이동시킬 유클리드거리(mm)
    def optimize_accuracy(self, box_num, box_size, hand_side, learning_rate=0.1, mode='median'):
        data = self.data

        full_data = data[
            (data['box_num'] == box_num) & (data['box_size'] == box_size) & (data['hand_side'] == hand_side)]

        num_of_total_data = len(full_data.index)
        miss_data = full_data[(full_data['distance_2'] < 0)]
        num_of_missed_data = len(miss_data.index)

        origin_accuracy = 1 - (num_of_missed_data / num_of_total_data)
        print('origin accuracy :', origin_accuracy)

        if mode =='median':
            x_value = miss_data['x_thumb'].median()
            y_value = miss_data['y_thumb'].median()
        elif mode == 'mean':
            x_value = miss_data['x_thumb'].mean()
            y_value = miss_data['y_thumb'].mean()
        # 기울기
        a = y_value / x_value

        # x 변화량
        dx = math.sqrt((learning_rate) ** 2 / (a ** 2 + 1))

        print('dx :', dx, 'mm')
        for i in range(100):
            self.move_coord(miss_data, i*dx, a, box_size, num_of_total_data, mode)

if __name__ == '__main__':
    analyzer = HFEAnalyzer()
    analyzer.optimize_accuracy(2, 33, 0)


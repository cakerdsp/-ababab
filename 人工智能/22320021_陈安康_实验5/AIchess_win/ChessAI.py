import copy
from ChessBoard import *


class Evaluate(object):
    # 棋子棋力得分
    single_chess_point = {
        'c': 989,   # 车
        'm': 439,   # 马
        'p': 442,   # 炮
        's': 226,   # 士
        'x': 210,   # 象
        'z': 55,    # 卒
        'j': 65536  # 将
    }
    # 红兵（卒）位置得分
    red_bin_pos_point = [
        [1, 3, 9, 10, 12, 10, 9, 3, 1],
        [18, 36, 56, 95, 118, 95, 56, 36, 18],
        [15, 28, 42, 73, 80, 73, 42, 28, 15],
        [13, 22, 30, 42, 52, 42, 30, 22, 13],
        [8, 17, 18, 21, 26, 21, 18, 17, 8],
        [3, 0, 7, 0, 8, 0, 7, 0, 3],
        [-1, 0, -3, 0, 3, 0, -3, 0, -1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    # 红车位置得分
    red_che_pos_point = [
        [185, 195, 190, 210, 220, 210, 190, 195, 185],
        [185, 203, 198, 230, 245, 230, 198, 203, 185],
        [180, 198, 190, 215, 225, 215, 190, 198, 180],
        [180, 200, 195, 220, 230, 220, 195, 200, 180],
        [180, 190, 180, 205, 225, 205, 180, 190, 180],
        [155, 185, 172, 215, 215, 215, 172, 185, 155],
        [110, 148, 135, 185, 190, 185, 135, 148, 110],
        [100, 115, 105, 140, 135, 140, 105, 115, 110],
        [115, 95, 100, 155, 115, 155, 100, 95, 115],
        [20, 120, 105, 140, 115, 150, 105, 120, 20]
    ]
    # 红马位置得分
    red_ma_pos_point = [
        [80, 105, 135, 120, 80, 120, 135, 105, 80],
        [80, 115, 200, 135, 105, 135, 200, 115, 80],
        [120, 125, 135, 150, 145, 150, 135, 125, 120],
        [105, 175, 145, 175, 150, 175, 145, 175, 105],
        [90, 135, 125, 145, 135, 145, 125, 135, 90],
        [80, 120, 135, 125, 120, 125, 135, 120, 80],
        [45, 90, 105, 190, 110, 90, 105, 90, 45],
        [80, 45, 105, 105, 80, 105, 105, 45, 80],
        [20, 45, 80, 80, -10, 80, 80, 45, 20],
        [20, -20, 20, 20, 20, 20, 20, -20, 20]
    ]
    # 红炮位置得分
    red_pao_pos_point = [
        [190, 180, 190, 70, 10, 70, 190, 180, 190],
        [70, 120, 100, 90, 150, 90, 100, 120, 70],
        [70, 90, 80, 90, 200, 90, 80, 90, 70],
        [60, 80, 60, 50, 210, 50, 60, 80, 60],
        [90, 50, 90, 70, 220, 70, 90, 50, 90],
        [120, 70, 100, 60, 230, 60, 100, 70, 120],
        [10, 30, 10, 30, 120, 30, 10, 30, 10],
        [30, -20, 30, 20, 200, 20, 30, -20, 30],
        [30, 10, 30, 30, -10, 30, 30, 10, 30],
        [20, 20, 20, 20, -10, 20, 20, 20, 20]
    ]
    # 红将位置得分
    red_jiang_pos_point = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 9750, 9800, 9750, 0, 0, 0],
        [0, 0, 0, 9900, 9900, 9900, 0, 0, 0],
        [0, 0, 0, 10000, 10000, 10000, 0, 0, 0],
    ]
    # 红相或士位置得分
    red_xiang_shi_pos_point = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 60, 0, 0, 0, 60, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [80, 0, 0, 80, 90, 80, 0, 0, 80],
        [0, 0, 0, 0, 0, 120, 0, 0, 0],
        [0, 0, 70, 100, 0, 100, 70, 0, 0],
    ]

    red_pos_point = {
        'z': red_bin_pos_point,
        'm': red_ma_pos_point,
        'c': red_che_pos_point,
        'j': red_jiang_pos_point,
        'p': red_pao_pos_point,
        'x': red_xiang_shi_pos_point,
        's': red_xiang_shi_pos_point
    }

    def __init__(self, team):
        self.team = team

    def get_single_chess_point(self, chess: Chess):#接受的参数名是chess，它的类型是Chess
        if chess.team == self.team:
            return self.single_chess_point[chess.name]
        else:
            return -1 * self.single_chess_point[chess.name]

    def get_chess_pos_point(self, chess: Chess):
        red_pos_point_table = self.red_pos_point[chess.name]
        if chess.team == 'r':
            pos_point = red_pos_point_table[chess.row][chess.col]#红方在下面
        else:
            pos_point = red_pos_point_table[9 - chess.row][chess.col]#这是黑方的
        if chess.team != self.team:
            pos_point *= -1
        return pos_point

    def evaluate(self, chessboard: ChessBoard):
        point = 0
        for chess in chessboard.get_chess():
            point += self.get_single_chess_point(chess)
            point += self.get_chess_pos_point(chess)
        return point


class ChessMap(object):
    def __init__(self, chessboard: ChessBoard):
        self.chess_map = copy.deepcopy(chessboard.chessboard_map)


class ChessAI(object):
    def __init__(self, computer_team):
        self.team = computer_team   #自己是什么方
        self.max_depth = 5  #最大搜索深度
        self.old_pos = [0, 0]
        self.new_pos = [0, 0]
        self.evaluate_class = Evaluate(self.team)

    # def get_next_step(self, chessboard):
    #     for chess in chessboard.get_chess():
    #         if chess.team == self.team:
    #             put_down_pos = chessboard.get_put_down_position(chess)
    #             if len(put_down_pos) == 0:
    #                 continue
    #             return chess.row, chess.col, put_down_pos[0][0], put_down_pos[0][1]
    #     return

    def get_next_step(self, chessboard: ChessBoard):
        self.old_pos = None
        self.new_pos = None
        self.alpha_beta(1, -1 * 0x3f3f3f3f, 0x3f3f3f3f, chessboard)
        return self.old_pos[0], self.old_pos[1], self.new_pos[0], self.new_pos[1]

    @staticmethod
    def get_nxt_player(player):#得到下一个执行方
        if player == 'r':
            return 'b'
        else:
            return 'r'

    @staticmethod
    #把以前的位置改成新的位置，返回一个Chessboard对象
    def get_tmp_chessboard(chessboard, player_chess, new_row, new_col) -> ChessBoard:#-> 后面是返回类型
        tmp_chessboard = copy.deepcopy(chessboard)#深拷贝
        tmp_chess = tmp_chessboard.chessboard_map[player_chess.row][player_chess.col]
        tmp_chess.row, tmp_chess.col = new_row, new_col
        tmp_chessboard.chessboard_map[new_row][new_col] = tmp_chess
        tmp_chessboard.chessboard_map[player_chess.row][player_chess.col] = None
        return tmp_chessboard

    # def alpha_beta(self, chessboard, depth, a, b, cur_player):
    #     cur_eval = self.evaluate(chessboard)
    #     if depth == 0:
    #         return cur_eval
    #     if cur_player == self.team:
    #         for player_chess in chessboard.get_chess():
    #             if player_chess.team != cur_player:
    #                 continue
    #             nxt_pos = chessboard.get_put_down_position(player_chess)
    #             for new_row, new_col in nxt_pos:
    #                 tmp_chessboard = self.get_tmp_chessboard(chessboard, player_chess, new_row, new_col)
    #                 a = max(a, self.alpha_beta(tmp_chessboard, depth-1, a, b, self.get_nxt_player(cur_player)))
    #                 if b <= a:
    #                     break
    #             if b <= a:
    #                 break
    #         return a
    #     else:
    #         for player_chess in chessboard.get_chess():
    #             if player_chess.team != cur_player:
    #                 continue
    #             nxt_pos = chessboard.get_put_down_position(player_chess)
    #             for new_row, new_col in nxt_pos:
    #                 tmp_chessboard = self.get_tmp_chessboard(chessboard, player_chess, new_row, new_col)
    #                 b = min(b, self.alpha_beta(tmp_chessboard, depth-1, a, b, self.get_nxt_player(cur_player)))
    #                 if b <= a:
    #                     break
    #             if b <= a:
    #                 break

    #当前层的a,b值，如果a>=b就进行剪枝
    def alpha_beta(self, depth, a, b, chessboard: ChessBoard):
        # 奇数层取AI持棋，取极大；偶数层玩家持棋，取极小
        #如果层数大于规定层数就返回得分
        if depth >= self.max_depth:
            return self.evaluate_class.evaluate(chessboard)
        #获取当前棋盘中的所有棋子
        chess_in_board = chessboard.get_chess()
        for chess in chess_in_board:
            
            if depth % 2 == 1 and chess.team == self.team or \
               depth % 2 == 0 and chess.team != self.team:
                nxt_pos_arr = chessboard.get_put_down_position(chess)# 获取当前被点击棋子可以落子的位置
                for nxt_row, nxt_col in nxt_pos_arr:
                    old_row, old_col = chess.row, chess.col #棋子目前的位置
                    old_chess_in_new_pos = chessboard.chessboard_map[nxt_row][nxt_col]#chessboard_map
                    #更新chess和board的对象
                    chessboard.chessboard_map[nxt_row][nxt_col] = chessboard.chessboard_map[old_row][old_col]
                    chessboard.chessboard_map[nxt_row][nxt_col].update_position(nxt_row, nxt_col)
                    chessboard.chessboard_map[old_row][old_col] = None
                    #返回的得分值
                    ret = self.alpha_beta(depth+1, a, b, chessboard)
                    #还原回原棋盘和棋子对象
                    chessboard.chessboard_map[old_row][old_col] = chessboard.chessboard_map[nxt_row][nxt_col]
                    chessboard.chessboard_map[old_row][old_col].update_position(old_row, old_col)
                    chessboard.chessboard_map[nxt_row][nxt_col] = old_chess_in_new_pos
                    if depth % 2 == 1:  # 若为极大层
                        #只有返回第一层时才会更改
                        if (ret > a or not self.old_pos) and depth == 1:
                            self.old_pos = [chess.row, chess.col]
                            self.new_pos = [nxt_row, nxt_col]
                        a = max(a, ret)
                    else:               # 若为极小层
                        b = min(b, ret)
                    if b <= a:
                        #这个返回值估计也没用了
                        return a if depth % 2 == 1 else b
        return a if depth % 2 == 1 else b

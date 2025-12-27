import copy
from ChessBoard import *
import math

class Evaluate(object):
    # 棋子棋力得分
    single_chess_point = {
        'c': 989,   # 车
        'm': 443,   # 马
        'p': 500,   # 炮
        's': 226,   # 士
        'x': 210,   # 象
        'z': 55,    # 卒
        'j': 65536  # 将
    }
    # 象棋棋盘是9x10的
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
        [70, 100, 100, 90, 150, 90, 100, 100, 70],
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
        'z': red_bin_pos_point,#红兵的位置得分
        'm': red_ma_pos_point,#红马
        'c': red_che_pos_point,#红车
        'j': red_jiang_pos_point,#红将
        'p': red_pao_pos_point,#红炮
        'x': red_xiang_shi_pos_point,#红象
        's': red_xiang_shi_pos_point#红士
    }

    def __init__(self, team):
        self.team = team

    def get_single_chess_point(self, chess: Chess):
        if chess.team == self.team:
            return self.single_chess_point[chess.name]
        else:
            return -1 * self.single_chess_point[chess.name]

    def get_chess_pos_point(self, chess: Chess):
        red_pos_point_table = self.red_pos_point[chess.name]
        if chess.team == 'r':
            pos_point = red_pos_point_table[chess.row][chess.col]
        else:
            pos_point = red_pos_point_table[9 - chess.row][chess.col]
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


class MY_AI2(object):
    def __init__(self,team,parent,old_pos = None,op = None,chess = None):
        self.team = team
        self.parent = parent
        self.children = []
        self.visited = 0.000001
        self.val = 0
        self.param = 1.4
        self.evaluate = Evaluate(self.team) #初始化
        self.max_depth = 4
        self.count = 80
        self.old_pos = old_pos
        self.op = op
        self.chess_eat = chess 
        self.max_val = 10000
          	  
    def reverse_team(self,team):
        if team == 'r':
        	return 'b'
        else:
        	return 'r'
    

    #生成下一个子对象
    def get_next_state(self,op,chess,chessboard):
        old_row,old_col = chess.row,chess.col
        old_pos = (old_row,old_col)
        chess_eat = chessboard.chessboard_map[op[0]][op[1]]
        child = MY_AI2(self.reverse_team(self.team),self,old_pos,op,chess_eat)
        return child
        
    def expand(self,chessboard):
        chesses = chessboard.get_chess()
        for chess in chesses:
            if chess.team == self.team:
                possible_op = chessboard.get_put_down_position(chess)
                for op in possible_op:
                    child = self.get_next_state(op,chess,chessboard)
                    self.children.append(child)
    
    
    def select_child(self):
        if len(self.children) != 0:
            selected_child = max(self.children,key = lambda c: c.val/c.visited + c.param * ((math.log(self.visited,2.7) / c.visited) ** 0.5))
            return selected_child
        else:
            return None
        
    
    #这个函数还起着恢复现场的作用
    def backpropagate(self,val,chessboard):
        self.visited += 1
        self.val += val
        if self.op != None and self.old_pos != None:
            chess = chessboard.chessboard_map[self.op[0]][self.op[1]]
            chess.update_position(self.old_pos[0],self.old_pos[1])
            chessboard.chessboard_map[self.old_pos[0]][self.old_pos[1]] = chess
            chessboard.chessboard_map[self.op[0]][self.op[1]] = self.chess_eat
        if self.parent:
        	self.parent.backpropagate(val,chessboard)
  
	

    #把root_team 传入，用来判断该求最大还是最小,team是当前操作方
    def simulate(self,chessboard,a,b,depth,team,max_depth,root_team):
        if depth >= max_depth:
        	#调用方法得到返回值
            eva = Evaluate(root_team)
            return eva.evaluate(chessboard)
        chesses = chessboard.get_chess()
        for chess in chesses:
            if (root_team == team and chess.team == root_team) or (root_team != team and chess.team != root_team):
                possible_op = chessboard.get_put_down_position(chess)
                for row,col in possible_op:
                    cur_row,cur_col = chess.row,chess.col
                    chess2 = chessboard.chessboard_map[row][col]
                    chess.update_position(row,col)
                    chessboard.chessboard_map[row][col] = chess
                    chessboard.chessboard_map[cur_row][cur_col] = None
                    val = self.simulate(chessboard,a,b,depth + 1,self.reverse_team(team),max_depth,root_team)                   
                    chess.update_position(cur_row,cur_col)
                    chessboard.chessboard_map[cur_row][cur_col] = chess
                    chessboard.chessboard_map[row][col] = chess2
                    if root_team == team:
                        a = max(val,a)
                    else:                                                                                                                                                                  
                        b = min(val,b)
                    if a >= b:
                        return a if root_team == team else b
        return a if root_team == team else b
                        	                   
	
    def get_next_step(self,chesssboard):
        child = self.MCTS(chesssboard,self.count)
        nxt_row,next_col = child.op[0],child.op[1]
        cur_row,cur_col = child.old_pos[0],child.old_pos[1]
        return cur_row,cur_col,nxt_row,next_col

    
    def MCTS(self,chessboard,count):
        hhhmax = 0
        root = MY_AI2(self.team,None)
        for _ in range(count):
            hhh = 1
            node = root
            while True:
            	if len(node.children) == 0:
            		node.expand(chessboard)
            		break
            	else:
                    tmp_node = node.select_child()
                    hhh += 1
                    # if tmp_node == None:
                    #     node.backpropagate(val,chessboard)
                    #     best_child = max(root.children,key = lambda c:c.val/c.visited)
                    #     return best_child
                    node = tmp_node
                    chess = chessboard.chessboard_map[node.old_pos[0]][node.old_pos[1]]
                    chess.update_position(node.op[0],node.op[1])
                    chessboard.chessboard_map[node.op[0]][node.op[1]] = chess
                    chessboard.chessboard_map[node.old_pos[0]][node.old_pos[1]] = None
            #下面进行模拟，这个待定,用alpha-beta剪枝进行模拟
            val = node.simulate(chessboard,-1 * (0x3f3f3f3f),(0x3f3f3f3f),1,node.team,node.max_depth,root.team)
            hhh += self.max_depth
            #如果是对手操作，val是评估函数计算得到的值，这个值肯定是越大越好，但对我们来说，这个值应给越小越好，所以这里应该有一个判断
            #if node.team != root.team:
            #max_val是一次得分的最大值
            #	val = -val
            node.backpropagate(val,chessboard)
            hhhmax = max(hhhmax,hhh)
        best_child = max(root.children,key = lambda c:c.val/c.visited)
        #best_child = root.select_child()
        print(hhhmax)
        return best_child




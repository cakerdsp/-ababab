import numpy as np
import matplotlib.pyplot as plt
import random
class GeneticAlgTSP():
    #初始化函数，读取tsp文件并初始化城市位置信息以及初始化种群
    def __init__(self,filename):
        #种群规模
        self.pop_size = 20
        #选择出的优秀种群的数目
        #self.select_num = 0
        #操作次数
        self.operate_num = self.pop_size * 2
        self.mutation_times_reverse = 0
        self.mutation_times_swap = 0
        self.population = []
        self.ans_distance = []
        self.population_dist = []
        with open(filename,'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('DIMENSION'):
                    #获取数据数量
                    self.dimension = int(line.split(':')[1])
                if line.startswith('NODE_COORD_SECTION'):
                    #获取数据起始行
                    start = lines.index(line) + 1
                    break
            self.cities = np.zeros((self.dimension,2))
            #把数据放在cities里面
            for i in range(start,start + self.dimension):
                its = lines[i].split(' ')
                self.cities[i - start][0] = float(its[1])
                self.cities[i - start][1] = float(its[2])
            #初始化population
            for i in range(self.pop_size):
                individual = list(range(self.dimension))
                random.shuffle(individual)
                individual.append(individual[0])
                self.population.append(individual)
                self.population_dist.append(self.distance(individual))


    #用来计算总的距离
    def distance(self,individual):
        sum_dist = 0
        for i in range(self.dimension):
            x1 = self.cities[individual[i]][0]
            y1 = self.cities[individual[i]][1]
            x2 = self.cities[individual[i + 1]][0]
            y2 = self.cities[individual[i + 1]][1]
            point1 = np.array([x1,y1])
            point2 = np.array([x2,y2])
            dist = np.linalg.norm(point2 - point1)
            sum_dist = sum_dist + dist
        return sum_dist
    
    #选择种群中的优秀个体，采用轮盘赌算法
    # def select(self):
    #     sumdist = 0
    #     dists = []
    #     weight = []
    #     for i in range(self.pop_size):
    #         dist = self.distance(self.population[i])
    #         dists.append(dist)
    #         sumdist = sumdist + dist
    #     for i in range(self.pop_size):
    #         weight.append(1 - (dists[i]/sumdist))
    #     selected = random.choices(self.population,weight,k = self.select_num)
    #     no_repeat_selected = []
    #     for it in selected:
    #         if it not in no_repeat_selected:
    #             no_repeat_selected.append(it)
    #     #返回什么待定
    #     return no_repeat_selected
    # def select(self):
    #     selected = sorted(self.population,key = lambda x : self.distance(x))
    #     #返回什么待定
    #     return selected[:self.select_num]
    #一个辅助函数，返回依据种群个体的索引找到的个体的总距离
    def sort_by_reference(self,x):
        idx = self.population.index(x)
        return self.population_dist[idx]
    #依据总距离选择下一代的种群
    def select(self):
        #selected = sorted(self.population,key = lambda x : self.population_dist[x])
        selected = sorted(self.population,key = self.sort_by_reference)
        return selected[:self.pop_size]

    #更新population_dist
    def update_dist(self):
        self.population_dist.clear()
        for it in self.population:
            self.population_dist.append(self.distance(it))



    #交叉操作，保证得到的子代合规
    def crossover(self,parent1,parent2):
        parent1.pop()
        parent2.pop()
        a,b = random.sample(range(self.dimension),2)
        start,end = min(a,b),max(a,b)
        child1 = [None] * self.dimension 
        child2 = [None] * self.dimension
        for index in range(start,end + 1):
            child1[index] = parent1[index]
            child2[index] = parent2[index]
        idx1 = 0
        idx2 = 0
        for i in range(self.dimension):
            if child1[i] is None:
                while parent2[idx1] in child1:
                    idx1 = idx1 + 1
                child1[i] = parent2[idx1]
            if child2[i] is None:
                while parent1[idx2] in child2:
                    idx2 = idx2 + 1
                child2[i] = parent1[idx2]
        parent1.append(parent1[0])
        parent2.append(parent2[0])
        child1.append(child1[0])
        child2.append(child2[0])
        return child1,child2

    #映射交叉，效果不是很好
    # def crossover(self,parent1,parent2):
    #     parent1.pop()
    #     parent2.pop()
    #     map_set1 = {}
    #     map_set2 = {}
    #     a,b = random.sample(range(self.dimension),2)
    #     start,end = min(a,b),max(a,b)
    #     child1 = [None] * self.dimension 
    #     child2 = [None] * self.dimension
    #     for index in range(start,end + 1):
    #         child1[index] = parent1[index]
    #         child2[index] = parent2[index]
    #         map_set1[parent1[index]] = parent2[index]
    #         map_set2[parent2[index]] = parent1[index]
    #     # print(map_set1)
    #     # print(map_set2)
    #     for i in range(self.dimension):
    #         if child1[i] is None:
    #             if parent2[i] in child1:
    #                 it = parent2[i]
    #                 while it in child1:
    #                     it = map_set1[it]
    #                 child1[i] = it
    #             else:
    #                 child1[i] = parent2[i]
    #         if child2[i] is None:
    #             if parent1[i] in child2:
    #                 it = parent1[i]
    #                 while it in child2:
    #                     it = map_set2[it]
    #                 child2[i] = it
    #             else:
    #                 child2[i] = parent1[i]
    #     parent1.append(parent1[0])
    #     parent2.append(parent2[0])
    #     child1.append(child1[0])
    #     child2.append(child2[0])
    #     return child1,child2

    
    #交换变异操作,
    def swapmutate(self,individual):
        individual.pop()
        a,b = random.sample(range(self.dimension),2)
        tmp = individual[b]
        individual[b] = individual[a]
        individual[a] = tmp
        individual.append(individual[0])
        return individual

    #翻转变异操作
    def reversemutae(self,individual):
        individual.pop()
        a,b = random.sample(range(self.dimension),2)
        start,end = min(a,b),max(a,b)
        individual[start : end + 1] = individual[start : end + 1][::-1]
        individual.append(individual[0])
        return individual
            
    #
    # def iterate(self,num_iterations):
    #     self.num_iterations = num_iterations
    #     for i in range(num_iterations):
    #         new_population = self.select()
    #         while len(new_population) < self.pop_size:
    #             a,b = random.sample(new_population,2)    
    #             child = self.crossover(a,b)
    #             if random.random() < 0.3:
    #                 child = self.swapmutate(child)
    #             if random.random() < 0.1:
    #                 child = self.reversemutae(child)
    #             if child in new_population:
    #                 continue
    #             new_population.append(child)
    #         self.population = new_population
    #         best_individual = min(self.population,key = lambda x : self.distance(x))
    #         best_val = self.distance(best_individual)
    #         self.ans_distance.append(best_val)
    #     #best_individual = min(self.population,key = lambda x : self.distance(x))
    #     #best_val = self.distance(best_individual)
    #     return best_individual,best_val


    #选出用来做交叉的父母
    def select_parent(self):
        size = len(self.population)
        sumdist = sum(self.population_dist)
        weight = []
        for i in range(size):
            w = 1 - (self.population_dist[i]/sumdist)
            while w in weight:
                w = w + random.random() * 1e-10
            weight.append(w)
        pare1 = random.choices(self.population,weight,k = 1)[0]
        idx = self.population.index(pare1)
        a = [x for x in self.population if x != pare1]
        b = [w for w in weight if weight.index(w) != idx]
        if len(a) != len(b):
            print(len(a))
            print(len(b))
            print(len(self.population_dist))
            print(len(self.population))
            print(size)
            print(idx)
            print(weight[idx])
            print(1 - 0.1 * (self.population_dist[idx]/sumdist))
            print(weight.index(1 - 0.1 * (self.population_dist[idx]/sumdist)))
        pare2 = random.choices(a,b,k = 1)[0]
        return pare1,pare2

    # #变化率从0.1 - 0.2
    # def rate_reversemutation(self,count):
    #     return 0.1 - 0.09 * (float(count) / self.num_iterations)

    # 变化率从0.1 - 0.2
    def rate_reversemutation(self,count):
        mutation_rate = 0.3 - 0.2 * (float(count) / self.num_iterations)
        # c = min(self.population,key = self.sort_by_reference)
        # a = self.population_dist[self.population.index(c)]
        # b = 2 * a
        a = 1
        b = 2
        if len(self.ans_distance) >= 2:
            b = self.ans_distance[-2]
            a = self.ans_distance[-1]
        if  abs((b - a) / b) < 0.00001:
            self.mutation_times_reverse = self.mutation_times_reverse + 1
        if self.mutation_times_reverse > self.num_iterations * 0.65 + self.num_iterations - count:
            #
            mutation_rate = 0.3 + 0.2 * (float(count) / self.num_iterations) 
            print(count)
            print(abs((b - a) / b))
            print(a)
            if abs((b - a) / b) >= 0.001:  
                self.mutation_times_reverse = 0
        return mutation_rate

    # #变化率从0.2 - 0.3
    # def rate_swapmutation(self,count):
    #     return 0.3 - 0.2 * (float(count) / self.num_iterations) 
    #交换两个城市在个体队列中的位置的变异率
    def rate_swapmutation(self,count):
        mutation_rate = 0.3 - 0.2 * (float(count) / self.num_iterations)
        # c = min(self.population,key = self.sort_by_reference)
        # a = self.population_dist[self.population.index(c)]
        # b = 2 * a
        a = 1
        b = 2
        if len(self.ans_distance) >= 2:
            b = self.ans_distance[-2]
            a = self.ans_distance[-1]
        if  abs((b - a) / b) < 0.00001:
            self.mutation_times_swap = self.mutation_times_swap + 1
        if self.mutation_times_swap > self.num_iterations * 0.65 + self.num_iterations - count:
            #高变异率模式，变异率随迭代次数线性增加
            mutation_rate = 0.3 + 0.2 * (float(count) / self.num_iterations) 
            if abs((b - a) / b) >= 0.001:  
                self.mutation_times_swap = 0
        return mutation_rate

    #选择变异的个体，已经作废了
    def select_mutate_individual(self):
        size = len(self.population)
        sumdist = sum(self.population_dist)
        weight = []
        for i in range(size):
            w = (self.population_dist[i]/sumdist)
            while w in weight:
                w = w + random.random() * 1e-10
            weight.append(w)
        individual = random.choices(self.population,weight,k = 1)[0]
        return individual

    #报告中优化方案3的废弃方案，因为性能和个体重合问题导致了这个方案废弃
    # def iterate(self,num_iterations):
    #     self.num_iterations = num_iterations
    #     for i in range(num_iterations):
    #         new_population = []
    #         for i in range(self.operate_num):
    #             #a,b = random.sample(self.population,2) 
    #             a,b = self.select_parent()   
    #             child1,child2 = self.crossover(a,b)
    #             if child1 not in self.population:
    #                 self.population.append(child1)
    #                 self.population_dist.append(self.distance(child1))
    #             if child2 not in self.population:
    #                 self.population.append(child2)
    #                 self.population_dist.append(self.distance(child2))
    #             #child1 = self.crossover(a,b)
    #             if random.random() < self.rate_swapmutation(i):
    #             # if random.random() < 0.3
    #                 individual = self.select_mutate_individual()
    #                 self.swapmutate(individual)
    #             if random.random() < self.rate_reversemutation(i):
    #             # if random.random() < 0.1:
    #                 individual = self.select_mutate_individual()
    #                 self.reversemutae(individual)
    #             # if random.random() < self.rate_swapmutation(i):
    #             # # if random.random() < 0.3:
    #             #     child2 = self.swapmutate(child2)
    #             # if random.random() < self.rate_reversemutation(i):
    #             # # if random.random() < 0.1:
    #             #     child2 = self.reversemutae(child2)
    #         self.population = self.select()
    #         self.update_dist()
    #         best_individual = min(self.population,key = self.sort_by_reference)
    #         best_val = self.distance(best_individual)
    #         self.ans_distance.append(best_val)
    #         # print(i)
    #     #best_individual = min(self.population,key = lambda x : self.distance(x))
    #     #best_val = self.distance(best_individual)
    #     ans_best_individual = [x + 1 for x in best_individual]
    #     return ans_best_individual,best_val


    #求解函数
    def iterate(self,num_iterations):
        self.num_iterations = num_iterations
        for c in range(num_iterations):
            new_population = []
            for i in range(self.operate_num):
                #a,b = random.sample(self.population,2) 
                a,b = self.select_parent()   
                child1,child2 = self.crossover(a,b)
                #child1 = self.crossover(a,b)
                if random.random() < self.rate_swapmutation(c):
                # if random.random() < 0.3:
                    child1 = self.swapmutate(child1)
                if random.random() < self.rate_reversemutation(c):
                # if random.random() < 0.3:
                    child1 = self.reversemutae(child1)
                if random.random() < self.rate_swapmutation(c):
                # if random.random() < 0.3:
                    child2 = self.swapmutate(child2)
                if random.random() < self.rate_reversemutation(c):
                # if random.random() < 0.3:
                    child2 = self.reversemutae(child2)
                if child1 not in self.population:
                    self.population.append(child1)
                    self.population_dist.append(self.distance(child1))
                if child2 not in self.population:
                    self.population.append(child2)
                    self.population_dist.append(self.distance(child2))
            self.population = self.select()
            self.update_dist()
            best_individual = min(self.population,key = self.sort_by_reference)
            best_val = self.population_dist[self.population.index(best_individual)]
            self.ans_distance.append(best_val)
            # print(i)
        #best_individual = min(self.population,key = lambda x : self.distance(x))
        #best_val = self.distance(best_individual)
        ans_best_individual = [x + 1 for x in best_individual]
        return ans_best_individual,best_val


    #展示函数
    def show(self,path,num_iterations):
        x = []
        y = []
        labels = []
        for i in range(self.dimension + 1):
            x.append(self.cities[path[i] - 1][0])
            y.append(self.cities[path[i] - 1][1])
            labels.append(path[i])
        
        x_plot = range(num_iterations)
        plt.subplot(2, 1, 1)
        plt.plot(x, y)
        for i, txt in enumerate(labels):
            plt.text(x[i], y[i], str(txt), fontsize=6, ha='right', va='bottom')
        #plt.show()
        plt.subplot(2, 1, 2)
        plt.scatter(x_plot,self.ans_distance,s = 3,c = 'g')
        plt.show()


def show_wendingxing(arr):
    x = range(len(arr))
    plt.plot(x,arr)
    plt.show()
#测试部分，里面的路径是我电脑里面的绝对路径，若要运行应改成正确的文件路径
# test = GeneticAlgTSP("C:\\Users\\86135\\Desktop\\python\\TSP\\dj38 (1).tsp")
test = GeneticAlgTSP("C:\\Users\\86135\\Desktop\\python\\TSP\\xqg237.tsp")
# test = GeneticAlgTSP("C:\\Users\\86135\\Desktop\\python\\TSP\\pma343.tsp")
# test = GeneticAlgTSP("C:\\Users\\86135\\Desktop\\python\\TSP\\qa194.tsp")
# path,val = test.iterate(3000)
# arr = []
# for i in range(10):
#     # test = GeneticAlgTSP("C:\\Users\\86135\\Desktop\\python\\TSP\\dj38 (1).tsp")
#     test = GeneticAlgTSP("C:\\Users\\86135\\Desktop\\python\\TSP\\xqg237.tsp")
#     path2,val2 = test.iterate(6000)
#     arr.append(val2)
# show_wendingxing(arr)
path2,val2 = test.iterate(6000)
print(path2)
print(val2)
test.show(path2,6000)


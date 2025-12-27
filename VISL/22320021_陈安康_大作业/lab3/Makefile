# Makefile with Automatic Dependency Generation

# All .cpp source files
SRC = main.cpp Design.cpp FPGA.cpp FpgaTile.cpp Net.cpp RRNode.cpp Solution.cpp

# All .o object files and .d dependency files
OBJ = $(SRC:.cpp=.o)
DEPS = $(SRC:.cpp=.d)

CXX = g++
# 新增 -MMD -MP 标志，告诉 g++ 生成依赖文件
CFLAGS = -Wall -Wextra -std=c++17 -pedantic -g -MMD -MP

all: main

main: $(OBJ)
	$(CXX) $(CFLAGS) -o main $(OBJ)

%.o: %.cpp
	$(CXX) $(CFLAGS) -c $< -o $@

clean:
	# clean 命令也需要删除 .d 文件
	rm -f main $(OBJ) $(DEPS)

# 包含所有生成的依赖文件。
# 前面的 '-' 符号让 make 在找不到文件时不会报错。
-include $(DEPS)
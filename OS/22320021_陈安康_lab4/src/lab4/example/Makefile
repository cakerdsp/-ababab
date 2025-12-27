BUILD_DIR = build
SRC_DIR = src

main.out : $(BUILD_DIR)/main.o $(BUILD_DIR)/c_func.o $(BUILD_DIR)/cpp_func.o $(BUILD_DIR)/asm_func.o
	g++ -o main.out $(BUILD_DIR)/main.o $(BUILD_DIR)/c_func.o $(BUILD_DIR)/cpp_func.o $(BUILD_DIR)/asm_func.o -m32

$(BUILD_DIR)/c_func.o : $(SRC_DIR)/c_func.c
	gcc -o $(BUILD_DIR)/c_func.o -m32 -c $(SRC_DIR)/c_func.c

$(BUILD_DIR)/cpp_func.o : $(SRC_DIR)/cpp_func.cpp
	g++ -o $(BUILD_DIR)/cpp_func.o -m32 -c $(SRC_DIR)/cpp_func.cpp

$(BUILD_DIR)/main.o : $(SRC_DIR)/main.cpp
	g++ -o $(BUILD_DIR)/main.o -m32 -c $(SRC_DIR)/main.cpp

$(BUILD_DIR)/asm_func.o : $(SRC_DIR)/asm_func.asm
	nasm -o $(BUILD_DIR)/asm_func.o -f elf32 $(SRC_DIR)/asm_func.asm


clean :
	rm $(BUILD_DIR)/*.o *.out

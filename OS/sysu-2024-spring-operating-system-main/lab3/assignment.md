# Lab3 保护模式

# 实验要求

> - DDL：2024年4月6号 23:59:59
> - 提交的内容：将**3个assignment的代码**和**实验报告**放到**压缩包**中，命名为“**学号_姓名_lab3.zip**”，并交到[课程网站上](http://course.dds-sysu.tech/course/14/homework)
> - **材料的Example的代码放置在`src`目录下**。

1. 实验不限语言， C/C++/Rust都可以。
2. 实验不限平台， Windows、Linux和MacOS等都可以。
3. 实验不限CPU， ARM/Intel/Risc-V都可以。

## Assignment 1

### 1.1

复现Example 1，说说你是怎么做的并提供结果截图，也可以参考Ucore、Xv6等系统源码，实现自己的LBA方式的磁盘访问。

### 1.2

在Example1中，我们使用了LBA28的方式来读取硬盘。此时，我们只要给出逻辑扇区号即可，但需要手动去读取I/O端口。然而，BIOS提供了实模式下读取硬盘的中断，其不需要关心具体的I/O端口，只需要给出逻辑扇区号对应的磁头（Heads）、扇区（Sectors）和柱面（Cylinder）即可，又被称为CHS模式。现在，同学们需要将LBA28读取硬盘的方式换成CHS读取，同时给出逻辑扇区号向CHS的转换公式。最后说说你是怎么做的并提供结果截图。

参考资料：

- [LBA向CHS模式的转换](https://blog.csdn.net/G_Spider/article/details/6906184)
- [int 13h中断](https://blog.csdn.net/brainkick/article/details/7583727)

其中，关键参数如下。

| 参数               | 数值  |
| ---------------- | --- |
| 驱动器号（DL寄存器）      | 80h |
| 每磁道扇区数           | 63  |
| 每柱面磁头数（每柱面总的磁道数） | 18  |

## Assignment 2

复现Example 2，使用gdb或其他debug工具在进入保护模式的4个重要步骤上设置断点，并结合代码、寄存器的内容等来分析这4个步骤，最后附上结果截图。gdb的使用可以参考appendix的“debug with gdb and qemu”部份。

## Assignment 3

改造“Lab2-Assignment 4”为32位代码，即在保护模式后执行自定义的汇编程序。

# 参考资料

- 《从实模式到保护模式》：第8.3.3节~8.3.5节，第11章，第12.4节。

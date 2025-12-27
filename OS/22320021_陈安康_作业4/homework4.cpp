#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <stdlib.h>
class param {
public:
    int count;
    int nums[1000];
    float aver;
    int min;
    int max;
    param(int c,char* str[]) {
        count = c - 1;
        //printf("%d",count); 
        for(int i=1;i<c;i++) {
            nums[i - 1] = atoi(str[i]);
            //printf("%d",nums[i - 1]);
        }
        aver = -1;
        min = -1;
        max = -1;
        //printf("\n");
    }
};
void *average(void *p);
void *min(void *p);
void *max(void *p);
int main(int argc, char* argv[]) {
    pid_t pid;
    pthread_t tid;
    pthread_attr_t attr;
    if(argc == 1) {
        printf("没有输入参数，退出程序！");
        exit(0);
    }
    param p(argc,argv);
        pthread_attr_init(&attr);
        pthread_create(&tid,&attr,average,&p);
        pthread_join(tid,NULL);      
        printf("average:%.2f\n",p.aver);  
        pthread_create(&tid,&attr,max,&p);
        pthread_join(tid,NULL);
        printf("max:%d\n",p.max);
        pthread_create(&tid,&attr,min,&p);
        pthread_join(tid,NULL);
        printf("min:%d\n",p.min);

    
}
void *average(void *p) {
    float ans;
    int sum = 0;
    //printf("\n%d",(*((param*)p)).count);
    for(int i=0;i<(*((param*)p)).count;i++) {
        sum += (*((param*)p)).nums[i];
    }
    //printf("\n%d",sum);
    ans = float(sum) / (*((param*)p)).count;
    (*((param*)p)).aver = ans;
    printf("average : %.2f\n", ans);
    pthread_exit(0);
}
void *min(void *p) {
    int min = 100000000;
    //printf("\n%d",(*((param*)p)).count);
    for(int i=0;i<(*((param*)p)).count;i++) {
        min = min > (*((param*)p)).nums[i] ? (*((param*)p)).nums[i] : min;
    }
    //printf("\n%d",sum);
    (*(param*)p).min = min;
    printf("min : %d\n", min);
    pthread_exit(0);
}
void *max(void *p) {
    int max = -100000000;
    //printf("\n%d",(*((param*)p)).count);
    for(int i=0;i<(*((param*)p)).count;i++) {
        max = max < (*((param*)p)).nums[i] ? (*((param*)p)).nums[i] : max;
    }
    //printf("\n%d",sum);
    (*(param*)p).max = max;
    printf("max : %d\n", max);
    pthread_exit(0);
}
//编译命令是：gcc hello.cpp -o hello.o -pthread

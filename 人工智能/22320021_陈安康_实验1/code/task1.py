import time
def BinarySearch(nums,target):
    low=0
    high=len(nums)-1
    while low<=high:
        mid=int((low+high)/2)
        if nums[mid]<target:
            low=mid+1;
        elif nums[mid]>target:
            high=mid-1;
        else:
            return mid;
    return -1

start_time = time.time()
test=[1,2,3,4,5,7,8,9,10,11,22,33,44,55,66,77,88,100,102,678]
index=BinarySearch(test,66)
end_time = time.time()
print(index)
run_time = end_time - start_time
print(run_time)


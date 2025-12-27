from knn import KNNClassifier
from svm import SVMClassifier
from dimensionality_reduction import PCA, LDA
from utils import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib


if __name__ == "__main__":
    # 初始化分类器
    knn = KNNClassifier(n_neighbors=3, metric='euclidean')
    svm = SVMClassifier(C=1.0, kernel='rbf', gamma='scale')
    
    # 加载数据（自动分割训练/测试集）
    train_data,train_label,test_data,test_label = load_data(r'C:\Users\86135\Desktop\模式识别\22320021_陈安康_模式识别_homework02\Yale_64x64.mat')
    # # 任务三
    # pca = PCA(n_components=16)
    # lda = LDA(n_components=16)
    # trainPca = pca.fit_transform(train_data)
    # trainLda = lda.fit_transform(train_data, train_label)

    # visualize_eigenvectors(pca.components_, "PCA特征向量", n_components=8, img_shape=(64, 64))
    # visualize_eigenvectors(lda.components_, "LDA特征向量", n_components=8, img_shape=(64, 64))
    
    # # 创建2x2的子图布局，将四个降维结果绘制在一个图中 - 增加图像大小
    # fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # # # 在四个子图位置分别绘制降维结果
    # # visualize_2d_data(trainPca, train_label, 
    # #                  "PCA降维后的人脸数据分布 (训练集)", "PCA", ax=axes[0, 0])
    # # visualize_2d_data(trainLda, train_label,    
    # #                  "LDA降维后的人脸数据分布 (训练集)", "LDA", ax=axes[0, 1])
    
    # testPca = pca.transform(test_data)
    # testLda = lda.transform(test_data)
    # visualize_2d_data(testPca, test_label,
    #                  "PCA降维后的人脸数据分布 (测试集)", "PCA", ax=axes[1, 0])
    # visualize_2d_data(testLda, test_label,
    #                  "LDA降维后的人脸数据分布 (测试集)", "LDA", ax=axes[1, 1])
    
    # # 调整子图之间的间距 - 增加间距避免文字遮挡
    # plt.tight_layout(pad=5.0, h_pad=4.0, w_pad=5.0)
    
    # # 为整个图添加一个总标题 - 调整字体大小和上边距
    # fig.suptitle("降维方法比较：PCA vs LDA", fontsize=18, y=0.99)
    # # 增加右侧边距以完全容纳图例，避免遮挡，同时增加子图间距
    # plt.subplots_adjust(top=0.92, wspace=0.45, hspace=0.45, right=0.85)  # 为总标题和图例留出更多空间

    # 任务四：测试不同维度的PCA和LDA降维效果
    # 定义要测试的维度
    dimensions = list(range(1, 15))  
    
    # 存储不同维度下的准确率
    pca_knn_accuracies = []
    lda_knn_accuracies = []
    pca_svm_accuracies = []
    lda_svm_accuracies = []
    
    # 对每个维度进行测试
    for dim in dimensions:
        # PCA降维
        pca = PCA(n_components=dim)
        trainPca = pca.fit_transform(train_data)
        testPca = pca.transform(test_data)
        
        # 使用KNN分类器评估PCA
        knn.fit(trainPca, train_label)
        pred = knn.predict(testPca)
        pca_knn_acc = knn.accuracy(test_label, pred)
        pca_knn_accuracies.append(pca_knn_acc)
        print(f"KNN-PCA (维度={dim}) 准确率: {pca_knn_acc:.2%}")
        
        # 使用SVM分类器评估PCA
        svm.fit(trainPca, train_label)
        pred = svm.predict(testPca)
        pca_svm_acc = svm.accuracy(test_label, pred)
        pca_svm_accuracies.append(pca_svm_acc)
        print(f"SVM-PCA (维度={dim}) 准确率: {pca_svm_acc:.2%}")
        
        # LDA降维 (LDA最多只能降到类别数-1维)
        max_lda_dim = min(dim, len(np.unique(train_label)) - 1)
        lda = LDA(n_components=max_lda_dim)
        trainLda = lda.fit_transform(train_data, train_label)
        testLda = lda.transform(test_data)
        
        # 使用KNN分类器评估LDA
        knn.fit(trainLda, train_label)
        pred = knn.predict(testLda)
        lda_knn_acc = knn.accuracy(test_label, pred)
        lda_knn_accuracies.append(lda_knn_acc)
        print(f"KNN-LDA (维度={max_lda_dim}) 准确率: {lda_knn_acc:.2%}")
        
        # 使用SVM分类器评估LDA
        svm.fit(trainLda, train_label)
        pred = svm.predict(testLda)
        lda_svm_acc = svm.accuracy(test_label, pred)
        lda_svm_accuracies.append(lda_svm_acc)
        print(f"SVM-LDA (维度={max_lda_dim}) 准确率: {lda_svm_acc:.2%}")
    
    # 可视化不同维度下的准确率对比
    accuracies = {
        'KNN-PCA': pca_knn_accuracies,
        'KNN-LDA': lda_knn_accuracies,
        'SVM-PCA': pca_svm_accuracies,
        'SVM-LDA': lda_svm_accuracies
    }
    
    # 调用可视化函数
    visualize_accuracy_vs_dimensions(dimensions, accuracies, "PCA与LDA在不同降维维度下的准确率对比")
    
    # 显示图形
    plt.show()
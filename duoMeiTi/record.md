## 生物信号：


[1].	Ciftci, U.A., I. Demir and L. Yin, FakeCatcher: Detection of Synthetic Portrait Videos using Biological Signals. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2020: p. 1-1.


##  时空域 + 伪影

[1].	Lu, W., et al., Detection of Deepfake Videos Using Long-Distance Attention. IEEE Transactions on Neural Networks and Learning Systems, 2024. 35(7): p. 9366-9379.

上面的综述：空间域和时间域融合，长距离注意力机制 。

[1].	G., P., et al., MRE-Net: Multi-Rate Excitation Network for Deepfake Video Detection. IEEE Transactions on Circuits and Systems for Video Technology, 2023. 33(8): p. 3663-3676.

上文综述：时空不一致性，构建多速率激励网络（Multi-Rate Excitation Network, MRE-Net）

[1].	Li, X., et al., Artifacts-Disentangled Adversarial Learning for Deepfake Detection. IEEE Transactions on Circuits and Systems for Video Technology, 2023. 33(4): p. 1658-1670.

上文综述：针对伪影的



## 对抗噪声标签攻击的深度伪造检测框架（感觉只是用来净化数据的）

[1].	Qiao, T., et al., Deepfake Detection Fighting Against Noisy Label Attack. IEEE Transactions on Multimedia, 2024. 26: p. 9047-9059.

上面的综述：一个负样本生成器（Negative Sample Generator, NSG）利用可能被污染的样本，通过模拟深度伪造造成的混合伪影来生成标签可靠的负样本。接下来，一个抗噪声对比学习器（Noise-immune Contrastive Learner, NiCL）将正样本和负样本作为训练数据，探索混合伪影和内在伪造线索以过滤掉噪声样本。此外，依靠标签净化，过滤后的噪声样本进一步被净化，然后反馈到特征提取器中用于后续的模型训练。



## 无监督方法

[1].	Zhang, L., et al., Unsupervised Learning-Based Framework for Deepfake Video Detection. IEEE Transactions on Multimedia, 2023. 25: p. 4785-4799.

上文的综述：基于光响应非均匀性（Photo-Response Non-Uniformity, PRNU）和噪声特征的两个聚类阶段



## 动态信息

[1].	Wang, H., Z. Liu and S. Wang, Exploiting Complementary Dynamic Incoherence for DeepFake Video Detection. IEEE Transactions on Circuits and Systems for Video Technology, 2023. 33(8): p. 4027-4040.

互补交叉动态融合模块（Complementary Cross Dynamics Fusion Module, CCDFM）



## 多模态

[1].	Yu, Y., et al., PVASS-MDD: Predictive Visual-Audio Alignment Self-Supervision for Multimodal Deepfake Detection. IEEE Transactions on Circuits and Systems for Video Technology, 2024. 34(8): p. 6926-6936.
音视频信号不一致


## 帧间

[1].	Hu, J., et al., Detecting Compressed Deepfake Videos in Social Networks Using Frame-Temporality Two-Stream Convolutional Network. IEEE Transactions on Circuits and Systems for Video Technology, 2022. 32(3): p. 1089-1102.

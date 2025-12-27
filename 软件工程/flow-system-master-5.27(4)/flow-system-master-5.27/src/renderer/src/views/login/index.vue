<template>
  <div class="login-main" v-loading="changeRegLoading || submitLoading">
    <form class="form" @submit.prevent="submit">
      <!-- 账户输入 -->
      <div class="flex-column">
        <label>账户</label>
      </div>
      <div class="inputForm">
        <img src="~@/assets/login/email.svg" alt="email" />
        <input type="text" class="input" v-model="loginObj.username" placeholder="您的账户" />
      </div>

      <!-- 密码输入 -->
      <div class="flex-column">
        <label>密码</label>
      </div>
      <div class="inputForm">
        <img src="~@/assets/login/pass.svg" alt="password" />
        <input
          :type="showPassword ? 'text' : 'password'"
          class="input"
          v-model="loginObj.password"
          placeholder="您的密码"
        />
        <img
          src="~@/assets/login/eye.svg"
          alt="toggle password visibility"
          class="eye-icon"
          @click="togglePasswordVisibility"
        />
      </div>

      <!-- 确认密码输入 -->
      <div v-if="regState" class="flex-column">
        <label>确认密码</label>
      </div>
      <div v-if="regState" class="inputForm">
        <img src="~@/assets/login/pass.svg" alt="password" />
        <input
          :type="showConfirmPassword ? 'text' : 'password'"
          class="input"
          v-model="loginObj.affirmPassword"
          placeholder="确认密码"
        />
        <img
          src="~@/assets/login/eye.svg"
          alt="toggle confirm password visibility"
          class="eye-icon"
          @click="toggleConfirmPasswordVisibility"
        />
      </div>

      <!-- 记住我选项 -->
      <div v-if="!regState" class="flex-row" style="margin-bottom: 15px;">
        <label class="remember-me-container">
          <input
            type="checkbox"
            v-model="loginObj.rememberMe"
            class="remember-me-checkbox"
          />
          <span class="checkmark"></span>
          记住我，自动登录
        </label>
      </div>

      <!-- 忘记密码--
      <div v-if="!regState" class="flex-row">
        <span class="span" @click="handleForgotPassword">忘记密码?</span>
      </div> -->

      <!-- 提交按钮 -->
      <button type="submit" class="button-submit">{{ regState ? '注 册' : '登 录' }}</button>

      <!-- 注册切换 -->
      <p class="p" v-if="!regState">
        没有账户?
        <span class="span" @click="toggleRegisterState">注 册</span>
      </p>
      <p class="p" v-else>
        点击返回
        <span class="span" @click="toggleRegisterState">登 录</span>
      </p>

      <!--<p class="p line">或者以下方式登录</p>-->

      <!-- 第三方登录 -->
      <!--<div class="flex-row">
        <button type="button" class="btn google" @click="showServiceUpgradeMessage('face')">
          <img src="~@/assets/login/face.svg" width="25" height="25" alt="google" />
          人脸登录
        </button>
        <button type="button" class="btn apple" @click="showServiceUpgradeMessage('sso')">
          <img src="~@/assets/login/sso.svg" width="25" height="25" alt="apple" />
          网页SSO登录
        </button>
      </div>-->
    </form>
  </div>
</template>

<script>
export default {
  data() {
    return {
      regState: false,
      showPassword: false,
      showConfirmPassword: false,
      changeRegLoading: false,
      submitLoading: false,
      loginObj: {
        username: '',
        password: '',
        affirmPassword: '',
        rememberMe: false
      }
    }
  },
  async created() {
    this.$emit('updateBar')
    // 按照原始流程，在登录页面检查自动登录
    await this.checkAutoLogin()
  },
  methods: {
    // // 处理忘记密码
    // handleForgotPassword() {
    //   // 这里可以添加忘记密码的逻辑，例如跳转到忘记密码页面或显示一个弹窗
    //   this.$message({
    //     message: '忘记密码功能尚未实现',
    //     type: 'info'
    //   })
    // },
    // 切换注册状态
    toggleRegisterState() {
      this.changeRegLoading = true
      //window.ipcRenderer.send('loginOrRegister',!this.regState)
      setTimeout(() => {
        this.regState = !this.regState
        if (!this.regState) {
          this.loginObj.username = ''
          this.loginObj.password = ''
          this.loginObj.affirmPassword = ''
        }
        this.changeRegLoading = false
      }, 1000)
    },
    // 显隐密码
    togglePasswordVisibility() {
      this.showPassword = !this.showPassword
    },
    toggleConfirmPasswordVisibility() {
      this.showConfirmPassword = !this.showConfirmPassword
    },
    // 提交表单
    async submit() {
      // 校验逻辑
      if (!this.loginObj.username || !this.loginObj.password) {
        this.$message({
          message: '请输入完整的账户信息！',
          type: 'info'
        })
        return
      }
      if (this.regState && this.loginObj.password !== this.loginObj.affirmPassword) {
        this.$message({
          message: '两次输入的密码不一致！',
          type: 'error'
        })
        return
      }

      this.submitLoading = true

      try {
        if (this.regState) {
          // 注册逻辑
          await this.handleRegister()
        } else {
          // 登录逻辑
          await this.handleLogin()
        }
      } catch (error) {
        console.error('提交失败:', error)
        this.$message.error(error.message || '操作失败，请重试')
      } finally {
        this.submitLoading = false
      }
    },

    // 处理登录
    async handleLogin() {
      try {
        console.log('开始登录请求...')

        // 调用主进程的登录接口
        const loginResult = await window.ipcRenderer.invoke('login', {
          userId: this.loginObj.username,
          password: this.loginObj.password,
          rememberMe: this.loginObj.rememberMe // 使用用户选择的记住我状态
        })

        console.log('登录结果:', loginResult)

        if (loginResult.success) {
          // 检查是否为离线调试模式
          if (this.loginObj.username === 'admin') {
            this.$message({
              message: '🟡 离线调试模式：admin账户无需SSE连接，使用本地数据进行测试',
              type: 'warning',
              duration: 5000,
              showClose: true
            });
            console.log('🟡 [前端调试] admin账户启用离线调试模式');
          } else if (loginResult.offlineDebugMode) {
            this.$message({
              message: '🟡 离线调试模式：SSE连接失败，切换到本地数据模式',
              type: 'warning',
              duration: 5000,
              showClose: true
            });
            console.log('🟡 [前端调试] 启用离线调试模式');
          } else {
            this.$message.success('登录成功');
          }

          // 发送窗口调整消息
          const screenWidth = window.screen.width
          const screenHeight = window.screen.height

          try {
            const screenData = {
              userId: this.loginObj.username, // 使用userId替代username
              token: loginResult.token || '',
              screenWidth: Number(screenWidth) || 1200,
              screenHeight: Number(screenHeight) || 800
            }
            window.ipcRenderer.send('toMain', screenData)
          } catch (error) {
            console.error('发送窗口调整消息失败:', error)
          }

          // 跳转到主页面
          this.$router.push('/main')
        } else {
          // 登录失败
          const errorMessage = loginResult.message || '登录失败，请检查用户名和密码'
          this.$message.error(errorMessage)
          console.error('登录失败:', errorMessage)
        }
      } catch (error) {
        console.error('登录请求失败:', error)
        this.$message.error('网络连接失败，请检查服务器连接')
      }
    },

    // 处理注册
    async handleRegister() {
      try {
        console.log('开始注册请求...')

        // 调用主进程的注册接口
        const registerResult = await window.ipcRenderer.invoke('register', {
          userId: this.loginObj.username,
          password: this.loginObj.password
        })

        console.log('注册结果:', registerResult)

        if (registerResult.success) {
          // 注册成功
          this.$message.success('注册成功，请登录')

          // 切换到登录模式
          this.regState = false
          this.loginObj.affirmPassword = ''
        } else {
          // 注册失败
          const errorMessage = registerResult.message || '注册失败，请重试'
          this.$message.error(errorMessage)
          console.error('注册失败:', errorMessage)
        }
      } catch (error) {
        console.error('注册请求失败:', error)
        this.$message.error('网络连接失败，请检查服务器连接')
      }
        },

    // 检查自动登录 - 按照原始流程文档
    async checkAutoLogin() {
      try {
        console.log('登录页面：检查自动登录...')

        const autoLoginResult = await window.ipcRenderer.invoke('check-auto-login')
        console.log('自动登录检查结果:', autoLoginResult)

        if (autoLoginResult.success && autoLoginResult.autoLogin) {
          // 检查是否为离线调试模式
          const isAdminUser = autoLoginResult.user?.userId === 'admin';
          if (isAdminUser) {
            this.$message({
              message: '🟡 离线调试模式：admin账户无需SSE连接，使用本地数据进行测试',
              type: 'warning',
              duration: 5000,
              showClose: true
            });
            console.log('🟡 [前端调试] admin账户自动登录启用离线调试模式');
          } else if (autoLoginResult.offlineDebugMode) {
            this.$message({
              message: '🟡 离线调试模式：SSE连接失败，切换到本地数据模式',
              type: 'warning',
              duration: 5000,
              showClose: true
            });
            console.log('🟡 [前端调试] 自动登录启用离线调试模式');
          } else {
            this.$message.success('自动登录成功');
          }

          // 发送窗口调整消息
          const screenWidth = window.screen.width
          const screenHeight = window.screen.height

                     try {
             const screenData = {
               userId: autoLoginResult.user?.userId || '',
               token: autoLoginResult.token || '',
               screenWidth: Number(screenWidth) || 1200,
               screenHeight: Number(screenHeight) || 800
             }
            window.ipcRenderer.send('toMain', screenData)
          } catch (error) {
            console.error('发送窗口调整消息失败:', error)
          }

          // 跳转到主页面
          this.$router.push('/main')
        } else {
          console.log('没有自动登录，用户需要手动登录')
        }
      } catch (error) {
        console.error('自动登录检查失败:', error)
        // 自动登录失败不影响正常登录流程
      }
    },

    // 显示升级提示
    showServiceUpgradeMessage(type) {
      if ('face' === type) {
        this.$router.push('/face')
      } else {
        window.open('https://www.baidu.com/', '_blank')
      }
    }
  }
}
</script>

<style>
@import './index.css';
.el-loading-spinner .path {
  stroke: #151717 !important;
}
.el-loading-mask {
  border-radius: 20px !important;
  width: 510px !important;
}

/* 记住我选项样式 */
.remember-me-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  user-select: none;
}

.remember-me-checkbox {
  margin-right: 8px;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.remember-me-container:hover {
  color: #409eff;
}

.flex-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
</style>

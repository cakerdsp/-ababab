<template>
  <!-- <div class="desktop-main">
    <div class="desktop-main-title">
      <h2>智能高效，掌控家居。</h2>
    </div>

    <div class="desktop-main-mid">
      <div class="desktop-card" style="margin-right: 30px">
        <img src="~@/assets/main/desk.webp" width="315" height="200" />
        <div class="desktop-card__content">
          <p class="desktop-card__title">任务全自动化</p>
          <p class="desktop-card__description">
            智能脚本让重复任务一键完成，无需手动干预，高效可靠，提升生产力。
          </p>
        </div>
      </div>

      <div class="desktop-card">
        <img src="~@/assets/main/desk2.webp" width="315" height="200" />
        <div class="desktop-card__content">
          <p class="desktop-card__title">实时数据处理</p>
          <p class="desktop-card__description">
            实时监控与流量分配，确保系统稳定运行，轻松应对复杂场景需求。
          </p>
        </div>
      </div>
    </div>

    <div class="desktop-main-title">
      <h2>推荐更多功能点</h2>
    </div>

    <div class="desktop-main-bottom">
      <div class="desktop-main-bottom-item">
        <img src="~@/assets/desktop/jiqr.svg" />
        <p>机器人队列</p>
      </div>

      <div class="desktop-main-bottom-item">
        <img src="~@/assets/desktop/fwl.svg" />
        <p>访问量</p>
      </div>

      <div class="desktop-main-bottom-item">
        <img src="~@/assets/desktop/dianzan.svg" />
        <p>点赞系列</p>
      </div>
    </div>
  </div> -->
</template>



<script>
import { ElMessageBox } from 'element-plus'
export default {
  name: 'DesktopPage',
  data() {
    return {
      avatarUrl: '',
      username: 'typs****@163.com',
      hoverIndex: null, // 当前悬停的索引
      selectedIndex: 0, // 当前选中的索引，默认选中第一个
      functionList: [
        {
          name: '账号中心',
          selectedImg: new URL('@/assets/sidebar/home-selected.png', import.meta.url).href,
          defaultImg: new URL('@/assets/sidebar/home-default.png', import.meta.url).href,
          path: '/user-binding'
        },
        {
          name: '分组管理',
          selectedImg: new URL('@/assets/sidebar/czhi-selected.svg', import.meta.url).href,
          defaultImg: new URL('@/assets/sidebar/czhi-default.svg', import.meta.url).href,
          path: '/group'
        },
        {
          name: '设备发现',
          selectedImg: new URL('@/assets/sidebar/set-selected.svg', import.meta.url).href,
          defaultImg: new URL('@/assets/sidebar/set-default.svg', import.meta.url).href,
          path: '/setting'
        },
        {
          name: '环境检测',
          selectedImg: new URL('@/assets/sidebar/pingtai-selected.svg', import.meta.url).href,
          defaultImg: new URL('@/assets/sidebar/pingtai-default.svg', import.meta.url).href,
          path: '/platform'
        },

        {
          name: '退出登录',
          selectedImg: new URL('@/assets/sidebar/tuic-selected.svg', import.meta.url).href,
          defaultImg: new URL('@/assets/sidebar/tuic-default.svg', import.meta.url).href,
          path: '/login'
        }
      ]
    }
  },
  methods: {
    funcItem(path, index) {
      this.selectedIndex = index
      if (path === '/login') {
        // 其他清除token的操作
        ElMessageBox.confirm('确认需要退出吗?', '退出提示', {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning'
        })
          .then(() => {
            // 确认退出
            this.$router.push(path)
          })
          .catch(() => {
            // 取消
          })
      } else {
        this.$router.push(path)
      }
    },
    getItemImage(index) {
      if (this.hoverIndex === index || this.selectedIndex === index) {
        // 悬停或选中时使用 selectedImg
        return this.functionList[index].selectedImg
      }
      // 默认使用 defaultImg
      return this.functionList[index].defaultImg
    },
    getRandomValue(options) {
      return options[Math.floor(Math.random() * options.length)]
    },
    generateAvatar() {
      const baseUrl = 'https://avataaars.io/'
      const params = new URLSearchParams({
        topType: this.getRandomValue([
          'NoHair',
          'ShortHairDreads01',
          'ShortHairFrizzle',
          'LongHairStraight',
          'Hat',
          'Hijab'
        ]),
        accessoriesType: this.getRandomValue([
          'Blank',
          'Kurt',
          'Prescription01',
          'Sunglasses',
          'Round'
        ]),
        hairColor: this.getRandomValue(['Black', 'Blonde', 'BrownDark', 'Red', 'SilverGray']),
        facialHairType: this.getRandomValue([
          'Blank',
          'BeardMedium',
          'BeardLight',
          'MoustacheFancy'
        ]),
        clotheType: this.getRandomValue([
          'Hoodie',
          'BlazerShirt',
          'BlazerSweater',
          'GraphicShirt',
          'ShirtCrewNeck'
        ]),
        clotheColor: this.getRandomValue(['PastelRed', 'Blue03', 'Heather', 'Pink', 'Gray01']),
        eyeType: this.getRandomValue(['Happy', 'Squint', 'Surprised', 'Cry', 'Wink']),
        eyebrowType: this.getRandomValue([
          'Default',
          'RaisedExcited',
          'AngryNatural',
          'SadConcerned'
        ]),
        mouthType: this.getRandomValue(['Smile', 'Default', 'Twinkle', 'Tongue']),
        skinColor: this.getRandomValue(['Light', 'Tanned', 'Brown', 'DarkBrown', 'Black'])
      })

      if (this.$route.query && this.$route.query.base64) {
        this.avatarUrl = this.$route.query.base64
      } else {
        this.avatarUrl = `${baseUrl}?${params.toString()}`
      }
    }
  },
  created() {
    console.log('🔍 [调试] DesktopPage created - 桌面页面创建', {
      timestamp: new Date().toLocaleTimeString(),
      selectedIndex: this.selectedIndex,
      functionListLength: this.functionList.length
    });
  },
  mounted() {
    console.log('🔍 [调试] DesktopPage mounted - 桌面页面挂载完成', {
      timestamp: new Date().toLocaleTimeString(),
      avatarUrl: this.avatarUrl,
      username: this.username
    });
    this.generateAvatar()
  },
  activated() {
    console.log('🔍 [调试] DesktopPage activated - 桌面页面被激活 (keep-alive)', {
      timestamp: new Date().toLocaleTimeString(),
      message: '如果看到这个日志，说明keep-alive正在工作',
      selectedIndex: this.selectedIndex
    });
  },
  deactivated() {
    console.log('🔍 [调试] DesktopPage deactivated - 桌面页面被缓存 (keep-alive)', {
      timestamp: new Date().toLocaleTimeString(),
      message: '页面被缓存，状态应该保持',
      selectedIndex: this.selectedIndex
    });
  },
  beforeUnmount() {
    console.log('🔍 [调试] DesktopPage beforeUnmount - 桌面页面即将销毁', {
      timestamp: new Date().toLocaleTimeString(),
      message: '⚠️ 如果看到这个日志，说明组件被销毁了，状态会丢失！'
    });
  },
  watch: {
    selectedIndex(newVal, oldVal) {
      console.log('🔍 [调试] DesktopPage selectedIndex 变化:', {
        from: oldVal,
        to: newVal,
        timestamp: new Date().toLocaleTimeString()
      });
    }
  }
}
</script>



<!--<script>
export default {
  name: 'index'
}.
</script> -->

<style scoped>
.desktop-main {
  width: 100%;
  height: 100%;
  user-select: none;
  -webkit-app-region: no-drag;
}
.desktop-main-title {
  width: auto;
  height: 100px;
  line-height: 100px;
  margin-left: 30px;
}
.desktop-main-mid {
  width: auto;
  height: 200px;
  margin-left: 30px;
}

.desktop-main-bottom {
  width: auto;
  height: 100px;
  margin-left: 30px;
}

.desktop-main-bottom-item {
  width: 180px;
  height: 70px;
  border: 1px solid #eeeeee;
  border-radius: 10px;
  margin-right: 38px;
  color: #666666;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 18px;
  cursor: pointer;
  float: left;
}

.desktop-main-bottom-item img {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}

.desktop-card {
  position: relative;
  width: 315px;
  height: 200px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  float: left;
}

.desktop-card svg {
  width: 48px;
  fill: #333;
  transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
}

.desktop-card:hover {
  transform: rotate(-5deg) scale(1.1);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.desktop-card__content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  width: 100%;
  height: 100%;
  padding: 20px;
  box-sizing: border-box;
  background-color: #fff;
  opacity: 0;
  transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
}

.desktop-card:hover .desktop-card__content {
  transform: translate(-50%, -50%) rotate(0deg);
  opacity: 1;
}

.desktop-card__title {
  margin: 0;
  font-size: 24px;
  color: #333;
  font-weight: 700;
}

.desktop-card__description {
  margin: 10px 0 0;
  font-size: 14px;
  color: #777;
  line-height: 1.4;
}

.desktop-card:hover svg {
  scale: 0;
  transform: rotate(-45deg);
}
</style>



